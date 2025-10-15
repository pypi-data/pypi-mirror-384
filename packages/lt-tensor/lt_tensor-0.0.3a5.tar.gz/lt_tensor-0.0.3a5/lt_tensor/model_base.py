from __future__ import annotations

import torch
import warnings
from abc import ABC
from torch import nn, Tensor
from lt_utils.common import *
from lt_utils.type_utils import is_dict
from lt_tensor.misc_utils import set_seed
from lt_tensor.misc_utils import clear_cache
from lt_utils.misc_utils import get_current_time

from typing import TypeVar, Mapping, OrderedDict, Self, TYPE_CHECKING
from typing_extensions import override, overload

from lt_utils.file_ops import (
    load_json,
    save_json,
    load_yaml,
    save_yaml,
    find_files,
    is_file,
    is_path_valid,
    is_pathlike,
)

from lt_tensor.misc_utils import updateDict, DEFAULT_DEVICE, to_device

if TYPE_CHECKING:
    from lt_tensor.activations_utils import ACTIV_NAMES_TP
T = TypeVar("T")


POSSIBLE_OUTPUT_TYPES: TypeAlias = Union[
    Tensor,
    Tuple[Tensor, ...],
    Dict[str, Union[Tuple[Tensor, ...], Tensor, Any]],
]


def get_init_fn(
    norm_type: Literal[
        "normal",
        "xavier",
        "kaiming",
        "orthogonal",
        "sparse",
        "ones",
        "zeros",
        "constant",
        "trunc_normal",
        "uniform",
    ] = "normal",
    **kwargs,
):
    match norm_type:
        case "normal":
            fn = lambda x: nn.init.normal_(
                x, mean=kwargs.get("mean", 0.0), std=kwargs.get("std", 1.0)
            )
        case "uniform":
            fn = lambda x: nn.init.uniform_(
                x, a=kwargs.get("a", 0.0), b=kwargs.get("b", 1.0)
            )
        case "kaiming":  # _:
            fn = lambda x: nn.init.kaiming_normal_(
                x,
                a=kwargs.get("a", 0.01),
                mode=kwargs.get("mode", "fan_in"),
                nonlinearity=kwargs.get("nonlinearity", "leaky_relu"),
            )
        case "xavier":
            fn = lambda x: nn.init.xavier_normal_(x, gain=kwargs.get("gain", 1.0))
        case "orthogonal":
            fn = lambda x: nn.init.orthogonal_(x, gain=kwargs.get("gain", 1.0))
        case "zeros":
            fn = lambda x: nn.init.zeros_(x)
        case "ones":
            fn = lambda x: nn.init.ones_(x)
        case "constant":
            fn = lambda x: nn.init.constant_(x, val=kwargs.get("val", 0.25))
        case "trunc_normal":
            fn = lambda x: nn.init.trunc_normal_(
                x,
                mean=kwargs.get("mean", 0.0),
                std=kwargs.get("std", 1.0),
                a=kwargs.get("a", -2.0),
                b=kwargs.get("b", 2.0),
            )
        case "sparse":
            fn = lambda x: nn.init.sparse_(
                x, sparsity=kwargs.get("sparse_", 0.1), std=kwargs.get("", 0.01)
            )
        case _:
            raise ValueError(f"Not implemented '{norm_type}' yet!")
    return fn


