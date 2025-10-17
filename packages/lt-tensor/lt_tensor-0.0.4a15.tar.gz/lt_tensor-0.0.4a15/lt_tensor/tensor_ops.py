import torch
import copy
from torch import Tensor, nn
from typing import TypeGuard
from torch.nn import functional as F
from lt_utils.common import *
from lt_utils.type_utils import is_array_of
from lt_tensor._other_ops.torchaudio.cqt_vqt import (
    CQT,
    VQT,
    InverseCQT,
    relative_bandwidths,
    wavelet_fbank,
    wavelet_lengths,
    frequency_set,
)
from lt_tensor._other_ops.torchaudio.functional import (
    combine_max,
    median_smoothing,
    compute_mat_trace,
    tik_reg,
    compute_nccf,
    find_max_per_frame,
    rnnt_loss,
    apply_convolve_mode,
)
import numpy as np


def sin_freq(x: Tensor, freq: float = 1.0) -> Tensor:
    """Applies sine function element-wise."""
    return torch.sin(x * freq)


def cos_freq(x: Tensor, freq: float = 1.0) -> Tensor:
    """Applies cosine function element-wise."""
    return torch.cos(x * freq)


def sin_plus_cos(x: Tensor, freq: float = 1.0) -> Tensor:
    """Returns sin(x) + cos(x)."""
    return torch.sin(x * freq) + torch.cos(x * freq)


def sin_times_cos(x: Tensor, freq: float = 1.0) -> Tensor:
    """Returns sin(x) * cos(x)."""
    return torch.sin(x * freq) * torch.cos(x * freq)


def apply_window(x: Tensor, window_type: Literal["hann", "hamming"] = "hann") -> Tensor:
    """Applies a window function to a 1D tensor."""
    if window_type == "hamming":
        window = torch.hamming_window(x.shape[-1], device=x.device)
    else:
        window = torch.hann_window(x.shape[-1], device=x.device)
    return x * window


def dot_product(x: Tensor, y: Tensor, dim: int = -1) -> Tensor:
    """Computes dot product along the specified dimension."""
    return torch.sum(x * y, dim=dim)


def one_hot(labels: Tensor, num_classes: int) -> Tensor:
    """One-hot encodes a tensor of labels."""
    return F.one_hot(labels, num_classes).float()


def view_as_complex(tensor: Tensor):
    if not torch.is_complex(tensor):
        if tensor.size(-1) == 2:  # maybe real+imag as last dim
            return torch.view_as_complex(tensor)

        # treat as real and multiply by 1j
        return tensor * (1j)
    return tensor


def log_magnitude(stft_complex: Tensor, eps: float = 1e-6) -> Tensor:
    """
    Compute magnitude from STFT tensor.
    Args:
        stft: [B, F, T] tensor (complex or real)
    Returns:
        magnitude: [B, F, T] real tensor
    """
    if not torch.is_complex(stft):
        stft = view_as_complex(stft)
    magnitude = torch.abs(stft_complex)
    return torch.log(magnitude + eps)


def stft_phase_ola(
    stft: Tensor, n_fft: int, hop_length: int, win_length: int = None, window=None
):
    """
    Reconstruct phase (OLA style) from complex STFT.
    Args:
        stft: [B, F, T] complex tensor
        n_fft: FFT size
        hop_length: hop size
        win_length: window length
        window: torch window (optional)
    Returns:
        phase: [B, F, T] tensor of angles (radians)
    """
    # Inverse STFT (reconstruct waveform by overlap-add)
    if not torch.is_complex(stft):
        stft = view_as_complex(stft)

    wav = torch.istft(
        stft, n_fft=n_fft, hop_length=hop_length, win_length=win_length, window=window
    )
    # Forward STFT again to enforce consistency
    stft_re = torch.stft(
        wav,
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        window=window,
        return_complex=True,
    )

    return torch.angle(stft_re)


