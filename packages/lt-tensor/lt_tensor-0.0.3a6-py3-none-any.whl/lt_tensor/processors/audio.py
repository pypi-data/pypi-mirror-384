__all__ = [
    "AudioProcessor",
    "AudioProcessorConfig",
    "convert_to_16_bits",
    "SingleResolutionMelLoss",
    "MultiResolutionMelLoss",
    "MultiResolutionSTFTLoss",
    "BandFilter",
]

import warnings
import librosa
import numpy as np
from lt_utils.common import *
from lt_tensor.common import *
from lt_utils.misc_utils import default
import torchaudio
import torch.nn.functional as F
from lt_utils.file_ops import FileScan, is_file
from librosa.filters import mel as _mel_filter_bank
from lt_tensor.tensor_ops import to_device, to_other_device
from lt_tensor.misc_utils import (
    get_window,
    to_numpy_array,
    to_torch_tensor,
    _VALID_WINDOWS_TP,
    _VALID_WINDOWS,
)
from lt_utils.misc_utils import filter_kwargs


def convert_to_16_bits(
    audio: Tensor,
    apply_mx_norm: bool = False,
    out_mode: Literal["unchanged", "half", "short"] = "unchanged",
):
    """Convert and audio from float32 to float16"""
    if audio.dtype in [torch.float16, torch.bfloat16]:
        return audio
    if apply_mx_norm:
        data = audio / audio.abs().max()
    else:
        data = audio
    data = data * 32767
    if out_mode == "short":
        return data.short()
    elif out_mode == "half":
        return data.half()
    return data


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


