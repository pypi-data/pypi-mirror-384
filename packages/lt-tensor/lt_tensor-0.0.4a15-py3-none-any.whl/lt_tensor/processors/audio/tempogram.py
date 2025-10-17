__all__ = ["Tempogram"]
import scipy
from lt_utils.common import *
from lt_tensor.common import *
import torch.nn.functional as F


class Tempogram(Model):
    # Still incomplete but starting to take shape, needs more work

    def __init__(
        self,
        win_length: int = 1024,
        hop_length: int = 256,
        window_fn=lambda x: torch.hann_window(x, periodic=True),
    ):
        super().__init__()
        self.win_length = win_length
        self.hop_length = hop_length

        self.register_buffer("window", window_fn(win_length))

    def onset_env(self, x: Tensor) -> Tensor:
        # x: [T] or [B, T]
        if x.ndim == 1:
            x = x.unsqueeze(0)
        # simple spectral flux (mimics onset_strength)
        stft = torch.stft(
            x,
            n_fft=self.win_length,
            hop_length=self.hop_length,
            win_length=self.win_length,
            window=self.window,
            return_complex=True,
        )
        mag = stft.abs()
        diff = F.relu(mag[..., 1:] - mag[..., :-1])
        onset_env = diff.mean(dim=1)  # average over frequency bins
        # pad to match original frames
        pad_left = self.win_length // 2
        onset_env = F.pad(onset_env, (pad_left, pad_left))
        return onset_env

    def frame(self, x: Tensor) -> Tensor:
        # x: [B, T], unfold into overlapping frames with stride=1
        B, T = x.shape
        L = self.win_length
        frames = x.unfold(dimension=1, size=L, step=1)  # [B, T-L+1, L]
        return frames

    def autocorr(self, frames: Tensor, n_pad) -> Tensor:
        # frames: [B, n_frames, L]
        L = frames.shape[-1]
        # multiply window
        frames = frames * self.window
        # FFT padding

        f = torch.fft.rfft(frames, n=n_pad)
        auto = torch.fft.irfft(f.abs() ** 2, n=n_pad)
        auto = auto[..., :L]

        return auto

    def forward(self, x: Tensor) -> Tensor:
        T = x.shape[-1]
        with torch.no_grad():
            n_pad = scipy.fft.next_fast_len(2 * x.shape[-1] - 1, real=True)
        onset = self.onset_env(x)  # [B, T]
        frames = self.frame(onset)  # [B, n_frames, L]
        tempogram = self.autocorr(frames, n_pad)  # [B, n_frames, L]

        tempogram = tempogram.transpose(1, 2)
        return tempogram
