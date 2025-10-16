import gc
import sys
import torch
import math
import random
import warnings
import numpy as np
from lt_utils.common import *
import torch.nn.functional as F
from torch import nn, optim, Tensor
from lt_tensor.tensor_ops import (
    to_other_device,
    to_device,
    all_to_device,
    to_numpy_array,
    to_torch_tensor,
    is_tensor,
    is_conv,
    is_tensor,
    ensure_2d,
    ensure_3d,
    ensure_4d,
)
from lt_tensor.display_utils import (
    time_weighted_avg,
    time_weighted_ema,
    plot_view,
    plot_token_heatmap_grid,
)


def minimum_device():
    return torch.device("cpu") if torch.cpu.is_available() else torch.zeros(1).device


DEFAULT_DEVICE = minimum_device()


_VALID_WINDOWS_TP: TypeAlias = Literal[
    "hann",
    "hamming",
    "blackman",
    "bartlett",
    "kaiser",
]
_VALID_WINDOWS = [
    "hann",
    "hamming",
    "blackman",
    "bartlett",
    "kaiser",
]


def get_window(
    win_length: int = 1024,
    window_type: _VALID_WINDOWS_TP = "hann",
    periodic: bool = False,
    alpha: float = 1.0,
    beta: float = 1.0,
    *,
    pin_memory: bool | None = False,
    requires_grad: bool | None = False,
    device: Optional[Union[str, torch.device]] = None,
    dtype: Optional[torch.dtype] = None,
):

    assert window_type in _VALID_WINDOWS, (
        f'Invalid window type {window_type}. It must be one of: "'
        + '", '.join(_VALID_WINDOWS)
        + '".'
    )

    kwargs = dict(
        window_length=win_length,
        periodic=periodic,
        device=device,
        pin_memory=pin_memory,
        requires_grad=requires_grad,
        dtype=dtype,
    )

    if window_type == "hamming":
        return torch.hamming_window(**kwargs, alpha=alpha, beta=beta)
    elif window_type == "blackman":
        return torch.blackman_window(
            **kwargs,
        )
    elif window_type == "bartlett":
        return torch.bartlett_window(**kwargs)
    elif window_type == "kaiser":
        return torch.kaiser_window(**kwargs, beta=beta)
    return torch.hann_window(**kwargs)


def is_fused_available():
    import inspect

    return "fused" in inspect.signature(optim.AdamW).parameters


def update_lr(optimizer: optim.Optimizer, new_value: Union[float, Tensor] = 1e-4):
    if isinstance(new_value, (int, float)):
        new_value = float(new_value)

    elif isinstance(new_value, Tensor):
        if new_value.squeeze().ndim in [0, 1]:
            try:
                new_value = float(new_value.item())
            except:
                pass

    new_value_float = isinstance(new_value, float)
    for param_group in optimizer.param_groups:
        if isinstance(param_group["lr"], Tensor) and new_value_float:
            param_group["lr"].fill_(new_value)
        else:
            param_group["lr"] = new_value
    return optimizer


def plot_view(
    data: Dict[str, List[Any]],
    title: str = "Loss",
    xaxis_title="Step/Epoch",
    yaxis_title="Loss",
    template="plotly_dark",
    smoothing: Optional[Literal["ema", "avg"]] = None,
    alpha: float = 0.5,
    *args,
    **kwargs,
):
    try:
        import plotly.graph_objs as go
    except ModuleNotFoundError:
        warnings.warn(
            "No installation of plotly was found. To use it use 'pip install plotly' and restart this application!"
        )
        return
    fig = go.Figure()
    for mode, values in data.items():
        if values:
            if not smoothing:
                items = values
            elif smoothing == "avg":
                items = time_weighted_avg(values, kwargs.get("smoothing_alpha", alpha))
            else:
                items = time_weighted_ema(values, kwargs.get("smoothing_alpha", alpha))
            fig.add_trace(go.Scatter(y=items, name=mode.capitalize()))
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template=template,
    )
    return fig


