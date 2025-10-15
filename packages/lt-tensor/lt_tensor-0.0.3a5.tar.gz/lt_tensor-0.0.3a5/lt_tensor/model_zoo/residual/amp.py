__all__ = [
    "AMPBlock",
]
from torch import nn, Tensor
from lt_utils.common import *
from lt_utils.misc_utils import filter_kwargs
from lt_tensor.model_zoo.convs import ConvBase
from lt_tensor.model_zoo.activations import alias_free


class AMPBlock(ConvBase):
    """Modified from 'https://github.com/NVIDIA/BigVGAN/blob/main/bigvgan.py' under MIT license, found in 'bigvgan/LICENSE'

    AMPBlock applies Snake / SnakeBeta activation functions with trainable parameters that control periodicity, defined for each layer.

    """

    def __init__(
        self,
        channels: int,
        kernel_size: int = 3,
        dilation: tuple = (1, 3, 5),
        activation: Optional[Callable[[Tensor], Tensor]] = None,
        version: Literal["v1", "v2"] = "v1",
        groups: int = 1,
        norm: Optional[Literal["weight", "spectral"]] = None,
        alias_up_ratio: int = 2,
        alias_down_ratio: int = 2,
        alias_up_kernel_size: int = 12,
        alias_down_kernel_size: int = 12,
        snake_alpha: float = 1.0,
        snake_logscale: bool = True,
        **kwargs,
    ):
        super().__init__()

        self.resblock_version = version
        if activation is None:
            from lt_tensor.model_zoo.activations import snake

            activation = lambda: snake.SnakeBeta(
                channels,
                alpha_logscale=snake_logscale,
                alpha=snake_alpha,
                requires_grad=True,
            )

        ch1_kwargs = dict(in_channels=channels, kernel_size=kernel_size, norm=norm)
        ch2_kwargs = dict(
            in_channels=channels,
            kernel_size=kernel_size,
            padding=self.get_padding(kernel_size, 1),
            norm=norm,
        )
        alias_kwargs = dict(
            up_ratio=alias_up_ratio,
            down_ratio=alias_down_ratio,
            up_kernel_size=alias_up_kernel_size,
            down_kernel_size=alias_down_kernel_size,
        )
        self.convs = nn.ModuleList()
        for i, d in enumerate(dilation):
            if version == "v1":
                self.convs.append(
                    nn.Sequential(
                        alias_free.Activation1d(
                            activation=activation(), **alias_kwargs
                        ),
                        self.get_1d_conv(
                            **ch1_kwargs,
                            dilation=d,
                            padding=self.get_padding(kernel_size, d),
                            groups=groups,
                        ),
                        alias_free.Activation1d(
                            activation=activation(), **alias_kwargs
                        ),
                        self.get_1d_conv(**ch2_kwargs, groups=groups),
                    )
                )
            else:
                self.convs.append(
                    nn.Sequential(
                        alias_free.Activation1d(
                            activation=activation(), **alias_kwargs
                        ),
                        self.get_1d_conv(
                            **ch1_kwargs,
                            dilation=d,
                            padding=self.get_padding(kernel_size, d),
                            groups=groups,
                        ),
                    ),
                )

        self.num_layers = len(self.convs)

    def init_weights(
        self,
        mean: float = 0,
        std: float = 0.01,
        zero_bias: bool = False,
    ):
        for i, module in enumerate(self.convs1):
            if i == 0:
                nn.init.normal_(module.weight, mean=mean, std=std)
                if zero_bias and module.bias is not None:
                    nn.init.zeros_(module.bias)
            else:
                nn.init.normal_(module[-1].weight, mean=mean, std=std)
                if zero_bias and module[-1].bias is not None:
                    nn.init.zeros_(module[-1].bias)

    def forward(self, x):
        for layer in self.convs:
            x = layer(x) + x
        return x