def channel_randomizer(
    x: Tensor,
    combinations: int = 1,
    dim: int = 1,
) -> Tensor:
    """
    Randomizes channels along a dimension, with optional grouping.
    Args:
        x: Tensor [B, C, T] or [C, T]
        combinations: Number of groups/combinations to split channels into.
                groups=1 -> shuffle all channels freely
                groups=C -> no shuffle
        dim: channel dimension (1 for [B, C, T], 0 for [C, T])
    Returns:
        shuffled tensor
    """
    C = x.shape[dim]
    if C % combinations != 0:
        raise ValueError(
            f"Number of channels {C} not divisible by groups={combinations}"
        )

    # reshape into groups
    group_size = C // combinations
    shape = list(x.shape)
    shape[dim] = combinations
    shape.insert(dim + 1, group_size)
    xg = x.reshape(shape)

    # permutation of groups
    perm = torch.randperm(combinations, device=x.device)
    xg = xg.index_select(dim, perm)

    # flatten back
    x = xg.reshape(list(x.shape))
    return x


def channel_randomizer2(
    x: Tensor,
    groups: int = 1,
    dim: int = 1,
    shuffle_within: bool = False,
) -> Tensor:
    """
    Randomizes/shuffles channels in groups, optionally shuffling inside groups as well.
    Args:
        x: [B, C, T] or [C, T] tensor
        groups: number of groups to split channels into
        dim: channel dimension (default=1 for batched)
        shuffle_within: if True, shuffle channels inside each group,
                        if False, only shuffle group order
    Returns:
        shuffled tensor (detached, no graph)
    """
    C = x.shape[dim]
    if C % groups != 0:
        raise ValueError(f"Channels ({C}) must be divisible by groups={groups}")
    group_size = C // groups

    # Reshape into groups
    shape = list(x.shape)
    shape[dim] = groups
    shape.insert(dim + 1, group_size)
    xg = x.detach().reshape(shape)

    if shuffle_within:
        # Shuffle inside each group independently
        idx = np.arange(group_size)
        perms = [np.random.permutation(idx) for _ in range(groups)]
        perms = np.stack(perms)
        perms = torch.from_numpy(perms).to(x.device)

        arange_groups = torch.arange(groups, device=x.device)[:, None].expand(
            -1, group_size
        )
        xg = xg[(*[slice(None)] * dim, arange_groups, perms)]
    else:
        # Shuffle groups only
        perm = torch.randperm(groups, device=x.device)
        xg = xg.index_select(dim, perm)

    return xg.reshape(list(x.shape))


def compact_embeddings(
    x: Tensor,
    factor: int = 2,
    normalize: bool = True,
) -> Tensor:
    """
    Compact embeddings along the feature dimension by averaging groups of size `factor`.
    Args:
        x: [B, D] or [B, T, D] tensor
        factor: reduction factor
        normalize: whether to L2-normalize after compaction
    Returns:
        compacted tensor with reduced feature dimension
    """
    if x.shape[-1] % factor != 0:
        raise ValueError(f"Feature dim {x.shape[-1]} not divisible by factor={factor}")

    new_dim = x.shape[-1] // factor
    shape = list(x.shape[:-1]) + [new_dim, factor]
    x = x.reshape(shape).mean(dim=-1)

    if normalize:
        norm = torch.norm(x, p=2, dim=-1, keepdim=True).clamp(min=1e-6)
        x = x / norm
    return x


def sub_outer(tensor: Tensor, other: Tensor):
    return tensor.reshape(-1, 1) - other


def sub_outer_b(tensor: Tensor, other: Tensor, *, dim: int = 1):
    return tensor.unsqueeze(dim) - other


def normalize_unit_norm(x: Tensor, eps: float = 1e-6):
    norm = torch.norm(x, dim=-1, keepdim=True)
    return x / (norm + eps)


def normalize_minmax(
    x: Tensor,
    min_val: float = -1.0,
    max_val: float = 1.0,
    dim: Union[Sequence[int], int] = (),
    eps: float = 1e-6,
) -> Tensor:
    """Scales tensor to [min_val, max_val] range."""
    x_min, x_max = x.amin(dim=dim), x.amax(dim=dim)
    return (x - x_min) / (x_max - x_min + eps) * (max_val - min_val) + min_val


def normalize_zscore(
    x: Tensor, dim: int = -1, keep_dims: bool = True, eps: float = 1e-6
):
    mean = x.mean(dim=dim, keepdim=keep_dims)
    std = x.std(dim=dim, keepdim=keep_dims)
    return (x - mean) / (std + eps)


def spectral_norm(x: Tensor, c: int = 1, eps: float = 1e-6) -> Tensor:
    return torch.log(torch.clamp(x, min=eps) * c)