def updateDict(self, dct: dict[str, Any]):
    for k, v in dct.items():
        setattr(self, k, v)


def try_torch(fn: str, *args, **kwargs):
    tried_torch = False
    not_present_message = (
        f"Both `torch` and `torch.nn.functional` does not contain the module `{fn}`"
    )
    try:
        if hasattr(F, fn):
            return getattr(F, fn)(*args, **kwargs)
        elif hasattr(torch, fn):
            tried_torch = True
            return getattr(torch, fn)(*args, **kwargs)
        return not_present_message
    except Exception as a:
        try:
            if not tried_torch and hasattr(torch, fn):
                return getattr(torch, fn)(*args, **kwargs)
            return str(a)
        except Exception as e:
            return str(e) + " | " + str(a)


def enable_module(activation, **kwargs):
    """Ensure if the module and/or activation is valid or not, deploy if it is"""
    from lt_utils.misc_utils import filter_kwargs

    if not isinstance(activation, type):
        activ = activation
    else:
        try:
            kw = filter_kwargs(activation, False, [], **kwargs)
        except:
            kw = {}
        if kw:
            activ = activation(**kw)
        else:
            activ = activation()

    assert isinstance(activ, nn.Module) or callable(
        activ
    ), f"Invalid activation function: {activation}"
    return activ


def get_tensor_data(
    inp: Union[Tensor, nn.Parameter],
    dim: Optional[int] = None,
    *,
    mean: bool = True,
    std: bool = True,
    min_max: bool = True,
    check_nan: bool = False,
    dtype_info: bool = False,
    grad: bool = False,
    detach_grad: bool = False,
    check_inf: bool = False,
    std_unbiased: bool = False,
    std_correction: Optional[Number] = None,
    **kwargs,
):
    from lt_utils.misc_utils import filter_kwargs

    def _try_call_(fn: Callable[[Tensor], Any]):
        try:
            return fn(inp)
        except Exception as e:
            return e

    is_complex = torch.is_complex(inp)
    data = dict(
        dim=inp.ndim,
        dtype=inp.dtype,
        device=inp.device,
        is_complex=is_complex,
    )
    if grad:
        if hasattr(inp, "grad"):
            if inp.grad is None:
                data["grad"] = inp.grad
            else:
                if detach_grad:
                    data["grad"] = inp.grad.detach()
                else:
                    data["grad"] = inp.grad
    if check_inf or check_nan:
        nan_vals = []

        data["invalid"] = False
        if check_inf:
            inf_a = inp == torch.inf
            inf_b = inp == -torch.inf
            inf_comb = inf_a + inf_b
            data["has_inf"] = inf_comb.any().item()
            data["is_all_inf"] = False if not data["has_inf"] else inf_comb.all().item()

        if check_nan:
            if is_complex:
                _inp = torch.view_as_real(inp).flatten().tolist()
            else:
                _inp = inp.flatten().tolist()
            nan_vals = [math.isnan(x) for x in _inp]
            data["has_nan"] = any(nan_vals)
            data["is_all_nan"] = False if not data["has_nan"] else all(nan_vals)
            if check_inf:
                data["invalid"] = all([math.isinf(x) or math.isnan(x) for x in _inp])

    if min_max:
        data.update(
            dict(
                minimum=_try_call_(lambda x: torch.min(x)),
                maximum=_try_call_(lambda x: torch.max(x)),
            )
        )
    if mean:
        data.update(dict(mean=_try_call_(torch.mean)))
    if std:
        if std_correction is not None:
            data.update(
                dict(
                    std=_try_call_(
                        lambda x: torch.std(x, dim=dim, correction=std_correction)
                    )
                )
            )
        else:
            data.update(
                dict(
                    std=_try_call_(
                        lambda x: torch.std(x, dim=dim, unbiased=std_unbiased)
                    )
                )
            )
    # dtype info
    if dtype_info:
        _dtype_info = torch.finfo(inp.dtype)
        torch.finfo(inp.dtype).bits

        data["dtype_info"] = dict(
            bits=_dtype_info.bits,
            eps=_dtype_info.eps,
            resolution=_dtype_info.resolution,
            dt_min=_dtype_info.min,
            dt_max=_dtype_info.max,
            tiny=_dtype_info.tiny,
            smallest_normal=_dtype_info.smallest_normal,
        )
    return data