class AudioProcessor(Model):
    def __init__(
        self,
        config: Union[AudioProcessorConfig, Dict[str, Any]] = AudioProcessorConfig(),
    ):
        super().__init__()
        assert isinstance(config, (AudioProcessorConfig, dict))
        self.cfg = (
            config
            if isinstance(config, AudioProcessorConfig)
            else AudioProcessorConfig(**config)
        )

        self._mel_padding = (self.cfg.n_fft - self.cfg.hop_length) // 2
        self.window = nn.Parameter(
            get_window(
                win_length=self.cfg.win_length,
                window_type=self.cfg.window_type,
                periodic=self.cfg.periodic_window,
                requires_grad=False,
                alpha=self.cfg.window_alpha,
                beta=self.cfg.window_beta,
            ),
            requires_grad=False,
        )
        self.mel_filter_bank = nn.Parameter(
            self.get_mel_filterbank(
                sample_rate=self.cfg.sample_rate,
                n_fft=self.cfg.n_fft,
                n_mels=self.cfg.n_mels,
                f_min=self.cfg.f_min,
                f_max=self.cfg.f_max,
            ),
            requires_grad=False,
        )

    @staticmethod
    def normalize_minmax(
        x: Tensor, min_val: float = -1.0, max_val: float = 1.0
    ) -> Tensor:
        """Scales tensor to [min_val, max_val] range."""
        x_min, x_max = x.min(), x.max()
        return (x - x_min) / (x_max - x_min + 1e-8) * (max_val - min_val) + min_val

    def get_mel_filterbank(
        self,
        sample_rate: Optional[int] = None,
        n_fft: Optional[int] = None,
        n_mels: Optional[int] = None,
        f_min: Optional[float] = None,
        f_max: Optional[float] = None,
    ):
        return torch.from_numpy(
            _mel_filter_bank(
                sr=default(sample_rate, self.cfg.sample_rate),
                n_fft=default(n_fft, self.cfg.n_fft),
                n_mels=default(n_mels, self.cfg.n_mels),
                fmin=default(f_min, self.cfg.f_min),
                fmax=default(f_max, self.cfg.f_max),
            )
        ).to(device=self.device)

    @staticmethod
    def range_norm(x: Tensor, C: Number = 1, clip_val: float = 0.00001):
        return torch.log(torch.clamp(x, min=clip_val) * C)

    def get_window(
        self,
        win_length: Optional[int] = None,
        periodic: Optional[bool] = None,
        window_type: Optional[_VALID_WINDOWS_TP] = None,
    ):
        window_type = default(window_type, self.cfg.window_type)
        win_length = default(win_length, self.cfg.win_length)
        periodic = default(periodic, self.cfg.periodic_window)
        if all(
            [
                win_length == self.cfg.win_length,
                window_type == self.cfg.window_type,
                periodic == self.cfg.periodic_window,
            ]
        ):
            return self.window

        kwargs = dict(
            win_length=win_length,
            periodic=periodic,
            device=self.device,
            requires_grad=False,
        )

        return get_window(**kwargs)

    def log_norm(
        self,
        entry: Tensor,
        eps: float = 1e-5,
        mean: Optional[Number] = None,
        std: Optional[Number] = None,
    ) -> Tensor:
        mean = default(mean, self.cfg.mean)
        std = default(std, self.cfg.std)
        return (torch.log(eps + entry.unsqueeze(0)) - mean) / std

    def _setup_wave_for_mel(self, wave: Tensor):
        if wave.ndim == 1:
            wave = wave.unsqueeze(0)
        elif wave.ndim == 3:
            wave = wave.squeeze(1)
        T = wave.size(-1)
        B = 1 if wave.ndim < 2 else wave.size(0)

        wave = torch.nn.functional.pad(
            wave.view(B, -1),
            (self._mel_padding, self._mel_padding),
            mode="reflect",
        )
        return to_device(wave.view(B, -1), device=self.device)

    def compute_mel(
        self,
        wave: Tensor,
        norm: Optional[bool] = None,
        norm_fn: Optional[Callable[[Tensor], Tensor]] = None,
        norm_type: Optional[Literal["log_norm", "range_norm"]] = None,
        *,
        # window related settings
        periodic_window: Optional[bool] = None,
        window_type: Optional[_VALID_WINDOWS_TP] = None,
        # other settings
        n_fft: Optional[int] = None,
        hop_length: Optional[int] = None,
        win_length: Optional[int] = None,
    ) -> Tensor:
        wave = self._setup_wave_for_mel(wave)

        spec = self.stft(
            wave=wave,
            n_fft=n_fft,
            hop_length=hop_length,
            win_length=win_length,
            pad_mode="reflect",
            center=False,
            normalized=False,
            return_complex=False,
            periodic_window=periodic_window,
            window_type=window_type,
        )
        spec = torch.sqrt(spec.pow(2).sum(-1) + 1e-12)
        results = torch.matmul(self.mel_filter_bank, spec)
        if default(norm, self.cfg.normalize_mel):
            if norm_fn is None:
                norm_type = default(norm_type, self.cfg.mel_normalizer)
                match norm_type:
                    case "range_norm":
                        return self.range_norm(results).squeeze()
                    case _:
                        return self.log_norm(results).squeeze()
            return norm_fn(results).squeeze()
        return results.squeeze()

    def convert_to_16_bits(
        self,
        audio: Tensor,
        apply_mx_norm: bool = False,
        out_mode: Literal["unchanged", "half", "short"] = "unchanged",
        *args,
        **kwargs,
    ):
        audio = to_torch_tensor(audio)
        return convert_to_16_bits(audio, apply_mx_norm, out_mode)

    def compute_pitch(
        self,
        audio: Tensor,
        *,
        sr: Optional[float] = None,
        fmin: int = 65,
        fmax: float = 2093,
        win_length: int = 30,
        frame_time: float = 10 ** (-2),
    ) -> Tensor:
        sr = default(sr, self.cfg.sample_rate)
        from torchaudio.functional import detect_pitch_frequency

        return detect_pitch_frequency(
            audio,
            sample_rate=sr,
            frame_time=frame_time,
            win_length=win_length,
            freq_low=fmin,
            freq_high=fmax,
        ).squeeze()

    def pitch_shift(
        self,
        audio: Tensor,
        sample_rate: Optional[int] = None,
        n_steps: float = 2.0,
        bins_per_octave: int = 12,
        res_type: Literal["soxr_vhq", "soxr_hq", "soxr_mq", "soxr_lq"] = "soxr_vhq",
        scale: bool = False,
    ) -> Tensor:
        """
        Shifts the pitch of an audio tensor by `n_steps` semitones.

        Args:
            audio (Tensor): Tensor of shape (B, T) or (T,)
            sample_rate (int, optional): Sample rate of the audio. Will use the class sample rate if unset.
            n_steps (float): Number of semitones to shift. Can be negative.
            res_type (Literal["soxr_vhq", "soxr_hq", "soxr_mq", "soxr_lq"]): Resample type. soxr Very high-, High-, Medium-, Low-quality FFT-based bandlimited interpolation. Defaults to 'soxr_vhq'
            scale (bool): Scale the resampled signal so that ``y`` and ``y_hat`` have approximately equal total energy.
        Returns:
            Tensor: Pitch-shifted audio.
        """
        src_device = audio.device
        src_dtype = audio.dtype
        audio = audio.squeeze()
        sample_rate = default(sample_rate, self.cfg.sample_rate)

        def _shift_one(wav: Tensor):
            wav_np = self.to_numpy_safe(wav)
            shifted_np = librosa.effects.pitch_shift(
                wav_np,
                sr=sample_rate,
                n_steps=n_steps,
                bins_per_octave=bins_per_octave,
                res_type=res_type,
                scale=scale,
            )
            return torch.from_numpy(shifted_np)

        if audio.ndim == 1:
            return _shift_one(audio).to(device=src_device, dtype=src_dtype)
        return torch.stack([_shift_one(a) for a in audio]).to(
            device=src_device, dtype=src_dtype
        )

    def from_numpy(
        self,
        array: np.ndarray,
        device: Optional[torch.device] = None,
        dtype: Optional[torch.dtype] = None,
    ) -> Tensor:
        converted = torch.from_numpy(array)
        if device is None:
            device = self.device
        return converted.to(device=device, dtype=dtype)

    def from_numpy_batch(
        self,
        arrays: List[np.ndarray],
        device: Optional[torch.device] = None,
        dtype: Optional[torch.dtype] = None,
    ) -> Tensor:
        stacked = torch.stack([torch.from_numpy(x) for x in arrays])
        if device is None:
            device = self.device
        return stacked.to(device=device, dtype=dtype)

    def to_numpy_safe(self, tensor: Union[Tensor, np.ndarray]) -> np.ndarray:
        if isinstance(tensor, np.ndarray):
            return tensor
        return to_numpy_array(tensor)

    def interpolate(
        self,
        wave: Tensor,
        target_len: int,
        mode: Literal[
            "nearest",
            "linear",
            "bilinear",
            "bicubic",
            "trilinear",
            "area",
            "nearest-exact",
        ] = "nearest",
        align_corners: Optional[bool] = None,
        scale_factor: Optional[list[float]] = None,
        recompute_scale_factor: Optional[bool] = None,
        antialias: bool = False,
    ) -> Tensor:
        """
        The modes available for upsampling are: `nearest`, `linear` (3D-only),
        `bilinear`, `bicubic` (4D-only), `trilinear` (5D-only)
        """
        T = wave.size(-1)
        B = 1 if wave.ndim < 2 else wave.size(0)
        C = 1 if wave.ndim < 3 else wave.size(-2)
        return F.interpolate(
            wave.view(B, C, T),
            size=target_len,
            mode=mode,
            align_corners=align_corners,
            scale_factor=scale_factor,
            recompute_scale_factor=recompute_scale_factor,
            antialias=antialias,
        )

    def sp_istft(
        self,
        spec: Tensor,
        phase: Tensor,
        n_fft: Optional[int] = None,
        hop_length: Optional[int] = None,
        win_length: Optional[int] = None,
        length: Optional[int] = None,
        center: bool = True,
        normalized: Optional[bool] = None,
        onesided: Optional[bool] = None,
        return_complex: bool = False,
        window: Optional[Tensor] = None,
        periodic_window: Optional[bool] = None,
        window_type: Optional[_VALID_WINDOWS_TP] = None,
    ) -> Tensor:
        """Util for models that needs to reconstruct the audio using istft (namely istft based models)"""
        window = default(
            window,
            self.get_window(
                win_length=win_length,
                periodic=periodic_window,
                window_type=window_type,
            ),
        )
        spec = to_other_device(spec, window)
        phase = to_other_device(spec, window)
        inp = spec * torch.exp(phase * 1j)
        if not inp.is_complex():
            inp = torch.view_as_complex(inp)

        return torch.istft(
            inp,
            n_fft=default(n_fft, self.cfg.n_fft),
            hop_length=default(hop_length, self.cfg.hop_length),
            win_length=default(win_length, self.cfg.win_length),
            window=window,
            center=center,
            normalized=default(normalized, self.cfg.normalized),
            onesided=default(onesided, self.cfg.onesided),
            length=length,
            return_complex=return_complex,
        )

    def istft(
        self,
        wave: Tensor,
        n_fft: Optional[int] = None,
        hop_length: Optional[int] = None,
        win_length: Optional[int] = None,
        length: Optional[int] = None,
        center: bool = True,
        normalized: Optional[bool] = None,
        onesided: Optional[bool] = None,
        return_complex: bool = False,
        window: Optional[Tensor] = None,
        periodic_window: Optional[bool] = None,
        window_type: Optional[_VALID_WINDOWS_TP] = None,
        *args,
        **kwargs,
    ) -> Tensor:
        window = default(
            window,
            self.get_window(
                win_length, periodic=periodic_window, window_type=window_type
            ),
        )
        if not torch.is_complex(wave):
            wave = wave * 1j
        return torch.istft(
            to_other_device(wave, window),
            n_fft=default(n_fft, self.cfg.n_fft),
            hop_length=default(hop_length, self.cfg.hop_length),
            win_length=default(win_length, self.cfg.win_length),
            window=default(
                window,
                self.get_window(
                    win_length, periodic=periodic_window, window_type=window_type
                ),
            ),
            center=center,
            normalized=default(normalized, self.cfg.normalized),
            onesided=default(onesided, self.cfg.onesided),
            length=length,
            return_complex=return_complex,
        )

    def stft(
        self,
        wave: Tensor,
        center: bool = True,
        n_fft: Optional[int] = None,
        hop_length: Optional[int] = None,
        win_length: Optional[int] = None,
        normalized: Optional[bool] = None,
        onesided: Optional[bool] = None,
        return_complex: bool = True,
        window: Optional[Tensor] = None,
        periodic_window: Optional[bool] = None,
        window_type: Optional[_VALID_WINDOWS_TP] = None,
        pad_mode: str = "reflect",
        *args,
        **kwargs,
    ) -> Tensor:
        window = default(
            window,
            self.get_window(
                win_length=win_length,
                periodic=periodic_window,
                window_type=window_type,
            ),
        )
        results = torch.stft(
            input=to_other_device(wave, window),
            n_fft=default(n_fft, self.cfg.n_fft),
            hop_length=default(hop_length, self.cfg.hop_length),
            win_length=default(win_length, self.cfg.win_length),
            window=window,
            center=center,
            pad_mode=pad_mode,
            normalized=default(normalized, self.cfg.normalized),
            onesided=default(onesided, self.cfg.onesided),
            return_complex=True,
        )
        if not return_complex:
            return torch.view_as_real(results)
        return results

    def loss_fn(self, inputs: Tensor, target: Tensor, ld: float = 1.0):
        if target.device != inputs.device:
            target = target.to(inputs.device)
        return (
            F.l1_loss(
                self.compute_mel(inputs), self.compute_mel(target.view_as(inputs))
            )
            * ld
        )

    def noise_reduction(
        self,
        audio: Union[Tensor, np.ndarray],
        noise_decrease: float = 0.25,
        n_fft: Optional[int] = None,
        win_length: Optional[int] = None,
        hop_length: Optional[int] = None,
        sample_rate: Optional[float] = None,
    ):
        import noisereduce as nr

        device = audio.device if isinstance(audio, Tensor) else None
        clear_audio = nr.reduce_noise(
            y=self.to_numpy_safe(audio),
            sr=default(sample_rate, self.cfg.sample_rate),
            n_fft=default(n_fft, self.cfg.n_fft),
            win_length=default(win_length, self.cfg.win_length),
            hop_length=default(hop_length, self.cfg.hop_length),
            prop_decrease=min(1.0, (max(noise_decrease, 1e-3))),
        )
        return self.from_numpy(clear_audio, device=device)

    def normalize_stft(
        self,
        wave: Tensor,
        length: Optional[int] = None,
        center: bool = True,
        n_fft: Optional[int] = None,
        hop_length: Optional[int] = None,
        win_length: Optional[int] = None,
        normalized: Optional[bool] = None,
        onesided: Optional[bool] = None,
        window: Optional[Tensor] = None,
        periodic_window: Optional[bool] = None,
        window_type: Optional[_VALID_WINDOWS_TP] = None,
        pad_mode: str = "reflect",
        return_complex: bool = False,
    ) -> Tensor:
        window = default(
            window,
            self.get_window(
                win_length=win_length,
                periodic=periodic_window,
                window_type=window_type,
            ),
        )
        device = wave.device
        general_kwargs = dict(
            n_fft=default(n_fft, self.cfg.n_fft),
            hop_length=default(hop_length, self.cfg.hop_length),
            win_length=default(win_length, self.cfg.win_length),
            window=window,
            center=center,
            normalized=default(normalized, self.cfg.normalized),
            onesided=default(onesided, self.cfg.onesided),
        )
        spectrogram = torch.stft(
            input=to_other_device(wave, window),
            pad_mode=pad_mode,
            return_complex=True,
            **general_kwargs,
        )
        return torch.istft(
            spectrogram
            * torch.full(
                spectrogram.size(),
                fill_value=1,
                device=spectrogram.device,
            ),
            length=length,
            return_complex=return_complex,
            **general_kwargs,
        ).to(device=device)

    def normalize_audio(
        self,
        wave: Tensor,
        top_db: Optional[float] = None,
        norm: Optional[float] = np.inf,
        norm_axis: int = 0,
        norm_threshold: Optional[float] = None,
        norm_fill: Optional[bool] = None,
        ref: float | Callable[[np.ndarray], Any] = np.max,
    ):
        if isinstance(wave, Tensor):
            wave = self.to_numpy_safe(wave)
        if top_db is not None:
            wave, _ = librosa.effects.trim(wave, top_db=top_db, ref=ref)
        wave = librosa.util.normalize(
            wave,
            norm=norm,
            axis=norm_axis,
            threshold=norm_threshold,
            fill=norm_fill,
        )
        results = torch.from_numpy(wave).float().unsqueeze(0).to(self.device)
        return self.normalize_stft(results)

    def load_audio(
        self,
        path: PathLike,
        normalize: Optional[bool] = None,
        noise_reduction: float = 0.0,
        mono: bool = True,
        sample_rate: Optional[float] = None,
        duration: Optional[float] = None,
        top_db: Optional[float] = None,
        other_normalizer: Optional[Callable[[Tensor], Tensor]] = None,
        *,
        top_db_ref_kwargs: Dict[str, Any] = {},
        librosa_normalize_kwargs: Dict[str, Any] = {},
        librosa_kwargs: Dict[str, Any] = {},
        **kwargs,
    ) -> Tensor:

        is_file(path, True)
        sample_rate = default(sample_rate, self.cfg.sample_rate)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            warnings.filterwarnings("ignore", category=UserWarning)
            warnings.filterwarnings("ignore", category=FutureWarning)
            wave, _ = librosa.load(
                str(path),
                sr=sample_rate,
                mono=mono,
                duration=duration,
                **filter_kwargs(
                    librosa.load,
                    False,
                    ["path", "sr", "mono", "duration"],
                    **librosa_kwargs,
                ),
            )

        if noise_reduction > 0:
            wave = self.noise_reduction(wave, noise_reduction)

        if top_db is not None:
            wave, _ = librosa.effects.trim(
                wave,
                top_db=top_db,
                **filter_kwargs(
                    librosa.effects.trim,
                    False,
                    ["y", "top_db"],
                    **top_db_ref_kwargs,
                ),
            )
        if default(normalize, self.cfg.normalized):
            wave = librosa.util.normalize(
                wave,
                **filter_kwargs(
                    librosa.util.normalize,
                    False,
                    ["S"],
                    **librosa_normalize_kwargs,
                ),
            )

        results = torch.from_numpy(wave).to(device=self.device, dtype=torch.float32)
        results = self.normalize_stft(results.view(1, results.size(-1)))
        if other_normalizer is not None:
            results = other_normalizer(results)
        return results.view(1, results.size(-1))

    def find_audios(
        self,
        path: PathLike,
        additional_extensions: List[str] = [],
        maximum: int | None = None,
    ):
        extensions = ["*.wav", "*.aac", "*.m4a", "*.mp3"]
        extensions.extend(
            [
                x if "*" in x else f"*{x}"
                for x in additional_extensions
                if isinstance(x, str)
            ]
        )
        return FileScan.files(
            path,
            extensions,
            maximum,
        )

    def collate_mel(self, mels: List[Tensor], same_size: bool = False):
        n_mels = mels[0].shape[-1]
        B = len(mels)
        if same_size:
            return torch.stack(mels, dim=0).view(B, n_mels, mels[0].shape[-1])
        largest = max([a.shape[-1] for a in mels])
        return torch.stack(
            [F.pad(x, (0, largest - x.shape[-1]), value=0.0) for x in mels], dim=0
        ).view(B, n_mels, mels[0].shape[-1])

    def collate_wave(self, waves: List[Tensor], same_size: bool = False):
        B = len(waves)
        if same_size:
            largest = waves[0].shape[-1]
            return torch.stack(waves, dim=0).view(B, waves[0].shape[-1])

        largest = max([a.shape[-1] for a in waves])
        return torch.stack(
            [F.pad(x, (0, largest - x.shape[-1]), value=0.0) for x in waves], dim=0
        ).view(B, largest)

    def get_audio_duration(
        self, audio: Optional[Tensor] = None, num_frames: Optional[int] = None
    ):
        """Returns the audio duration in seconds"""
        assert (
            audio is not None or num_frames is not None
        ), "Cannot process without any data!"
        if audio is not None:
            return audio.size(-1) / self.cfg.sample_rate
        return num_frames / self.cfg.sample_rate

    @staticmethod
    def audio_splitter(audio: Tensor, chunk_size: int = 8192):
        """Split the audio into several segments with the chunk_size"""
        chunks = []
        for fragment in list(
            torch.split(audio, split_size_or_sections=chunk_size, dim=-1)
        ):
            cur_size = fragment.shape[-1]
            if chunk_size > cur_size:
                fragment = F.pad(fragment, [0, chunk_size - cur_size], value=0.0)
            chunks.append(fragment[:chunk_size])
        return chunks

    @staticmethod
    def random_segment(audio: Tensor, chunk_size: int = 8192):
        """Gets a random segment with the size of chuck_size of the given audio"""
        if audio.size(-1) < chunk_size + 1:
            audio = F.pad(audio, [0, (chunk_size - audio.size(-1)) + 1], value=0.0)
        crop_distance = audio.size(-1) - chunk_size
        audio_start = torch.randint(0, crop_distance, (1,), dtype=torch.long).item()

        return audio[:, audio_start : audio_start + chunk_size]


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
        reduce_to_size: bool = False
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
        assert (
            len(n_mels)
            == len(window_lengths)
            == len(n_ffts)
            == len(hops)
            == len(f_min)
            == len(f_max)
        )
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
        n_ffts=[2048, 1024, 512],
        hop_lengths=[256, 128, 64],
        window: List[_VALID_WINDOWS_TP] = ["hann", "hann", "hann"],
        periodic=[False, False, False],
        alphas: Sequence[float] = [1.0, 1.0, 1.0],
        betas: Sequence[float] = [1.0, 1.0, 1.0],
        loss_fn: nn.Module = nn.L1Loss(),
        reduce_to_size: bool = False
    ):
        super().__init__()
        self.hops = hop_lengths
        self.ffts = n_ffts
        self.seq = nn.ModuleList(
            [
                SingleResolutionSTFTLoss(
                    fft, hop, loss_fn, window=win, periodic=per, alpha=ap, beta=bt
                )
                for fft, hop, win, per, ap, bt in zip(
                    n_ffts, hop_lengths, window, periodic, alphas, betas
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


class BandFilter(Model):
    def __init__(
        self,
        type_fn: Literal[
            "band",
            "lowpass",
            "highpass",
            "allpass",
            "bandpass",
            "bandreject",
            "bass",
            "treble",
            "equalizer",
        ] = "band",
        sr: Number = 24000,
        q_factor: float = 0.707,
        central_freq: float = 3072.0,
        gain: float = 1.0,
        eps: float = 1e-5,
        noise_csg: bool = False,
        requires_grad: bool = True,
        gain_requires_grad: bool = True,
    ) -> None:
        """
        Args:
            central_freq: (float, optional): Will be used as either central freq or cutoff_freq
                                            case type_fn is set to `lowpass`or `highpass`
            noise_csg: (bool, optional): Is used as 'noise' argument for 'band_biquad', and as 'const_skirt_gain' for 'bandpass_biquad'.
        """
        super().__init__()
        _valid_fn = [
            "band",
            "lowpass",
            "highpass",
            "allpass",
            "bandpass",
            "bandreject",
            "bass",
            "treble",
            "equalizer",
        ]
        assert type_fn in _valid_fn, (
            f'Invalid type_fn: {type_fn}. It must be: "' + '", '.join(_valid_fn) + '".'
        )
        self.sr = sr
        self.noise_csg = noise_csg

        # initial guardrails:
        eps = float(max(min(eps, 2**16 // 2 - 1), 1e-7))
        central_freq = float(max(central_freq, min(eps, 1e-5)))
        q_factor = float(max(q_factor, min(eps, 1e-5)))

        self.eps = eps

        self.central_freq = nn.Parameter(
            torch.as_tensor(central_freq),
            requires_grad=requires_grad,
        )
        self.Q_factor = nn.Parameter(
            torch.as_tensor(q_factor),
            requires_grad=requires_grad,
        )
        self.type_fn = type_fn
        self.gain = nn.Parameter(
            torch.as_tensor(float(gain)),
            requires_grad=gain_requires_grad and self.type_fn == "bass",
        )
        # to avoid NaN and zero values we clamp
        # both central frequencies[min,max] and q factor[min]
        self.register_buffer("cf_min", torch.as_tensor(eps))
        self.register_buffer("cf_max", torch.as_tensor((sr / 2) - eps))
        self.register_buffer("q_min", torch.as_tensor(eps))

        match self.type_fn:
            case "allpass":
                self.fn = lambda x, cf, Q: torchaudio.functional.allpass_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                )
            case "bandreject":
                self.fn = lambda x, cf, Q: torchaudio.functional.bandreject_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                )
            case "lowpass":
                self.fn = lambda x, cf, Q: torchaudio.functional.lowpass_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                )
            case "highpass":
                self.fn = lambda x, cf, Q: torchaudio.functional.highpass_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                )
            case "bass":
                self.fn = lambda x, cf, Q: torchaudio.functional.bass_biquad(
                    x,
                    self.sr,
                    self.gain,
                    cf,
                    Q,
                )
            case "treble":
                self.fn = lambda x, cf, Q: torchaudio.functional.treble_biquad(
                    x,
                    self.sr,
                    self.gain,
                    cf,
                    Q,
                )
            case "equalizer":
                self.fn = lambda x, cf, Q: torchaudio.functional.equalizer_biquad(
                    x,
                    self.sr,
                    cf,
                    self.gain,
                    Q,
                )
            case "bandpass":
                self.fn = lambda x, cf, Q: torchaudio.functional.bandpass_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                    self.noise_csg,
                )
            case _:
                self.fn = lambda x, cf, Q: torchaudio.functional.band_biquad(
                    x,
                    self.sr,
                    cf,
                    Q,
                    self.noise_csg,
                )

    def forward(self, x: Tensor):
        cf = self.central_freq.clamp(self.cf_min, self.cf_max)
        Q = self.Q_factor.clamp_min(self.q_min)
        return self.fn(x, cf, Q)


# Untested/Unfinished content
# it "works" but now model has been trained with this for now.
class FilterDiscriminator(Model):
    def __init__(
        self,
        hidden_dim: int = 128,
        sr: Number = 24000,
        q_factors: List[float] = [0.3673, 1.1539, 3.6249],
        central_freq: List[float] = [4.1416, 32.0062, 1225.0787],
        gain: List[float] = [6.25, 12.5, 25.0],
        eps: float = 1e-5,
        noise_csg: List[bool] = [False, False, True],
        filter_requires_grad: bool = True,
        filter_gain_requires_grad: bool = True,
        types_fn: List[str] = ["highpass", "lowpass", "equalizer"],
    ) -> None:
        """
        Args:
            ...
        """
        super().__init__()
        self.bn_models = nn.ModuleList()
        filter_kw = dict(
            sr=sr,
            eps=eps,
            requires_grad=filter_requires_grad,
            gain_requires_grad=filter_gain_requires_grad,
        )
        self.activ = nn.LeakyReLU()
        for q, cf, gn, noise, tp in zip(
            q_factors, central_freq, gain, noise_csg, types_fn
        ):
            self.bn_models.append(
                nn.ModuleDict(
                    dict(
                        fn=BandFilter(
                            type_fn=tp,
                            q_factor=q,
                            central_freq=cf,
                            gain=gn,
                            noise_csg=noise,
                            **filter_kw,
                        ),
                        conv=nn.Conv1d(
                            1,
                            4,
                            kernel_size=3,
                            padding=1,
                            bias=False,
                        ),
                    )
                )
            )

        layers = len(self.bn_models)
        from lt_tensor.model_zoo import BidirectionalConv

        self.bi_conv2d = BidirectionalConv(
            layers,
            layers,
            kernel_size=7,
            stride=2,
            dilation=4,
            padding=(7 - 1) * 4 // 2,
        )
        self.process = nn.ModuleList(
            [
                nn.Sequential(
                    nn.LeakyReLU(0.2),
                    nn.Conv2d(layers * 2, hidden_dim, 3, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.ConvTranspose2d(hidden_dim, hidden_dim, 4, 2, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.MaxPool2d(2),
                ),
                nn.Sequential(
                    nn.LeakyReLU(0.2),
                    nn.Conv2d(hidden_dim, hidden_dim, 3, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.ConvTranspose2d(hidden_dim, hidden_dim, 4, 2, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.MaxPool2d(2),
                ),
                nn.Sequential(
                    nn.LeakyReLU(0.2),
                    nn.Conv2d(hidden_dim, hidden_dim, 3, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.ConvTranspose2d(hidden_dim, hidden_dim // 2, 4, 2, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.MaxPool2d(2),
                ),
                nn.Sequential(
                    nn.LeakyReLU(0.2),
                    nn.Conv2d(hidden_dim // 2, 1, 3, padding=1),
                    nn.MaxPool2d(1, 2),
                    nn.Flatten(-2, -1),
                    nn.LeakyReLU(0.2),
                    nn.Conv1d(1, 1, 3, padding=1),
                ),
            ]
        )

    def pass_proc_layers(self, ct: Tensor):
        data = []
        for P in self.process:
            ct = P(ct)
            data.append(ct)
        return data

    def pass_encoder_layers(self, x: Tensor):
        data = []
        for C in self.bn_models:
            u = C["conv"](C["fn"](x))
            data.append(u)
        return data

    def forward(self, x: Tensor):
        data_bn = self.pass_encoder_layers(x)
        stacked = torch.stack(data_bn, dim=1)
        ct = self.bi_conv2d(stacked)
        post = self.pass_proc_layers(ct)
        return post[-1]

    def feature_forward(self, x: Tensor):
        all_features = []
        data_bn = self.pass_encoder_layers(x)
        stacked_data = torch.stack(data_bn, dim=1)
        ct = self.bi_conv2d(stacked_data)
        all_features.append(stacked_data)
        [all_features.append(j) for j in self.pass_proc_layers(ct)]
        return all_features