def spectral_de_norm(x: Tensor, c: int = 1) -> Tensor:
    return torch.exp(x) / c


def log_norm(entry: Tensor, mean: float, std: float, eps: float = 1e-6) -> Tensor:
    return (eps + entry.log() - mean) / max(std, 1e-6)


def clip_gradients(model: nn.Module, max_norm: float = 1.0):
    """Applies gradient clipping."""
    return nn.utils.clip_grad_norm_(model.parameters(), max_norm)


def detach(entry: Union[Tensor, Tuple[Tensor, ...]]):
    """Detaches tensors (for RNNs)."""
    if isinstance(entry, Tensor):
        return entry.detach()
    return tuple(detach(h) for h in entry)


def non_zero(value: Union[float, Tensor], eps: float = 1e-6):
    _value = value.item() if isinstance(value, Tensor) else value
    if not _value:
        return value + eps
    return value


def safe_divide(a: Tensor, b: Tensor, eps: float = 1e-6):
    """Safe division for tensors (prevents divide-by-zero)."""
    try:
        return a / b
    except:
        return a / (b + eps)


def is_same_dim(tensor1: Tensor, tensor2: Tensor):
    return tensor1.ndim == tensor2.ndim


def is_same_shape(
    tensor1: Tensor,
    tensor2: Tensor,
    dim: Optional[int] = None,
    validate: bool = False,
):
    results = tensor1.size(dim) == tensor2.size(dim)
    assert (
        not validate or results
    ), f"Shapes mismatch: `tensor1` with size: {tensor1.size()} does not match `tensor2` with size {tensor2.size()}."
    return results


def ensure_2d(x: Tensor):
    if x.ndim == 2:
        return x
    B = 1 if x.ndim < 2 else x.size(0)
    return x.view(B, -1)


def ensure_3d(x: Tensor, t_centered: bool = False):
    if x.ndim != 3:
        B = 1 if x.ndim < 2 else x.size(0)
        T = 1 if not x.ndim else x.size(-1)  # scalar
        x = x.view(B, -1, T)
        if t_centered:
            x = x.transpose(-1, -2)
    return x


def ensure_4d(x: Tensor, t_centered: bool = False):
    if x.ndim != 4:
        B = 1 if x.ndim < 2 else x.size(0)
        T = 1 if not x.ndim else x.size(-1)
        x = x.view(B, 1, -1, T)
        if t_centered:
            x = x.transpose(-2, -3)
    return x


def is_tensor(item: Any) -> TypeGuard[Tensor]:
    return isinstance(item, Tensor)


def to_torch_tensor(inp: Union[Tensor, np.ndarray, List[Number], Number]):

    if is_tensor(inp):
        return inp
    try:
        return torch.as_tensor(
            inp, dtype=None if not isinstance(inp, int) else torch.long
        )
    except:
        pass
    if isinstance(inp, (int, float)):
        if isinstance(inp, int):
            return torch.tensor(inp, dtype=torch.long)
        return torch.tensor(inp)
    elif isinstance(inp, (list, tuple)):
        return torch.tensor([float(x) for x in inp if isinstance(x, (int, float))])
    elif isinstance(inp, np.ndarray):
        return torch.from_numpy(inp)
    raise ValueError(f"'{inp}' cannot be converted to tensor! (type: {type(inp)})")


def to_numpy_array(
    inp: Union[Tensor, np.ndarray, List[Number], Number],
    dtype: Optional[np.dtype] = None,
):
    if isinstance(inp, (np.ndarray, list, int, float, tuple)):
        return np.asarray(inp, dtype=dtype)

    if isinstance(inp, Tensor):
        return np.asarray(inp.detach().tolist(), dtype=dtype)

    return np.asanyarray(inp, dtype=dtype)


def is_conv(module: nn.Module) -> TypeGuard[nn.modules.conv._ConvNd]:
    return isinstance(
        module,
        (
            nn.Conv1d,
            nn.Conv2d,
            nn.Conv3d,
            nn.ConvTranspose1d,
            nn.ConvTranspose2d,
            nn.ConvTranspose3d,
            nn.LazyConv1d,
            nn.LazyConv2d,
            nn.LazyConv3d,
            nn.LazyConvTranspose1d,
            nn.LazyConvTranspose2d,
            nn.LazyConvTranspose3d,
            nn.modules.conv._ConvNd,
        ),
    )