def log_tensor_v2(
    item: Union[Tensor, np.ndarray],
    title: str = "...",
    logger_fn: Callable[[str], None] = print,
    dtype: bool = True,
    ndim: bool = True,
    device: bool = True,
    show_tensor: bool = False,
    *,
    dim: Optional[int] = None,
    mean: bool = True,
    std: bool = True,
    min_max: bool = True,
    check_nan: bool = False,
    check_inf: bool = False,
    std_unbiased: bool = False,
    std_correction: Optional[Number] = None,
    grad: bool = False,
    detach_grad: bool = False,
    dtype_info: bool = False,
    **kwargs,
):
    try:
        item = torch.as_tensor(item)
    except Exception as e:
        try:
            item = torch.as_tensor(np.asarray(item))
        except:
            raise e

    data = get_tensor_data(
        item,
        dim=dim,
        mean=mean,
        std=std,
        min_max=min_max,
        check_nan=check_nan,
        check_inf=check_inf,
        std_unbiased=std_unbiased,
        std_correction=std_correction,
        grad=grad,
        detach_grad=detach_grad,
        dtype_info=dtype_info,
        **kwargs,
    )
    if not title:
        title = "..."
    logger_fn("========[" + title.title() + "]========")
    _b = 20 + len(title.strip())

    def _slice_if_number(target: Any):
        if isinstance(target, Number):
            return f"{target:.4f}"
        if isinstance(target, Tensor):
            try:
                return f"{target.item():.4f}"
            except:
                return target
        return target

    logger_fn(f"shape: {item.shape}")
    if dtype:
        logger_fn(f"dtype: {item.dtype}")
    if ndim:
        logger_fn(f"ndim: {item.ndim}")
    if device:
        logger_fn(f"device: {item.device}")
    if mean:
        logger_fn(f"mean: {_slice_if_number(data['mean'])}")
    if std:
        logger_fn(f"std: {_slice_if_number(data['std'])}")
    if min_max:
        logger_fn(f"min: {_slice_if_number(data.get('minimum'))}")
        logger_fn(f"max: {_slice_if_number(data.get('maximum'))}")
    if check_inf:
        logger_fn(f"has any infinite: {_slice_if_number(data.get('has_inf'))}")
        logger_fn(f"all infinite: {_slice_if_number(data.get('is_all_inf'))}")
    if check_nan:
        logger_fn(f"has any NaN: {_slice_if_number(data.get('has_nan'))}")
        logger_fn(f"all NaNs: {_slice_if_number(data.get('is_all_nan'))}")
        if check_inf:
            logger_fn(f"invalid [NaNs and infs]: {data.get('invalid', False) }")

    if show_tensor:
        logger_fn(item)

    logger_fn("".join(["-"] * _b) + "\n")
    sys.stdout.flush()
    return data


def log_tensor(
    item: Union[Tensor, np.ndarray],
    title: Optional[str] = None,
    print_details: bool = True,
    print_tensor: bool = False,
    dim: Optional[int] = None,
):
    try:
        item = torch.as_tensor(item)
    except Exception as e:
        try:
            item = torch.as_tensor(np.asarray(item))
        except:
            raise e
    from lt_utils.type_utils import is_str

    if not title:
        title = "..."
    complex_type = item.is_complex()

    print("========[" + title.title() + "]========")
    _b = 20 + len(title.strip())
    print(f"shape: {item.shape}")
    print(f"dtype: {item.dtype}")
    print(f"complex: {complex_type}")
    if print_details:
        print(f"ndim: {item.ndim}")
        if isinstance(item, Tensor):
            print(f"device: {item.device}")
            try:
                print(f"min: {item.amin():.4f}")
                print(f"max: {item.amax():.4f}")
            except:
                pass
            try:
                print(f"std: {item.std(dim=dim):.4f}")
            except:
                pass
            try:

                print(f"mean: {item.mean(dim=dim):.4f}")
            except:
                pass
    if print_tensor:
        print(item)
    print("".join(["-"] * _b))
    print()
    sys.stdout.flush()


