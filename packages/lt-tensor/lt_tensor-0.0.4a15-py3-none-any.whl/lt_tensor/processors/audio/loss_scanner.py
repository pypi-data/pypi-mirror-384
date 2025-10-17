__all__ = ["AdaptiveSpectralExplorer"]

import torch
import optuna
import warnings
from lt_utils.common import *
from lt_tensor.common import *
from lt_tensor.processors.audio.losses import SingleResolutionMelLoss


class AdaptiveSpectralExplorer:
    def __init__(
        self,
        sample_rate: int = 24000,
        trials: int = 128,
        device: str = "cpu",
    ):

        self.loss_class = SingleResolutionMelLoss
        self.sample_rate = sample_rate
        self.trials = trials
        self.device = device
        optuna.logging.disable_default_handler()
        optuna.logging.set_verbosity(optuna.logging.ERROR)
        warnings.filterwarnings(
            action="ignore",
            category=UserWarning,
        )
        self.study = optuna.create_study(direction="maximize")

    @torch.no_grad()
    def objective(self, trial, real_audio: torch.Tensor, fake_audio: torch.Tensor):
        n_mels = trial.suggest_int("n_mels", 8, 512, step=8)
        hop_length = trial.suggest_int("hop_length", 16, 1024, step=8)
        n_fft = trial.suggest_int(
            "n_fft", int(max(hop_length * 1.25, 128)), 2048, step=8
        )

        try:
            loss_fn = self.loss_class(
                sample_rate=self.sample_rate,
                n_mels=n_mels,
                n_fft=n_fft,
                hop_length=hop_length,
            ).to(self.device)

            fb = getattr(loss_fn.mel_fn.mel_scale, "fb", None)
            if fb is not None and (fb.max(dim=0).values == 0.0).any():
                return -float("inf")

            # evaluate without gradient
            loss_val = loss_fn(fake_audio, real_audio).item()
            return loss_val

        except Exception:
            return -float("inf")

    def restart_study(self):
        self.study = optuna.create_study(direction="maximize")

    def _run_search(
        self,
        fake_audio: torch.Tensor,
        real_audio: torch.Tensor,
    ):
        """Runs Optuna to find configurations exposing model weaknesses."""
        self.study.optimize(
            lambda trial: self.objective(trial, real_audio, fake_audio),
            n_trials=self.trials,
            show_progress_bar=True,
        )
        return self.study.best_params, self.study.best_value

    def __call___(
        self,
        fake_audio: torch.Tensor,
        real_audio: torch.Tensor,
        top_k: int = 3,
    ):
        """Returns top-k configurations to add to the training ensemble."""

        self._run_search(real_audio, fake_audio)
        trials = sorted(self.study.trials, key=lambda t: t.value, reverse=True)
        return [t.params for t in trials[:top_k]]
