__all__ = [
    "SingleResolutionMelLoss",
    "MultiResolutionMelLoss",
    "MultiResolutionSTFTLoss",
    "BandFilter",
    "CQTLoss",
]


from lt_utils.common import *
from lt_tensor.common import *
import torch.nn.functional as F
from lt_tensor.misc_utils import (
    get_window,
    _VALID_WINDOWS_TP,
)
from .misc import BandFilter
from lt_tensor.tensor_ops import CQT


class CQTLoss(Model):
    def __init__(
        self,
        sample_rate: int = 24000,
        n_bins: int = 112,
        bins_per_octave: int = 16,
        hop_length: int = 256,
        f_min: float = 32.703,
        dtype: torch.dtype = torch.float32,
        loss_fn: Callable[[Tensor, Tensor], Tensor] = F.l1_loss,
        window: _VALID_WINDOWS_TP = "hann",
        periodic: bool = False,
        alpha: float = 1,
        beta: float = 1,
        forward_method: Literal["0", "1"] = "0",
    ):
        super().__init__()
        self.cqt = CQT(
            sample_rate=sample_rate,
            n_bins=n_bins,
            bins_per_octave=bins_per_octave,
            hop_length=hop_length,
            f_min=f_min,
            window_fn=lambda x: get_window(
                x,
                window_type=window,
                periodic=periodic,
                alpha=alpha,
                beta=beta,
            ),
            dtype=dtype,
        )
        self.loss_fn = loss_fn
        self.forward_method = forward_method

    def forward(self, inputs: Tensor, target: Tensor):
        cqt_i = self.cqt(inputs)
        cqt_t = self.cqt(target)
        if self.forward_method == "0":

            mag_i = torch.abs(cqt_i)
            mag_t = torch.abs(cqt_t)

            # Perceptual log compression
            mag_i = torch.log1p(mag_i)
            mag_t = torch.log1p(mag_t)

            # Spectral convergence
            num = torch.norm(mag_t - mag_i, p="fro")
            den = torch.norm(mag_t, p="fro") + 1e-8
            den = den**0.96
            loss_sc = num / den

            loss_mag = self.loss_fn(mag_i, mag_t)
            return loss_mag + loss_sc
        return self.loss_fn(cqt_i, cqt_t)


class SingleResolutionMelLoss(Model):
    def __init__(
        self,
        sample_rate: int = 24000,
        n_mels: int = 80,
        window_length: int = 1024,
        n_fft: int = 1024,
        hop_length: int = 256,
        f_min: float = 0,
        f_max: Optional[float] = None,
        loss_fn: Callable[[Tensor, Tensor], Tensor] = nn.L1Loss(),
        center: bool = False,
        power: float = 1.0,
        normalized: bool = False,
        pad_mode: str = "reflect",
        onesided: Optional[bool] = None,
        weight: float = 1.0,
        window: _VALID_WINDOWS_TP = "hann",
        periodic: bool = False,
        alpha: float = 1,
        beta: float = 1,
    ):
        super().__init__()
        import torchaudio

        self.mel_fn = torchaudio.transforms.MelSpectrogram(
            sample_rate=sample_rate,
            center=center,
            onesided=onesided,
            normalized=normalized,
            power=power,
            pad_mode=pad_mode,
            n_fft=n_fft,
            hop_length=hop_length,
            win_length=window_length,
            n_mels=n_mels,
            f_min=f_min,
            f_max=f_max,
            window_fn=lambda x: get_window(x, window, periodic, alpha=alpha, beta=beta),
        )
        self.loss_fn = loss_fn
        self.weight = weight

    def forward(self, wave: Tensor, target: Tensor):
        x_mels = self.mel_fn.forward(wave)
        y_mels = self.mel_fn.forward(target)
        return self.loss_fn(x_mels, y_mels) * self.weight


