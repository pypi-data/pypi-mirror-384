__all__ = [
    "ResBlock",
    "ResBlock2d1x1",
    "PoolResBlock2D",
]
from torch import nn, Tensor
from lt_utils.common import *
from lt_utils.misc_utils import filter_kwargs
from lt_tensor.model_zoo.convs import ConvBase


class ResBlock(ConvBase):
    def __init__(
        self,
        channels,
        kernel_size=3,
        dilation=(1, 3, 5),
        activation: Callable[[Any], nn.Module] = lambda: nn.LeakyReLU(0.1),
        groups: int = 1,
        version: Literal["v1", "v2"] = "v1",
        norm: Optional[Literal["weight", "spectral"]] = None,
        **kwargs,
    ):
        super().__init__()
        self.resblock_version = version
        self.convs1 = nn.ModuleList()
        self.convs2 = nn.ModuleList()
        cnn2_padding = self.get_padding(kernel_size, 1)
        for i, d in enumerate(dilation):
            mdk = dict(
                in_channels=channels,
                kernel_size=kernel_size,
                dilation=d,
                padding=self.get_padding(kernel_size, d),
                norm=norm,
                groups=groups,
            )
            if self.resblock_version == "v1":
                self.convs2.append(
                    nn.Sequential(
                        activation(),
                        self.get_1d_conv(
                            channels,
                            kernel_size=kernel_size,
                            dilation=1,
                            padding=cnn2_padding,
                            norm=norm,
                            groups=groups,
                        ),
                    )
                )
            else:
                self.convs2.append(nn.Identity())

            if i == 0:
                self.convs1.append(self.get_1d_conv(**mdk))
            else:
                self.convs1.append(nn.Sequential(activation(), self.get_1d_conv(**mdk)))

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

    def forward(self, x: Tensor):
        for c1, c2 in zip(self.convs1, self.convs2):
            xt = c1(x)
            x = c2(xt) + x
        return x


class ResBlock2d1x1(ConvBase):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        hidden_size: Optional[int] = None,
        dilation: int = 1,
        kernel_size: Union[int, Sequence[int]] = 3,
        pool_kernel_size: Union[int, Sequence[int]] = (1, 2),
        activation: Type[nn.Module] = lambda: nn.LeakyReLU(0.1, inplace=True),
        norm: Optional[Literal["weight", "spectral"]] = None,
        groups: int = 1,
        bias: bool = False,
        c1x1_stride: int = 1,
        c1x1_transposed: bool = False,
        c1x1_dilation: int = 1,
        c1x1_padding: int = 0,
        c1x1_kernel_size: int = 1,
        c1x1_groups: int = 1,
        c1x1_bias: bool = False,
    ):
        super().__init__()
        # BN / LReLU / MaxPool layer before the conv layer - see Figure 1b in the paper
        self.pre_conv = nn.Sequential(
            nn.BatchNorm2d(num_features=in_channels),
            activation(),
            nn.MaxPool2d(kernel_size=pool_kernel_size),
        )
        if not hidden_size:
            hidden_size = (in_channels + out_channels) // 2

        # conv layers

        self.conv = nn.Sequential(
            self.get_2d_conv(
                in_channels=in_channels,
                out_channels=hidden_size,
                kernel_size=kernel_size,
                groups=groups,
                dilation=dilation,
                padding=self.get_padding(kernel_size, dilation, mode="b"),
                bias=bias,
                norm=norm,
            ),
            nn.BatchNorm2d(hidden_size),
            activation(),
            self.get_2d_conv(
                in_channels=hidden_size,
                out_channels=out_channels,
                kernel_size=kernel_size,
                groups=groups,
                padding=self.get_padding(kernel_size, 1, mode="b"),
                bias=bias,
                norm=norm,
            ),
        )

        self.learned_dx = in_channels != out_channels
        if not self.learned_dx:
            self.conv1x1 = nn.Identity()
        else:
            self.conv1x1 = self.get_2d_conv(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=c1x1_kernel_size,
                stride=c1x1_stride,
                dilation=c1x1_dilation,
                groups=c1x1_groups,
                padding=c1x1_padding,
                transposed=c1x1_transposed,
                bias=c1x1_bias,
                norm=norm,
            )

    def forward(self, x: Tensor):
        x = self.pre_conv(x)
        return self.conv(x) + self.conv1x1(x)


class PoolResBlock2D(ConvBase):
    def __init__(
        self,
        pool_features: int = 256,
        pool_activation: nn.Module = nn.LeakyReLU(0.1, inplace=True),
        pool_kernel_size: Union[int, Sequence[int]] = (1, 4),
        resblock_activation: Type[nn.Module] = lambda: nn.LeakyReLU(0.1, inplace=True),
        residual_sizes: List[Tuple[int, int]] = [(64, 128), (128, 192), (192, 256)],
        residual_dilation_sizes: List[Union[int, Sequence[int]]] = [1, 1, 1],
        residual_hidden_sizes: List[int] = [128, 192, 256],
        residual_kernel_sizes: List[Union[int, Sequence[int]]] = [3, 3, 3],
        residual_pool_kernel_sizes: List[Union[int, Sequence[int]]] = [
            (1, 2),
            (1, 2),
            (1, 2),
        ],
        dropout: float = 0.0,
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = None,
    ):
        super().__init__()
        assert (
            len(residual_sizes)
            == len(residual_kernel_sizes)
            == len(residual_pool_kernel_sizes)
            == len(residual_dilation_sizes)
            == len(residual_hidden_sizes)
        )

        self.bn = nn.BatchNorm2d(num_features=pool_features)
        self.pool = nn.MaxPool2d(kernel_size=pool_kernel_size)
        self.activation = pool_activation
        self.dropout = nn.Dropout(dropout)
        self.resblocks = nn.Sequential()

        for (sz_in, sz_out), kernel_sz, kernel_sz_pool, dilation, hidden_dim in zip(
            residual_sizes,
            residual_kernel_sizes,
            residual_pool_kernel_sizes,
            residual_dilation_sizes,
            residual_hidden_sizes,
        ):
            self.resblocks.append(
                ResBlock2d1x1(
                    in_channels=sz_in,
                    out_channels=sz_out,
                    hidden_size=hidden_dim,
                    dilation=dilation,
                    kernel_size=kernel_sz,
                    pool_kernel_size=kernel_sz_pool,
                    activation=resblock_activation,
                    norm=norm,
                )
            )

    def forward(self, x: Tensor) -> Tensor:
        x = self.resblocks(x)
        x = self.activation(self.bn(x))
        return self.pool(x)
