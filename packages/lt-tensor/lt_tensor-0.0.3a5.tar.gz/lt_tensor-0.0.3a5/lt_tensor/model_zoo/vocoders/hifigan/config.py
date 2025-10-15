__all__ = ["HifiganGenerator", "HifiganConfig"]


from lt_utils.common import *
from lt_tensor.model_base import ModelConfig
from lt_tensor.model_zoo.residual import ResBlock, AMPBlock
from lt_tensor.activations_utils import ACTIV_NAMES_TP


def get_snake(name: Literal["snake", "snakebeta"] = "snake"):
    assert name.lower() in [
        "snake",
        "snakebeta",
    ], f"'{name}' is not a valid snake activation! use 'snake' or 'snakebeta'"
    from lt_tensor.model_zoo.activations import snake

    if name.lower() == "snake":
        return snake.Snake
    return snake.SnakeBeta


class HifiganConfig(ModelConfig):
    in_channels: int = 80
    upsample_rates: List[Union[int, List[int]]] = [8, 8, 2, 2]
    upsample_kernel_sizes: List[Union[int, List[int]]] = [16, 16, 4, 4]
    upsample_initial_channel: int = 768
    resblock_kernel_sizes: List[Union[int, List[int]]] = [3, 7, 11]
    resblock_dilation_sizes: List[Union[int, List[int]]] = [
        [1, 3, 5],
        [1, 3, 5],
        [1, 3, 5],
    ]
    final_gate: Optional[Literal["tanh", "norm", "clamp"]] = "tanh"
    use_bias_on_final_layer: bool = True

    activation: ACTIV_NAMES_TP = "leakyrelu"
    last_activation: ACTIV_NAMES_TP = "leakyrelu"
    resblock_activation: ACTIV_NAMES_TP = "leakyrelu"

    activation_kwargs: Dict[str, Any] = dict()
    residual_activation_kwargs: Dict[str, Any] = dict()

    resblock_version: Literal["v1", "v2"] = "v1"
    residual_groups: Union[int, List[Union[int, Tuple[int, int]]]] = 1
    resblock_name: Literal["resblock", "ampblock"] = "resblock"
    alpha_logscale: bool = False
    snake_alpha: float = 1.0
    groups: Union[int, List[int]] = 1

    norm: Optional[Literal["weight", "spectral"]] = "weight"
    norm_residual: Optional[Literal["weight", "spectral"]] = "weight"

    def __init__(
        self,
        in_channels: int = 80,
        upsample_rates: List[Union[int, List[int]]] = [8, 8, 2, 2],
        upsample_kernel_sizes: List[Union[int, List[int]]] = [16, 16, 4, 4],
        upsample_initial_channel: int = 512,
        resblock_kernel_sizes: List[Union[int, List[int]]] = [3, 7, 11],
        resblock_dilation_sizes: List[Union[int, List[int]]] = [
            [1, 3, 5],
            [1, 3, 5],
            [1, 3, 5],
        ],
        *,
        activation: ACTIV_NAMES_TP = "leakyrelu",
        last_activation: ACTIV_NAMES_TP = "leakyrelu",
        resblock_activation: ACTIV_NAMES_TP = "leakyrelu",
        activation_kwargs: Dict[str, Any] = dict(negative_slope=0.1),
        resblock_activation_kwargs: Dict[str, Any] = dict(negative_slope=0.1),
        final_layer_task: bool = False,
        use_tanh: bool = True,
        groups: Union[int, List[int]] = 1,
        final_gate: Optional[Literal["tanh", "norm", "clamp"]] = "tanh",
        resblock_name: Literal["resblock", "ampblock"] = "resblock",
        resblock_version: Literal["v1", "v2"] = "v1",
        residual_groups: Union[int, List[int]] = 1,
        alpha_logscale: bool = False,
        snake_alpha: float = 1.0,
        norm: Optional[Literal["weight", "spectral"]] = "weight",
        norm_residual: Optional[Literal["weight", "spectral"]] = "weight",
        **kwargs,
    ):
        settings = {
            "in_channels": kwargs.get("n_mels", in_channels),
            "upsample_rates": upsample_rates,
            "upsample_kernel_sizes": upsample_kernel_sizes,
            "upsample_initial_channel": upsample_initial_channel,
            "resblock_kernel_sizes": resblock_kernel_sizes,
            "resblock_dilation_sizes": resblock_dilation_sizes,
            "activation": activation,
            "resblock_activation": resblock_activation,
            "resblock_activation_kwargs": resblock_activation_kwargs,
            "activation_kwargs": activation_kwargs,
            "use_tanh": use_tanh,
            "use_bias_on_final_layer": final_layer_task,
            "do_norm": final_gate,
            "residual_groups": residual_groups,
            "alpha_logscale": alpha_logscale,
            "snake_alpha": snake_alpha,
            "resblock_name": resblock_name,
            "resblock_version": resblock_version,
            "groups": groups,
            "norm": norm,
            "norm_residual": norm_residual,
            "last_activation": last_activation,
        }
        super().__init__(**settings)
        self._forbidden_list.append("_resblock_cal")

    def _get_resblock_activation(self, **kwargs):
        if "snake" in self.resblock_activation:
            if "alpha_logscale" not in kwargs:
                kwargs["alpha_logscale"] = self.alpha_logscale
            if "snake_alpha" not in kwargs:
                kwargs["snake_alpha"] = self.snake_alpha

        return self.get_activation(self.resblock_activation, as_callable=True, **kwargs)

    def retrieve_resblock(
        self,
        channels: int,
        dilation: Tuple[int, ...],
        kernel_size: int,
        activation_kwargs: Dict[str, Any] = {},
        groups: int = 1,
    ) -> Union[ResBlock, AMPBlock]:
        match self.resblock_name:
            case "resblock":
                return ResBlock(
                    channels=channels,
                    kernel_size=kernel_size,
                    dilation=dilation,
                    activation=self._get_resblock_activation(**activation_kwargs),
                    groups=groups,
                    version=self.resblock_version,
                    norm=self.norm_residual,
                )
            case _:
                return AMPBlock(
                    channels=channels,
                    kernel_size=kernel_size,
                    dilation=dilation,
                    activation=self._get_resblock_activation(**activation_kwargs),
                    groups=groups,
                    version=self.resblock_version,
                    norm=self.norm_residual,
                )

    def post_process(self):
        self.resblock_activation = self.resblock_activation.lower().strip()
        self.activation = self.activation.lower().strip()
        pass

    @staticmethod
    def get_cfg_v1():
        return {
            "upsample_rates": [8, 8, 2, 2],
            "upsample_kernel_sizes": [16, 16, 4, 4],
            "upsample_initial_channel": 512,
            "resblock_kernel_sizes": [3, 7, 11],
            "resblock_dilation_sizes": [[1, 3, 5], [1, 3, 5], [1, 3, 5]],
            "resblock": 0,
            "use_tanh": True,
            "use_bias_on_final_layer": True,
            "norm": "weight",
        }

    @staticmethod
    def get_cfg_v2():
        return {
            "upsample_rates": [8, 8, 2, 2],
            "upsample_kernel_sizes": [16, 16, 4, 4],
            "upsample_initial_channel": 128,
            "resblock_kernel_sizes": [3, 7, 11],
            "resblock_dilation_sizes": [[1, 3, 5], [1, 3, 5], [1, 3, 5]],
            "resblock": 0,
            "use_tanh": True,
            "use_bias_on_final_layer": True,
            "norm": "weight",
        }

    @staticmethod
    def get_cfg_v3():
        return {
            "upsample_rates": [8, 8, 4],
            "upsample_kernel_sizes": [16, 16, 8],
            "upsample_initial_channel": 256,
            "resblock_kernel_sizes": [3, 5, 7],
            "resblock_dilation_sizes": [[1, 2], [2, 6], [3, 12]],
            "resblock": 1,
            "use_tanh": True,
            "use_bias_on_final_layer": True,
            "norm": "weight",
        }