def _conv_padding_helper(k: int, d: int, mode: Literal["a", "b"] = "a"):
    k = max(k, 1)
    d = max(d, 1)
    if mode == "a":
        return (k - 1) * d // 2
    return (k * d - d) // 2


def get_padding_conv(
    kernel_size: Union[int, Sequence[int]],
    dilation: Union[int, Sequence[int]],
    mode: Literal["a", "b"] = "a",
):
    _is_int_kernel = isinstance(kernel_size, int)
    _is_int_dilation = isinstance(dilation, int)

    if _is_int_kernel and _is_int_dilation:
        return _conv_padding_helper(kernel_size, dilation, mode)
    elif not _is_int_kernel and not _is_int_dilation:
        return tuple(
            _conv_padding_helper(k, d, mode) for k, d in zip(kernel_size, dilation)
        )
    elif _is_int_dilation:
        return tuple(_conv_padding_helper(k, dilation, mode) for k in kernel_size)

    return tuple(_conv_padding_helper(kernel_size, d, mode) for d in dilation)


def to_other_device(tensor: Tensor, other_tensor: Tensor):
    if tensor.device.type == other_tensor.device.type:
        return tensor
    return tensor.to(other_tensor.device)


def to_device(tensor: Tensor, device: Union[str, torch.device]):
    if isinstance(device, torch.device):
        device = device.type
    if tensor.device.type == device:
        return tensor
    return tensor.to(device)


def _to_device_kwargs(device: Union[str, torch.device], **kwargs):
    proc_kwargs = {}
    for k, v in kwargs.items():
        if isinstance(v, (Tensor, nn.Module, nn.Parameter)):
            proc_kwargs.update({k: to_device(v, device=device)})
        elif isinstance(v, (list, tuple)):
            proc_kwargs.update({k: _to_device_args(device, *v)})
        elif isinstance(v, dict):
            proc_kwargs.update({k: _to_device_kwargs(v)})
        else:
            proc_kwargs.update({k: v})

    return proc_kwargs


def _to_device_args(device: Union[str, torch.device], *args):
    proc_args = []
    for arg in args:
        if isinstance(arg, (Tensor, nn.Module, nn.Parameter)):
            proc_args.append(to_device(arg, device=device))
        elif isinstance(arg, (list, tuple)):

            proc_args.append(_to_device_args(device, *arg))
        elif isinstance(arg, dict):
            proc_args.append(_to_device_kwargs(device, **arg))
        else:
            proc_args.append(arg)

    return proc_args


def all_to_device(device: Union[str, torch.device], *args, **kwargs):
    kw = _to_device_kwargs(device, **kwargs)
    arg = _to_device_args(device, *args)
    return arg, kw


def move_list_to_device(
    entries: Union[List[Union[Any, Tensor]], Tuple[Union[Any, Tensor], ...]],
    device: Union[str, torch.device],
    max_depth: int = 3,
    *,
    _depth: int = 0,
):
    was_tuple = isinstance(entries, tuple)
    if was_tuple:
        entries_list = [x for x in copy.copy(entries)]
        entries = entries_list

    for i in range(len(entries)):
        if is_tensor(entries[i]):
            entries[i] = entries[i].to(device=device)
        elif _depth >= max_depth:
            continue
        elif isinstance(entries[i], dict):
            entries[i] = move_dict_to_device(
                entries[i], device=device, _depth=_depth + 1
            )
        elif isinstance(entries[i], (tuple, list)):
            entries[i] = move_list_to_device(
                entries[i], device=device, _depth=_depth + 1
            )
    if was_tuple:
        return tuple(entries)
    return entries


def move_dict_to_device(
    entries: Dict[str, Union[Any, Tensor]],
    device: Union[str, torch.device],
    max_depth: int = 3,
    *,
    _depth: int = 0,
):
    keys = list(entries.keys())
    for k in keys:
        if is_tensor(entries[k]):
            entries[k] = entries[k].to(device)
        elif _depth >= max_depth:
            continue
        elif isinstance(entries[k], dict):
            entries[k] = move_dict_to_device(
                entries[k], device=device, _depth=_depth + 1
            )
        elif isinstance(entries[k], (list, tuple)):
            entries[k] = move_list_to_device(
                entries[k], device=device, _depth=_depth + 1
            )
    return entries