class ModelConfig(ABC, OrderedDict):
    _forbidden_list: List[str] = ["_forbidden_list"]

    def __init__(
        self,
        **settings,
    ):
        self.update(**settings)

    @staticmethod
    def get_activation(
        activation: "ACTIV_NAMES_TP",
        as_callable: bool = False,
        verbose: bool = False,
        **kwargs,
    ):
        from lt_tensor.activations_utils import get_activation

        return get_activation(
            activation=activation,
            __return_callable=as_callable,
            __verbose_warns=verbose,
            **kwargs,
        )

    def reset_settings(self):
        raise NotImplementedError("Not implemented")

    def post_process(self):
        """Implement the post process, to do a final check to the input data"""
        pass

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        super().__setattr__(key, value)

    def save_config(
        self,
        path: str,
    ):
        assert Path(path).name.endswith(
            (".json", ".yaml", ".yml")
        ), "No valid extension was found in '{path}', It must end with either '.json' or '.yaml' or '.yml'."
        if Path(path).name.endswith(".json"):
            base = {
                k: v
                for k, v in self.state_dict().items()
                if isinstance(v, (str, int, float, list, tuple, dict, set, bytes))
            }

            save_json(Path(path), base, indent=4)
        else:
            save_yaml(Path(path), self.state_dict())

    def set_value(self, var_name: str, value: str) -> None:
        assert var_name not in self._forbidden_list
        updateDict(self, {var_name: value})
        self.update({var_name: value})

    def get_value(self, var_name: str) -> Any:
        return self.__dict__.get(var_name)

    def load_state_dict(self, new_state: dict[str, str]):
        new_state = {
            k: y for k, y in new_state.items() if k not in self._forbidden_list
        }
        updateDict(self, new_state)
        self.update(**new_state)
        self.post_process()

    def state_dict(self):
        return {k: y for k, y in self.__dict__.items() if k not in self._forbidden_list}

    @classmethod
    def from_dict(cls, dictionary: Dict[str, Any]):
        assert is_dict(dictionary, False)
        return cls(**dictionary)

    @classmethod
    def from_path(cls, path: PathLike, encoding: Optional[str] = None):
        assert is_file(
            path, extensions=[".json", ".yaml", ".yml"]
        ), "path must point to a valid file!"
        if Path(path).name.endswith(".json"):
            settings = load_json(path, {}, encoding=encoding, errors="ignore")
        else:
            settings = load_yaml(path, {})
        return cls(**settings)


def _in_exclude_list(item: str, exclusion_list: List[str]):
    if exclusion_list:
        for exc in exclusion_list:
            if exc.lower() in item.lower():
                return True
    return False


def get_weights(
    directory_or_weights: Union[str, PathLike, Mapping],
    weights_only: bool = False,
    map_location: Union[torch.device, str] = torch.device("cpu"),
):
    if isinstance(directory_or_weights, (dict, Mapping)):
        return directory_or_weights
    if isinstance(map_location, str):
        map_location = torch.device(map_location)

    is_path_valid(
        directory_or_weights, validate=True
    )  # raises validation if its invalid path

    directory_or_weights = Path(directory_or_weights)

    if is_file(directory_or_weights):
        return torch.load(
            str(directory_or_weights),
            map_location=map_location,
            weights_only=weights_only,
        )

    for file in sorted(find_files(directory_or_weights, ["*.pt", "*.ckpt", "*.pth"])):
        try:
            return torch.load(
                file, map_location=map_location, weights_only=weights_only
            )
        except:
            pass
    raise ValueError("No weight has been found!")


def get_config(
    cfg_dir_or_data: Union[str, PathLike, ModelConfig, dict],
    default: Optional[Any] = None,
) -> Union[Dict[str, object], ModelConfig, Any]:
    # raises validation if its invalid path only when default is None otherwise it returns the defaults.
    if isinstance(cfg_dir_or_data, (ModelConfig, dict)):
        return cfg_dir_or_data
    if not is_path_valid(cfg_dir_or_data, validate=default is None):
        return default
    cfg_dir_or_data = Path(cfg_dir_or_data)
    if is_file(cfg_dir_or_data):
        assert cfg_dir_or_data.name.endswith(
            (".json", ".yaml", ".yml")
        ), "Invalid file provided"
        if cfg_dir_or_data.name.endswith(".json"):
            return load_json(cfg_dir_or_data, default)
        return load_yaml(cfg_dir_or_data, default)

    res = find_files(
        cfg_dir_or_data,
        [
            "config*.json",
            "*config.json",
            "config*.yml",
            "*config.yml",
            "*config.yaml",
            "config*.yaml",
        ],
        maximum=1,
    )
    assert res, f"No config file has been found in '{cfg_dir_or_data}'"

    if Path(res[0]).name.endswith(".json"):
        return load_json(res[0], default)
    return load_yaml(res[0], default)