class MultiResolutionMelLoss(Model):
    def __init__(
        self,
        sample_rate: int = 24000,
        n_mels: List[int] = [5, 10, 20, 40, 80, 160, 320],
        window_lengths: List[int] = [32, 64, 128, 256, 512, 1024, 2048],
        n_ffts: List[int] = [32, 64, 128, 256, 512, 1024, 2048],
        hops: List[int] = [8, 16, 32, 64, 128, 256, 512],
        f_min: List[float] = [0, 0, 0, 0, 0, 0, 0],
        f_max: List[Optional[float]] = [None, None, None, None, None, None, None],
        loss_fn: Callable[[Tensor, Tensor], Tensor] = nn.L1Loss(),
        center: bool = False,
        power: float = 1.0,
        normalized: bool = False,
        pad_mode: str = "reflect",
        onesided: Optional[bool] = None,
        weight: float = 1.0,
        window: List[_VALID_WINDOWS_TP] = [
            "hann",
            "hann",
            "hann",
            "hann",
            "hann",
            "hann",
            "hann",
        ],
        periodic: List[bool] = [False, False, False, False, False, False, False],
        alpha: List[float] = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        beta: List[float] = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        reduce_to_size: bool = False,
    ):
        super().__init__()
        assert (
            len(n_mels)
            == len(window_lengths)
            == len(n_ffts)
            == len(hops)
            == len(f_min)
            == len(f_max)
        )
        self._setup_mels(
            sample_rate,
            n_mels,
            window_lengths,
            n_ffts,
            hops,
            f_min,
            f_max,
            center,
            power,
            normalized,
            pad_mode,
            onesided,
            loss_fn,
            weight,
            window,
            periodic,
            alpha,
            beta,
        )
        self.reduce_to_size = reduce_to_size
        self.total = len(self.mel_losses)
        self.reducer = 1.0 / self.total

    def _setup_mels(
        self,
        sample_rate: int,
        n_mels: List[int],
        window_lengths: List[int],
        n_ffts: List[int],
        hops: List[int],
        f_min: List[float],
        f_max: List[Optional[float]],
        center: bool,
        power: float,
        normalized: bool,
        pad_mode: str,
        onesided: Optional[bool],
        loss_fn: Callable,
        weight: float,
        window: List[_VALID_WINDOWS_TP],
        periodic: List[bool],
        alpha: List[float],
        beta: List[float],
    ):
        if not (
            len(n_mels)
            == len(window_lengths)
            == len(n_ffts)
            == len(hops)
            == len(f_min)
            == len(f_max)
            == len(periodic)
            == len(alpha)
            == len(beta)
            == len(window)
        ):
            # Normalize lengths
            all_lists = [
                n_mels,
                window_lengths,
                n_ffts,
                hops,
                f_min,
                f_max,
                periodic,
                alpha,
                beta,
                window,
            ]
            max_len = max(len(lst) for lst in all_lists)

            def pad(lst):
                if not lst:
                    raise ValueError("Empty list found, cannot pad.")
                if len(lst) < max_len:
                    lst.extend([lst[-1]] * (max_len - len(lst)))
                return lst

            (
                n_mels,
                window_lengths,
                n_ffts,
                hops,
                f_min,
                f_max,
                periodic,
                alpha,
                beta,
                window,
            ) = [pad(lst) for lst in all_lists]

        _mel_kwargs = dict(
            sample_rate=sample_rate,
            center=center,
            onesided=onesided,
            normalized=normalized,
            power=power,
            pad_mode=pad_mode,
            loss_fn=loss_fn,
            weight=weight,
        )

        self.mel_losses: List[SingleResolutionMelLoss] = nn.ModuleList(
            [
                SingleResolutionMelLoss(
                    **_mel_kwargs,
                    n_fft=n_fft,
                    hop_length=hop,
                    window_length=win,
                    n_mels=mel,
                    f_min=fmin,
                    f_max=fmax,
                    alpha=ap,
                    beta=bt,
                    periodic=pr,
                    window=wn,
                )
                for mel, win, n_fft, hop, fmin, fmax, pr, ap, bt, wn in zip(
                    n_mels,
                    window_lengths,
                    n_ffts,
                    hops,
                    f_min,
                    f_max,
                    periodic,
                    alpha,
                    beta,
                    window,
                )
            ]
        )

    def forward(self, input_wave: Tensor, target_wave: Tensor) -> Tensor:
        loss = 0.0
        rd = 1.0 if not self.reduce_to_size else self.reducer
        for loss_fn in self.mel_losses:
            loss += loss_fn(input_wave, target_wave) * rd
        return loss