def get_losses(base: Tensor, target: Tensor, return_valid_only: bool = False):
    losses = {}
    losses["mse_loss"] = try_torch("mse_loss", base, target)
    losses["l1_loss"] = try_torch("l1_loss", base, target)
    losses["huber_loss"] = try_torch("huber_loss", base, target)
    losses["poisson_nll_loss"] = try_torch("poisson_nll_loss", base, target)
    losses["smooth_l1_loss"] = try_torch("smooth_l1_loss", base, target)
    losses["cross_entropy"] = try_torch("cross_entropy", base, target)
    losses["soft_margin_loss"] = try_torch("soft_margin_loss", base, target)
    losses["nll_loss"] = try_torch("nll_loss", base, target)
    losses["gaussian_nll_loss"] = try_torch("gaussian_nll_loss", base, target, var=1.0)
    losses["gaussian_nll_loss-var_0.25"] = try_torch(
        "gaussian_nll_loss", base, target, var=0.25
    )
    losses["gaussian_nll_loss-var_4.0"] = try_torch(
        "gaussian_nll_loss", base, target, var=4.0
    )
    if not return_valid_only:
        return losses
    valid = {}
    for name, loss in losses.items():
        if isinstance(loss, str):
            continue
        valid[name] = loss
    return valid


def set_seed(seed: int):
    """Set random seed for reproducibility."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if torch.mps.is_available():
        torch.mps.manual_seed(seed)
    if torch.xpu.is_available():
        torch.xpu.manual_seed_all(seed)


def count_parameters(model: nn.Module) -> int:
    """Returns total number of trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def freeze_all_except(model: nn.Module, except_layers: Optional[list[str]] = None):
    """Freezes all model parameters except specified layers."""
    no_exceptions = not except_layers
    for name, param in model.named_parameters():
        if no_exceptions:
            param.requires_grad_(False)
        elif any(layer in name for layer in except_layers):
            param.requires_grad_(False)


def freeze_selected_weights(model: nn.Module, target_layers: list[str]):
    """Freezes only parameters on specified layers."""
    for name, param in model.named_parameters():
        if any(layer in name for layer in target_layers):
            param.requires_grad_(False)


def unfreeze_all_except(model: nn.Module, except_layers: Optional[list[str]] = None):
    """Unfreezes all model parameters except specified layers."""
    no_exceptions = not except_layers
    for name, param in model.named_parameters():
        if no_exceptions:
            param.requires_grad_(True)
        elif not any(layer in name for layer in except_layers):
            param.requires_grad_(True)


def unfreeze_selected_weights(model: nn.Module, target_layers: list[str]):
    """Unfreezes only parameters on specified layers."""
    for name, param in model.named_parameters():
        if not any(layer in name for layer in target_layers):
            param.requires_grad_(True)


def sample_tensor(tensor: Tensor, num_samples: int = 5):
    """Randomly samples values from tensor for preview."""
    flat = tensor.flatten()
    idx = torch.randperm(len(flat))[:num_samples]
    return flat[idx]


def clear_cache():
    if torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
        except:
            pass
    if torch.mps.is_available():
        try:
            torch.mps.empty_cache()
        except:
            pass
    if torch.xpu.is_available():
        try:
            torch.xpu.empty_cache()
        except:
            pass
    if hasattr(torch, "mtia"):
        try:
            torch.mtia.empty_cache()
        except:
            pass
    gc.collect()
