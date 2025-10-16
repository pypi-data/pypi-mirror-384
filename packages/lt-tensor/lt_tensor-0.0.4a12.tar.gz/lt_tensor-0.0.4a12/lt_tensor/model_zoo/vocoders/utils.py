from lt_utils.common import *
from lt_tensor.model_base import ModelConfig
from lt_tensor.model_zoo.residual import (
    ResBlock,
    AMPBlock,
    GatedResBlock,
)


def get_snake(name: Literal["snake", "snakebeta"] = "snake"):
    assert name.lower() in [
        "snake",
        "snakebeta",
    ], f"'{name}' is not a valid snake activation! use 'snake' or 'snakebeta'"
    from lt_tensor.model_zoo.activations import snake

    if name.lower() == "snake":
        return snake.Snake
    return snake.SnakeBeta


class VocoderConfig(ModelConfig):
    in_channels: int = 80
    activation: str = "leakyrelu"
    resblock_activation: str = "leakyrelu"

    # resblock stuff:
    alpha_logscale: bool = True
    residual_scale: float = 1.0
    resblock_version: Literal["v1", "v2"] = "v1"

    def _get_resblock_activation(self, **kwargs):
        if "snake" in self.resblock_activation:
            if "alpha_logscale" not in kwargs:
                kwargs["alpha_logscale"] = self.alpha_logscale
            if "snake_alpha" not in kwargs:
                kwargs["snake_alpha"] = self.snake_alpha
        elif "aliasfree" in self.resblock_activation:
            if "up_ratio" not in kwargs:
                kwargs["up_ratio"] = self.aliasfree_up_ratio
            if "down_ratio" not in kwargs:
                kwargs["down_ratio"] = self.aliasfree_down_ratio
            if "up_kernel_size" not in kwargs:
                kwargs["up_kernel_size"] = self.aliasfree_up_kernel_size
            if "down_kernel_size" not in kwargs:
                kwargs["down_kernel_size"] = self.aliasfree_down_kernel_size
            return lambda: get_snake(self.snake_activ_choice)(
                kwargs.get("channels"),
                alpha=self.snake_alpha,
                alpha_logscale=self.alpha_logscale,
            )
        return self.get_activation(self.resblock_activation, as_callable=True, **kwargs)

    def retrieve_resblock(
        self,
        channels: int,
        dilation: Tuple[int, ...],
        kernel_size: int,
        activation_kwargs: Dict[str, Any] = {},
        groups: int = 1,
    ) -> Union[ResBlock, AMPBlock, GatedResBlock]:
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
                    init_weights=self.init_weights_residual,
                )
            case "ampblock":
                return AMPBlock(
                    channels=channels,
                    kernel_size=kernel_size,
                    dilation=dilation,
                    activation=self._get_resblock_activation(**activation_kwargs),
                    groups=groups,
                    version=self.resblock_version,
                    norm=self.norm_residual,
                    init_weights=self.init_weights_residual,
                )
            case _:
                return GatedResBlock(
                    channels=channels,
                    kernel_size=kernel_size,
                    dilations=dilation,
                    activation=self._get_resblock_activation(**activation_kwargs),
                    mode=self.residual_mode,
                    norm=self.norm_residual,
                    groups=groups,
                    alpha=self.gated_alpha,
                    alpha_train=self.gated_train_alpha,
                    conditional=False,
                    stochastic_dropout=self.gated_stochastic_dropout,
                    init_weights=self.init_weights_residual,
                )