class _Devices_Base(nn.Module):
    _device: torch.device = DEFAULT_DEVICE
    _setting_device: bool = False
    _autocast: bool = False
    _autocast_dtype: torch.dtype = torch.float16

    @property
    def autocast_dtype(self):
        return self._autocast_dtype

    @autocast_dtype.setter
    def autocast_dtype(self, value: torch.dtype):
        self._autocast_dtype = value

    @property
    def autocast(self):
        return self._autocast

    @autocast.setter
    def autocast(self, value: bool):
        self._autocast = value

    @property
    def device(self):
        return self._device

    def set_autocast(self, enabled: bool, dtype: Optional[torch.dtype] = None):
        self.autocast = enabled
        if dtype is not None:
            self.autocast_dtype = dtype
        return {"is_enabled": self.autocast, "d_type": self.autocast_dtype}

    @device.setter
    def device(self, device: Union[torch.device, str]):
        assert isinstance(device, (str, torch.device))
        self._device = torch.device(device) if isinstance(device, str) else device

    @torch.autocast(device_type=_device.type, dtype=_autocast_dtype, enabled=_autocast)
    def __call__(self, *args, **kwds) -> Union[Tensor, Any]:
        with torch.autocast(
            device_type=self._device.type,
            dtype=self._autocast_dtype,
            enabled=self.autocast,
        ):
            return super().__call__(*args, **kwds)

    def freeze_all(self, exclude: list[str] = []):
        for name, module in self.named_parameters():
            if _in_exclude_list(name, exclude):
                continue
            try:
                self.freeze_module(module)
            except:
                pass

    def unfreeze_all(self, exclude: list[str] = []):
        for name, module in self.named_parameters():
            if _in_exclude_list(name, exclude):
                continue
            try:
                self.unfreeze_module(module)
            except:
                pass

    @staticmethod
    def set_seed(seed: Optional[Number] = None):
        if seed is not None:
            set_seed(seed)

    @staticmethod
    def clear_cache():
        clear_cache()

    def freeze_module(
        self, module_or_name: Union[str, nn.Module, nn.Parameter, "Model", Tensor]
    ):
        self._change_gradient_state(module_or_name, False)

    def unfreeze_module(
        self, module_or_name: Union[str, nn.Module, nn.Parameter, "Model", Tensor]
    ):
        self._change_gradient_state(module_or_name, True)

    def _change_gradient_state(
        self,
        module_or_name: Union[str, nn.Module, nn.Parameter, "Model", Tensor],
        new_state: bool,  # True = unfreeze
    ):
        assert isinstance(
            module_or_name, (str, nn.Module, nn.Parameter, Model, Tensor)
        ), f"Item '{module_or_name}' is not a valid module, parameter, tensor or a string."
        if isinstance(module_or_name, (nn.Module, nn.Parameter, Model, Tensor)):
            target = module_or_name
        else:
            target = getattr(self, module_or_name)

        if isinstance(target, Tensor):
            target.requires_grad = new_state
        elif isinstance(target, nn.Parameter):
            target.requires_grad = new_state
        elif isinstance(target, Model):
            target.freeze_all()
        elif isinstance(target, nn.Module):
            for param in target.parameters():
                if hasattr(param, "requires_grad"):
                    param.requires_grad = new_state
        else:
            raise ValueError(
                f"Item '{module_or_name}' is not a valid module, parameter or tensor."
            )

    def apply_device(self):
        """Helps to apply devices towards all the internal components"""
        if self._setting_device:
            return

        self._setting_device = True

        try:
            for modules in self.modules():
                try:
                    modules.to(self.device)
                except:
                    pass

            for buffer in self.buffers():
                try:
                    buffer.to(self.device)
                except:
                    pass

            for tensor in self.parameters():
                try:
                    tensor.to(self.device)
                except:
                    pass
        except:
            pass
        finally:
            self._setting_device = False

    def _to_dvc(
        self, device_name: str, device_id: Optional[Union[int, torch.device]] = None
    ):
        device = device_name
        if device_id is not None:
            if isinstance(device_id, Number):
                device += ":" + str(int(device_id))
            elif hasattr(device_id, "index"):
                device += ":" + str(device_id.index)
        self.device = device
        if not self._setting_device:
            self.apply_device()

    def _to(self, *args, **kwargs):
        self.to(*args, _internal=True, **kwargs)

    @overload
    def to(
        self,
        device: Optional[Union[torch.device, str]] = ...,
        dtype: Optional[torch.dtype] = ...,
        non_blocking: bool = ...,
    ) -> Self: ...

    @overload
    def to(self, tensor: Tensor, non_blocking: bool = ...) -> Self: ...

    @override
    def to(self, *args, **kwargs) -> Self:
        self._to_dvc(torch._C._nn._parse_to(*args, **kwargs)[0].type)
        return super().to(*args, **kwargs)

    @override
    def ipu(self, device: Optional[Union[int, torch.device]] = None) -> T:
        super().ipu(device)
        self._to_dvc("ipu", device)
        return self

    @override
    def xpu(self, device: Optional[Union[int, torch.device]] = None) -> T:
        super().xpu(device)
        self._to_dvc("xpu", device)
        return self

    @override
    def cuda(self, device: Optional[Union[int, torch.device]] = None) -> T:
        super().cuda(device)
        self._to_dvc("cuda", device)
        return self

    @override
    def mtia(self, device: Optional[Union[int, torch.device]] = None) -> T:
        super().mtia(device)
        self._to_dvc("mtia", device)
        return self

    @override
    def cpu(self) -> T:
        super().cpu()
        self._to_dvc("cpu", None)
        return self

    def init_weights(
        self,
        base_norm_type: Optional[
            Union[
                Callable[[nn.Parameter], None],
                Literal[
                    "xavier",
                    "kaiming",
                    "orthogonal",
                    "sparse",
                    "ones",
                    "zeros",
                    "constant",
                    "normal",
                    "trunc_normal",
                    "uniform",
                ],
            ]
        ] = None,
        small_norm_type: Optional[
            Union[
                Callable[[nn.Parameter], None],
                Literal[
                    "xavier",
                    "kaiming",
                    "orthogonal",
                    "sparse",
                    "ones",
                    "zeros",
                    "constant",
                    "normal",
                    "trunc_normal",
                    "uniform",
                ],
            ]
        ] = None,
        small_norm_kwargs: Dict[str, Any] = {},
        base_norm_kwargs: Dict[str, Any] = {},
        selection_mode: Union[Literal["all", "selected", "non_selected"]] = "all",
        selected_modules: List[str] = [],
    ):
        """
        Example:

        ```python
        small_norm_kwargs: Dict[str, Any] = {
            "mean": 0.0,
            "std": 0.2,
        }
        base_norm_kwargs: Dict[str, Any] = {
            "a": 0.01,
            "mode": "fan_in",
            "nonlinearity": "leaky_relu",
        }
        model.init_weights(
            base_norm_type="kaiming",
            small_norm_type="normal",
            small_norm_kwargs=small_norm_kwargs,
            base_norm_kwargs=base_norm_kwargs,
        )

        """
        if base_norm_type is None and small_norm_type is None:
            return

        selection_disabled = (
            selection_mode not in ["selected", "non_selected"]
        ) or not selected_modules

        def _check_name(name: str):
            if selection_disabled:
                return True
            present = any([x in name for x in selected_modules])
            if selection_mode == "selected":
                return present
            return not present

        base_enabled = base_norm_type is not None
        if base_enabled:
            if isinstance(base_norm_type, str):
                b_fn = get_init_fn(base_norm_type)
            else:
                b_fn = lambda x: base_norm_type(x, **base_norm_kwargs)

        small_enabled = small_norm_type is not None
        if small_enabled:
            if isinstance(small_norm_type, str):
                s_fn = get_init_fn(small_norm_type)
            else:
                s_fn = lambda x: small_norm_type(x, **small_norm_kwargs)

        for name, param in self.named_parameters():
            if not _check_name(name):
                continue
            # smaller models (parameter of single dim like biasses for example)
            if param.data.ndim < 2:
                if small_enabled:
                    s_fn(param)
            else:
                if base_enabled:
                    b_fn(param)

    def __init__(
        self,
        seed: Optional[Number] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.set_seed(seed)


class Model(_Devices_Base, ABC):
    """
    This makes it easier to assign a device and retrieves it later
    """

    # dont save list:
    _dont_save_items: List[str] = []

    def trainable_parameters(self, module_name: Optional[str] = None):
        """Gets the number of trainable parameters from either the entire model or from a specific module."""
        if module_name is not None:
            assert hasattr(self, module_name), f"Module '{module_name}' not found."
            module = getattr(self, module_name)
            return sum(
                [
                    x.numel()
                    for x in module.parameters()
                    if hasattr(x, "requires_grad") and x.requires_grad
                ]
            )
        return sum(
            [
                x.numel()
                for x in self.parameters()
                if hasattr(x, "requires_grad") and x.requires_grad
            ]
        )

    def non_trainable_parameters(self, module_name: Optional[str] = None):
        """Gets the number of non-trainable parameters from either the entire model or from a specific module."""
        if module_name is not None:
            assert hasattr(self, module_name), f"Module '{module_name}' not found."
            module = getattr(self, module_name)
            return sum(
                [
                    x.numel()
                    for x in module.parameters()
                    if not hasattr(x, "requires_grad") or not x.requires_grad
                ]
            )
        return sum(
            [
                x.numel()
                for x in self.parameters()
                if not hasattr(x, "requires_grad") or not x.requires_grad
            ]
        )

    def extract_weights(self, module_name: Optional[str] = None) -> List[Tensor]:
        """Returns the weights of the model entry model or from a specified module"""
        if module_name is not None:
            assert hasattr(self, module_name), f"Module '{module_name}' not found."
            module = getattr(self, module_name)
            params = []
            if isinstance(module, nn.Module):
                return [x.data.detach() for x in module.parameters()]
            elif isinstance(module, (Tensor, nn.Parameter)):
                return [module.data.detach()]
            raise (f"{module_name} is has no weights")
        return [x.data.detach() for x in self.parameters()]

    def format_trainable_parameters(self, module_name: Optional[str] = None) -> str:
        params = format(self.trainable_parameters(module_name), ",").replace(",", ".")
        return params

    def format_non_trainable_parameters(self, module_name: Optional[str] = None) -> str:
        params = format(self.non_trainable_parameters(module_name), ",").replace(
            ",", "."
        )
        return params

    def print_trainable_parameters(self, module_name: Optional[str] = None) -> str:
        fmt = self.format_trainable_parameters(module_name)
        if module_name is not None:
            print(f"Trainable parameter(s) for module '{module_name}': {fmt}")
        else:
            print(f"Trainable parameter(s): {fmt}")

    def print_non_trainable_parameters(self, module_name: Optional[str] = None) -> str:
        fmt = self.format_non_trainable_parameters(module_name)
        if module_name is not None:
            print(f"Non-Trainable parameter(s) for module '{module_name}': {fmt}")
        else:
            print(f"Non-Trainable parameter(s): {fmt}")

    @classmethod
    def from_pretrained(
        cls,
        model_path_or_weight_data: Union[str, PathLike, Mapping],
        config: Optional[Union[str, PathLike]] = None,
        config_defaults: Dict[str, Any] = {},
        assign=False,
        strict=False,
    ):
        """TODO: Finish this implementation or leave it as an optional function."""
        assert isinstance(
            model_path_or_weight_data, (dict, Mapping, str, PathLike, bytes)
        ), (
            f"Invalid 'model_path_or_weight_data'. It must be either a path pointing to a checkpoint or a dictionary containing the loaded keys."
            " Received instead: ({model_path_or_weight_data}) type: {type(model_path_or_weight_data)}"
        )
        state_dict = get_weights(model_path_or_weight_data)
        if config is not None:
            config_data = get_config(config, config_defaults)

        if config is None:
            model = cls()
        else:
            try:
                if isinstance(config_data, ModelConfig):
                    model = cls(config_data)
                else:
                    model = cls(**config_data)
            except:
                model = cls(config_data)

        try:
            model.load_state_dict(state_dict, assign=assign, strict=strict)
        except Exception as e:
            if hasattr(model, "remove_norms"):
                model.remove_norms()
                model.load_state_dict(state_dict, assign=assign, strict=strict)
            else:
                raise e

        return model

    @override
    def state_dict(
        self,
        *args,
        ignore_keys: List[str] = [],
        destination: Optional[OrderedDict] = None,
        prefix: str = "",
        keep_vars: bool = False,
        move_to_cpu: bool = False,
    ):
        if destination is None:
            destination = OrderedDict()
            destination._metadata = OrderedDict()

        old_device = self.device
        if move_to_cpu and self.device.type != DEFAULT_DEVICE.type:
            self.to(DEFAULT_DEVICE)

        local_metadata = dict(version=self._version)
        if hasattr(destination, "_metadata"):
            destination._metadata[prefix[:-1]] = local_metadata

        for hook in self._state_dict_pre_hooks.values():
            hook(self, prefix, keep_vars)
        self._save_to_state_dict(destination, prefix, keep_vars)

        ignore_keys.extend(self._dont_save_items)
        _needs_to_check = bool(ignore_keys)

        def _check_by_name(name: str):
            if not _needs_to_check:
                return True
            for k in ignore_keys:
                if k in name:
                    return False
            return True

        for name, module in self._modules.items():
            if not _check_by_name(name):
                continue
            if module is not None:
                module.state_dict(
                    destination=destination,
                    prefix=prefix + name + ".",
                    keep_vars=keep_vars,
                )

        for hook in self._state_dict_hooks.values():
            hook_result = hook(self, destination, prefix, local_metadata)
            if not getattr(hook, "_from_public_api", False):
                if hook_result is not None:
                    destination = hook_result
            else:
                if hook_result is not None:
                    raise RuntimeError("state_dict post-hook must return None")
        if move_to_cpu and self.device.type != old_device.type:
            self.to(old_device)
        return destination

    def save_weights(
        self,
        path: Union[Path, str],
        replace: bool = False,
        ignore_keys: List[str] = [],
        move_to_cpu: bool = True,
    ):
        is_pathlike(path, False, validate=True)
        path = Path(path)
        model_dir = path

        if path.exists():
            if path.is_dir():
                model_dir = Path(path, f"model_{get_current_time()}.pt")
            elif path.is_file():
                if replace:
                    path.unlink()
                else:
                    model_dir = Path(path.parent, f"model_{get_current_time()}.pt")
        else:
            if not "." in str(path):
                model_dir = Path(path, f"model_{get_current_time()}.pt")
        path.parent.mkdir(exist_ok=True, parents=True)
        state_dict = self.state_dict(move_to_cpu=move_to_cpu, ignore_keys=ignore_keys)
        state_dict.pop("_setting_device", None)
        torch.save(obj=state_dict, f=str(model_dir))

    def load_weights(
        self,
        path_or_state_dict: Union[Path, str, Dict],
        raise_if_not_exists: bool = False,
        from_key: Optional[str] = None,
        *,
        strict: bool = False,
        assign: bool = False,
        weights_only: bool = False,
        mmap: Optional[bool] = None,
        **pickle_load_args,
    ):
        if not isinstance(path_or_state_dict, dict):
            is_pathlike(path_or_state_dict, False, validate=True)
            path_or_state_dict = Path(path_or_state_dict)
            if not path_or_state_dict.exists():
                assert (
                    not raise_if_not_exists
                ), f"Path '{path_or_state_dict}' does not exists."
                return None

            if path_or_state_dict.is_dir():
                possible_files = list(Path(path_or_state_dict).rglob("*.pt"))
                assert (
                    possible_files or not raise_if_not_exists
                ), f"No model could be found in the path '{path_or_state_dict}'."
                if not possible_files:
                    return None
                path_or_state_dict = possible_files[-1]
            state_dict = torch.load(
                str(path_or_state_dict),
                weights_only=weights_only,
                mmap=mmap,
                **pickle_load_args,
            )
        else:
            state_dict = path_or_state_dict.copy()
        if from_key is not None:
            if from_key in state_dict:
                state_dict = state_dict[from_key]
        incompatible_keys = self.load_state_dict(
            state_dict,
            strict=strict,
            assign=assign,
        )
        return incompatible_keys

    @torch.no_grad()
    def inference(self, *args, **kwargs):
        if self.training:
            self.eval()
        return self(*args, **kwargs)

    def train_step(
        self,
        *inputs,
        **kwargs,
    ):
        """Train Step"""
        if not self.training:
            self.train()
        return self(*inputs, **kwargs)

    def _move_to_self_device(self, *args, **kwargs):
        from lt_tensor.misc_utils import all_to_device

        return all_to_device(self.device, *args, **kwargs)

    def forward(self, x: Tensor, *args, **kwargs) -> Union[Tensor, Any]:
        raise NotImplementedError(
            f"No forward method has been implement for '{self.__class__.__name__}'"
        )

    def reset_parameters(self, *args, **kwargs) -> None:
        raise NotImplementedError()


class ModelLoRA(Model, ABC):
    adapters: Union[nn.Identity, nn.Module] = nn.Sequential(nn.Identity())
    adapters_modules: List[str] = ["adapters"]

    def save_lora(
        self,
        path: Union[Path, str],
        replace: bool = False,
    ):
        is_pathlike(path, False, validate=True)
        path = Path(path)
        model_dir = path
        if path.exists():
            if path.is_dir():
                model_dir = Path(path, f"adapter_{get_current_time()}.pt")
            elif path.is_file():
                if replace:
                    path.unlink()
                else:
                    model_dir = Path(path.parent, f"adapter_{get_current_time()}.pt")
        else:
            if not "." in path.name:
                model_dir = Path(path, f"adapter_{get_current_time()}.pt")
        state_dict = self.adapters.state_dict()
        torch.save(obj=state_dict, f=str(model_dir))

    def load_lora(
        self,
        path: Union[Path, str],
        raise_if_not_exists: bool = False,
        strict: bool = False,
        assign: bool = False,
        weights_only: bool = True,
        mmap: Optional[bool] = None,
        **pickle_load_args,
    ):
        is_pathlike(path, False, validate=True)
        path = Path(path)
        if not path.exists():
            assert raise_if_not_exists, f"Path {path} could not been found!"
            return None
        if path.is_dir():
            adapter = find_files(path, ["*adapter*.pt", "*lora*.pt", "*rank*.pt"])
            if not adapter:
                assert (
                    raise_if_not_exists
                ), f"No lora could be located at the path: '{path}'"
                return None
            adapter = adapter[0]
        else:
            adapter = str(path)
        state = torch.load(
            adapter, weights_only=weights_only, mmap=mmap, **pickle_load_args
        )
        return self.adapters.load_state_dict(state, strict=strict, assign=assign)

    def lora_step(self, *arg, **kwargs):
        raise NotImplementedError("Not implemented for this model")

    def freeze_all_but_lora(self):
        self.freeze_all()
        for adapter in self.adapters_modules:
            self.unfreeze_module(adapter)

    def unfreeze_all_but_lora(self):
        self.unfreeze_all()
        for adapter in self.adapters_modules:
            self.freeze_module(adapter)
