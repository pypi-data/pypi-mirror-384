__all__ = ["mel_filterbank", "mel_to_hz", "hz_to_mel", "mel_frequencies"]
import warnings
import librosa
import numpy as np
import scipy
from lt_utils.common import *
from lt_tensor.common import *
from lt_utils.misc_utils import default
import torchaudio
import torch.nn.functional as F
from lt_utils.file_ops import FileScan, is_file

from lt_tensor.tensor_ops import to_device, to_other_device
from lt_tensor.misc_utils import (
    get_window,
    to_numpy_array,
    to_torch_tensor,
    _VALID_WINDOWS_TP,
    _VALID_WINDOWS,
)
from lt_utils.misc_utils import filter_kwargs
from lt_tensor.tensor_ops import VQT, CQT, sub_outer


def mel_to_hz(
    mels: Tensor,
    *,
    htk: bool = False,
    dtype: Optional[Union[torch.device, str]] = torch.float64,
) -> Tensor:
    """Adapted from librosa"""
    if htk:
        return 700.0 * (10.0 ** (mels / 2595.0) - 1.0)

    # Fill in the linear scale
    f_min = 0.0
    f_sp = 200.0 / 3
    freqs = f_min + f_sp * mels

    # And now the nonlinear scale
    min_log_hz = 1000.0  # beginning of log region (Hz)
    min_log_mel = (min_log_hz - f_min) / f_sp  # same (Mels)
    logstep = (
        torch.log(torch.as_tensor(6.4, dtype=dtype)) / 27.0
    )  # step size for log region

    if mels.ndim:
        # If we have vector data, vectorize
        log_t = mels >= min_log_mel
        freqs[log_t] = min_log_hz * torch.exp(logstep * (mels[log_t] - min_log_mel))
    elif mels >= min_log_mel:
        # If we have scalar data, check directly
        freqs = min_log_hz * torch.exp(logstep * (mels - min_log_mel))

    return freqs


def hz_to_mel(
    frequencies: float,
    *,
    htk: bool = False,
    dtype: Optional[Union[torch.device, str]] = torch.float64,
) -> torch.Tensor:
    """Adapted from librosa"""
    frequencies = torch.as_tensor(frequencies)

    if htk:
        mels = 2595.0 * torch.log10(1.0 + frequencies / 700.0)
        return mels

    # Fill in the linear part
    f_min = 0.0
    f_sp = 200.0 / 3

    mels = (frequencies - f_min) / f_sp

    # Fill in the log-scale part

    min_log_hz = 1000.0  # beginning of log region (Hz)
    min_log_mel = (min_log_hz - f_min) / f_sp  # same (Mels)
    logstep = (
        torch.log(torch.as_tensor(6.4, dtype=dtype)) / 27.0
    )  # step size for log region

    if frequencies.ndim:
        # If we have array data, vectorize
        log_t = frequencies >= min_log_hz
        mels[log_t] = min_log_mel + torch.log(frequencies[log_t] / min_log_hz) / logstep
    elif frequencies >= min_log_hz:
        # If we have scalar data, heck directly
        mels = min_log_mel + torch.log(frequencies / min_log_hz) / logstep

    return mels


def mel_frequencies(
    n_mels: int = 128,
    *,
    f_min: float = 0.0,
    f_max: float = 11025.0,
    htk: bool = False,
    dtype: Optional[Union[torch.device, str]] = torch.float64,
):
    """Adapted from librosa"""
    min_mel = hz_to_mel(f_min, htk=htk, dtype=dtype)
    max_mel = hz_to_mel(f_max, htk=htk, dtype=dtype)

    mels = torch.linspace(min_mel, max_mel, n_mels, dtype=dtype)

    hz = mel_to_hz(mels, htk=htk, dtype=dtype)

    return hz


def mel_filterbank(
    sr: float = 24000,
    n_fft: int = 1024,
    n_mels: int = 80,
    f_min: float = 0.0,
    f_max: Optional[float] = None,
    htk: bool = False,
    dtype: Optional[Union[torch.device, str]] = torch.float32,
    device: Optional[torch.device] = None,
):
    """Adapted from librosa"""
    if f_max is None:
        f_max = float(sr) / 2

    # Initialize the weights
    n_mels = int(n_mels)
    weights = torch.zeros((n_mels, int(1 + n_fft // 2)), dtype=dtype)
    fftfreqs = torch.fft.rfftfreq(n=n_fft, d=1.0 / sr, dtype=dtype)
    # mel_f = mel_frequencies(n_mels + 2, fmin=fmin, fmax=fmax, htk=htk)
    mel_f = mel_frequencies(n_mels + 2, f_min=f_min, f_max=f_max, htk=htk, dtype=dtype)

    # compare_ramps(mel_f, fftfreqs)
    fdiff = mel_f.diff()
    ramps = sub_outer(mel_f, fftfreqs)
    zero_tensor = torch.zeros(1)
    for i in range(n_mels):
        # lower and upper slopes for all bins
        lower = -ramps[i] / fdiff[i]
        upper = ramps[i + 2] / fdiff[i + 1]
        weights_bd = torch.min(lower, upper)
        # .. then intersect them with each other and zero
        weights[i] = weights_bd.clamp_min(zero_tensor)

    # Slaney-style mel is scaled to be approx constant energy per channel
    enorm = 2.0 / (mel_f[2 : n_mels + 2] - mel_f[:n_mels])
    weights *= enorm[:, torch.newaxis]

    if (
        not torch.all(mel_f[:-2] == 0).item()
        or torch.all(weights.max(dim=1) > zero_tensor).item()
    ):
        print(
            "Empty filters detected in mel frequency basis. "
            "Some channels will produce empty responses. "
            "Try increasing your sampling rate (and fmax) or "
            "reducing n_mels.",
        )
    return weights.to(device=device, dtype=dtype)
