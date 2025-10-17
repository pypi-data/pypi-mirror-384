__all__ = ["AudioProcessorConfig"]
from lt_utils.common import *
from lt_tensor.common import *
from lt_utils.misc_utils import default
from lt_tensor.misc_utils import (
    _VALID_WINDOWS_TP,
    _VALID_WINDOWS,
)


class AudioProcessorConfig(ModelConfig):
    sample_rate: int = 24000
    n_mels: int = 80
    n_fft: int = 1024
    win_length: int = 1024
    hop_length: int = 256
    f_min: float = 0
    f_max: Optional[float] = None
    center: bool = True
    std: int = 4
    mean: int = -4
    n_iter: int = 32
    normalized: bool = False
    onesided: Optional[bool] = None
    n_stft: int = None
    normalize_mel: bool = False
    window_type: _VALID_WINDOWS_TP = "hann"
    periodic_window: bool = False
    window_alpha: float = 1
    window_beta: float = 1
    mel_normalizer: Literal["log_norm", "range_norm"] = "log_norm"

    def __init__(
        self,
        sample_rate: int = 24000,
        n_mels: int = 80,
        n_fft: int = 1024,
        win_length: Optional[int] = None,
        hop_length: Optional[int] = None,
        f_min: float = 0,
        f_max: Optional[float] = None,
        center: bool = True,
        std: int = 4,
        mean: int = -4,
        normalized: bool = False,
        onesided: Optional[bool] = None,
        normalize_mel: bool = False,
        mel_normalizer: Literal["log_norm", "range_norm"] = "log_norm",
        window_type: _VALID_WINDOWS_TP = "hann",
        periodic_window: bool = False,
        window_alpha: float = 1,
        window_beta: float = 1,
        *args,
        **kwargs,
    ):
        assert window_type in _VALID_WINDOWS, (
            f'Invalid window type {window_type}. It must be one of: "'
            + '", '.join(_VALID_WINDOWS)
            + '".'
        )
        settings = {
            "sample_rate": sample_rate,
            "n_mels": n_mels,
            "n_fft": n_fft,
            "win_length": win_length,
            "hop_length": hop_length,
            "f_min": f_min,
            "f_max": f_max,
            "center": center,
            "std": std,
            "mean": mean,
            "normalized": normalized,
            "mel_normalizer": mel_normalizer,
            "onesided": onesided,
            "normalize_mel": normalize_mel,
            "window_type": window_type,
            "periodic_window": periodic_window,
            "window_alpha": window_alpha,
            "window_beta": window_beta,
        }
        super().__init__(**settings)
        self.post_process()

    def post_process(self):
        self.n_stft = self.n_fft // 2 + 1
        # some functions needs this to be a non-zero or not None value.
        self.default_f_min = max(self.f_min, (self.sample_rate / (self.n_fft - 1)) * 2)
        self.default_f_max = min(
            default(self.f_max, self.sample_rate // 2), self.sample_rate // 2
        )
        self.hop_length = default(self.hop_length, self.n_fft // 4)
        self.win_length = default(self.win_length, self.n_fft)
