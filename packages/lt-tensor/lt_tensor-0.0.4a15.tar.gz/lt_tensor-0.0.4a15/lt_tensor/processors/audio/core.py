__all__ = ["AudioProcessor"]
import warnings
import librosa
import numpy as np
from lt_utils.common import *
from lt_tensor.common import *
from lt_utils.misc_utils import default
import torch.nn.functional as F
from lt_utils.file_ops import FileScan, is_file
from librosa.filters import mel as _mel_filter_bank
from lt_tensor.tensor_ops import to_device, to_other_device
from lt_tensor.misc_utils import (
    get_window,
    to_numpy_array,
    to_torch_tensor,
    _VALID_WINDOWS_TP,
)
from .utils import convert_to_16_bits
from lt_utils.misc_utils import filter_kwargs
from .configs import AudioProcessorConfig


class AudioProcessor(Model):
    def __init__(
        self,
        config: Union[AudioProcessorConfig, Dict[str, Any]] = AudioProcessorConfig(),
        seed: Optional[int] = None,
    ):
        super().__init__(seed=seed)
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
        *,
        max_norm: bool = False,
        out_mode: Literal["default", "half", "short"] = "default",
        **kwargs,
    ):
        audio = to_torch_tensor(audio)
        return convert_to_16_bits(audio, max_norm, out_mode)

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
        offset: float = 0.0,
        res_type: Literal[
            "soxr_vhq",
            "soxr_hq",
            "soxr_mq",
            "soxr_lq",
            "soxr_qq",
            "kaiser_best",
            "kaiser_fast",
            "fft",
            "scipy",
            "polyphase",
            "linear",
            "zero_order_hold",
            "sinc_best",
            "sinc_medium",
            "sinc_fastest",
        ] = "soxr_vhq",
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
                offset=offset,
                res_type=res_type,
                **filter_kwargs(
                    librosa.load,
                    False,
                    ["path", "sr", "mono", "duration", "offset", "res_type"],
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