class SingleResolutionSTFTLoss(Model):
    def __init__(
        self,
        n_fft: int = 1024,
        hop_length: int = 256,
        loss_fn: Callable[[Tensor, Tensor], Tensor] = nn.L1Loss(),
        window: _VALID_WINDOWS_TP = "hann",
        periodic: bool = False,
        alpha: float = 1,
        beta: float = 1,
    ):
        super().__init__()
        self.register_buffer(
            "window",
            get_window(
                n_fft, window_type=window, periodic=periodic, alpha=alpha, beta=beta
            ),
        )
        self.loss_fn = loss_fn
        self.hop_length = hop_length
        self.n_fft = n_fft

    def _stft_mag(self, x: Tensor):
        if x.ndim == 3:
            x = x.squeeze(1)
        return torch.stft(
            x,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            win_length=self.n_fft,
            window=self.window,
            return_complex=True,
        ).abs()

    def forward(self, input: Tensor, target: Tensor):
        mag_g = self._stft_mag(input)
        mag_r = self._stft_mag(target)

        loss_mag = self.loss_fn(mag_g, mag_r)
        num = torch.norm(mag_r - mag_g, p="fro")
        den = torch.norm(mag_r, p="fro") + 1e-8
        loss_sc = num / den

        return loss_mag + loss_sc


class MultiResolutionSTFTLoss(Model):
    def __init__(
        self,
        n_ffts: List[int] = [
            32,
            128,
            256,
            512,
            1024,
            2048,
        ],
        hop_lengths: List[int] = [
            8,
            32,
            64,
            128,
            256,
            512,
        ],
        window: List[_VALID_WINDOWS_TP] = [
            "hann",
            "hann",
            "hann",
            "hann",
            "hann",
            "hann",
        ],
        periodic: List[bool] = [
            False,
            False,
            False,
            False,
            False,
            False,
        ],
        alphas: List[float] = [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
        betas: List[float] = [
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
        loss_fn: nn.Module = nn.L1Loss(),
        reduce_to_size: bool = False,
    ):
        super().__init__()
        if not (
            len(n_ffts)
            == len(hop_lengths)
            == len(periodic)
            == len(alphas)
            == len(betas)
            == len(window)
        ):
            # Normalize lengths
            all_lists = [
                n_ffts,
                hop_lengths,
                periodic,
                alphas,
                betas,
                window,
            ]
            max_len = max(len(lst) for lst in all_lists)

            def pad(lst):
                if not lst:
                    raise ValueError("Empty list found, cannot pad.")
                if len(lst) < max_len:
                    lst.extend([lst[-1]] * (max_len - len(lst)))
                return lst

            (
                n_ffts,
                hop_lengths,
                periodic,
                alphas,
                betas,
                window,
            ) = [pad(lst) for lst in all_lists]
        self.hops = hop_lengths
        self.ffts = n_ffts
        self.seq = nn.ModuleList(
            [
                SingleResolutionSTFTLoss(
                    fft, hop, loss_fn, window=win, periodic=per, alpha=ap, beta=bt
                )
                for fft, hop, win, per, ap, bt in zip(
                    n_ffts,
                    hop_lengths,
                    window,
                    periodic,
                    alphas,
                    betas,
                )
            ]
        )
        self.reduce_to_size = reduce_to_size
        self.total = len(self.seq)
        self.reducer = 1.0 / self.total

    def forward(self, input: Tensor, target: Tensor):
        loss = 0.0
        rd = 1.0 if not self.reduce_to_size else self.reducer
        for L in self.seq:
            current = L(input, target)
            loss += current * rd
        return loss


"""
        n_mels: List[int] = [5, 10, 20, 40, 80, 160, 320],
        window_lengths: List[int] = [32, 64, 128, 256, 512, 1024, 2048],
        n_ffts: List[int] = [32, 64, 128, 256, 512, 1024, 2048],
        hops: List[int] = [8, 16, 32, 64, 128, 256, 512],
        f_min: List[float] = [0, 0, 0, 0, 0, 0, 0],
        f_max: List[Optional[float]] = [None, None, None, None, None, None, None],
"""
