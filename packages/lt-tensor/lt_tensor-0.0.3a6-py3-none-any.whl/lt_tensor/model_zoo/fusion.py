from lt_utils.common import *
from lt_tensor.common import *
import torch.nn.functional as F
from lt_tensor.model_zoo.basic import Scale
from lt_tensor.model_zoo.activations import Snake
from lt_tensor.model_zoo.convs import (
    get_conv,
    get_1d_conv,
    get_2d_conv,
    get_3d_conv,
)

TC: TypeAlias = Callable[[Any], Tensor]


class Conv1DGatedFusion(Model):
    def __init__(
        self,
        channels: int,
        kernel_size: Union[int, Sequence[int]] = 1,
        stride: int = 1,
        padding: Union[int, Sequence[int]] = 0,
        dilation: int = 1,
        groups: int = 1,
        bias: bool = True,
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = None,
    ):
        super().__init__()
        # use sigmoid to get gating in [0,1]
        self.gate = get_2d_conv(
            channels * 2,
            channels,
            kernel_size=kernel_size,
            stride=stride,
            dilation=dilation,
            padding=padding,
            groups=groups,
            bias=bias,
            norm=norm,
        )

    def forward(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        # a,b: (B, C, T)
        g = torch.sigmoid(self.gate(torch.cat([a, b], dim=1)))
        return g * a + (1.0 - g) * b


class FiLMConv1d(Model):
    def __init__(
        self,
        feat_channels: int,
        cond_channels: int,
        kernel_size: Union[int, Sequence[int]] = 1,
        stride: int = 1,
        padding: Union[int, Sequence[int]] = 0,
        dilation: int = 1,
        groups: int = 1,
        bias: bool = True,
        interp_match: bool = False,
        transposed: bool = False,
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = None,
    ):
        super().__init__()
        self.interp_match = interp_match
        self.modulator = get_1d_conv(
            cond_channels,
            2 * feat_channels,
            kernel_size=kernel_size,
            stride=stride,
            dilation=dilation,
            padding=padding,
            groups=groups,
            bias=bias,
            transposed=transposed,
            norm=norm,
        )

    def forward(self, x: Tensor, cond: Tensor) -> Tensor:
        # x: [B, C, T]
        gamma, beta = torch.chunk(self.modulator(cond), 2, dim=-2)
        if self.interp_match:
            if gamma.size(-1) != x.size(-1):
                gamma = F.interpolate(
                    gamma,
                    size=x.size(-1),
                    mode="linear",
                )
                beta = F.interpolate(
                    beta,
                    size=x.size(-1),
                    mode="linear",
                )
        return x * gamma + beta


class FiLMConv2d(Model):
    def __init__(
        self,
        feat_channels: int,
        cond_channels: int,
        kernel_size: Union[int, Sequence[int]] = 1,
        stride: int = 1,
        padding: Union[int, Sequence[int]] = 0,
        dilation: int = 1,
        groups: int = 1,
        bias: bool = True,
        interp_match: bool = False,
        transposed: bool = False,
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = None,
    ):
        super().__init__()
        self.interp_match = interp_match
        self.cond_dim = cond_channels
        self.feature_dim = feat_channels
        self.modulator = get_2d_conv(
            cond_channels,
            2 * feat_channels,
            kernel_size=kernel_size,
            stride=stride,
            dilation=dilation,
            padding=padding,
            groups=groups,
            bias=bias,
            transposed=transposed,
            norm=norm,
        )

    def forward(self, x: Tensor, cond: Tensor) -> Tensor:
        gamma, beta = torch.chunk(self.modulator(cond), 2, dim=-3)
        if self.interp_match:
            if gamma.shape[-2:] != x.shape[-2:]:
                gamma = F.interpolate(
                    gamma,
                    size=x.shape[-2:],
                    mode="bilinear",
                )
                beta = F.interpolate(
                    beta,
                    size=x.shape[-2:],
                    mode="bilinear",
                )
        return x * gamma + beta


class FiLMFusionScaled(Model):
    def __init__(
        self,
        feature_dim: int,
        cond_dim: int,
        scale: float = 1.0,
        trainable_scale: bool = True,
        bias: bool = True,
        residual_mode: bool = False,
    ):
        """...

        Args:
            cond_dim (int): Dimension of the conditional
            feature_dim (int): Feature/input size, that will be modulated into.
            scale (float, optional): The scale that the condition will be applied to the feature. Defaults to 1.0.
            trainable_scale (bool, optional): When true, the scale will be trainable otherwise will be static. Defaults to True.
            bias (bool, optional): Bias of the modulator. Defaults to True.
            residual_mode (bool, optional): If true, this will sum the x (feature) with the scaled module. Defaults to False.
        """
        super().__init__()
        assert scale != 0.0, "Scale cannot be zero"
        self.scale = Scale(dim=1, init_value=scale, requires_grad=trainable_scale)
        self.modulator = nn.Linear(cond_dim, 2 * feature_dim, bias=bias)
        self.bias = bias
        self.residual_mode = residual_mode

        if self.bias:
            nn.init.zeros_(self.modulator.bias)

    def forward(self, x: Tensor, cond: Tensor) -> Tensor:
        b, g = self.modulator(cond).chunk(2, dim=-1)
        module = x * b + g
        scaled = self.scale(module)
        if self.residual_mode:
            return x + scaled
        return scaled


class GatedSnakeFusion(Model):
    def __init__(
        self,
        feature_dim: int,
        cond_dim: int,
        eps: float = 1e-7,
        scale: float = 1.0,
        snake_scale: float = 1.0,
        trainable_scale: bool = True,
        trainable_snake: bool = True,
        residual_mode: bool = False,
        full_scale: bool = True,
        modulator_bias: bool = True,
        gated_proj_bias: bool = False,
    ):
        super().__init__()
        self.modulator = nn.Linear(cond_dim, 2 * feature_dim, bias=modulator_bias)
        self.snake = Snake(
            feature_dim, alpha=snake_scale, requires_grad=trainable_snake
        )
        self.scale = Scale(
            dim=(1 if not full_scale else feature_dim,),
            init_value=max(float(scale), 1e-5),
            requires_grad=trainable_scale,
        )
        self.eps = eps
        self.gated_proj = nn.Linear(feature_dim, feature_dim, bias=gated_proj_bias)
        self.residual_mode = residual_mode

        if self.modulator.bias is not None:
            nn.init.zeros_(self.modulator.bias)
        if self.gated_proj.bias is not None:
            nn.init.zeros_(self.gated_proj.bias)

    def forward(self, x: Tensor, cond: Tensor) -> Tensor:
        gate, h = torch.chunk(self.modulator(cond), chunks=2, dim=-1)

        gated = gate.sigmoid() * x + (1.0 - h.tanh())

        # transpose, so snake will affect channels then switch back
        snake = self.snake(gated.transpose(-1, -2)).transpose(-2, -1)
        gated_proj = self.gated_proj(gated) + snake

        # scale the proj
        scaled = self.scale(gated_proj)

        if self.residual_mode:
            return x + scaled
        return scaled


class GatedScaledFusion(Model):
    def __init__(
        self,
        feature_dim: int,
        cond_dim: int,
        bias: bool = True,
        scale: float = 1.0,
        full_scale: bool = True,
        trainable_scale: bool = True,
        residual_mode: bool = False,
    ):
        super().__init__()
        assert scale != 0.0, "Scale cannot be zero"
        self.scale = Scale(
            dim=(1 if not full_scale else feature_dim),
            init_value=max(float(scale), 1e-5),
            requires_grad=trainable_scale,
        )
        self.modulator = nn.Linear(cond_dim, 2 * feature_dim, bias=bias)
        self.bias = bias
        self.residual_mode = residual_mode

        if self.bias:
            nn.init.zeros_(self.modulator.bias)

    def forward(self, x: Tensor, cond: Tensor) -> Tensor:
        gate, h = torch.chunk(self.modulator(cond), 2, dim=-1)
        md = gate.sigmoid() * x + (1.0 - h.tanh())
        scaled = self.scale(md)
        if self.residual_mode:
            return x + scaled
        return scaled


# Similar to the GatedSnakeFusion but using activation before
# sum with gated x
class GatedSnakeFusionPrev(Model):
    def __init__(
        self,
        feature_dim: int,
        cond_dim: int,
        eps: float = 1e-5,
        scale: float = 1.0,
        snake_alpha: float = 1.0,
        snake_trainable: bool = False,
        trainable_scale: bool = False,
        full_scale: bool = True,
        residual_mode: bool = False,
    ):
        super().__init__()
        self.proj_expd = nn.Linear(cond_dim, feature_dim * 2)
        self.eps = eps
        self.scale = Scale(
            dim=(1 if not full_scale else feature_dim,),
            init_value=max(float(scale), 1e-5),
            requires_grad=trainable_scale,
        )
        self.snake = Snake(
            in_features=feature_dim, alpha=snake_alpha, requires_grad=snake_trainable
        )
        self.residual_mode = residual_mode

    def forward(self, x: Tensor, cond: Tensor):
        gate, h = torch.chunk(self.proj_expd(cond), 2, dim=-1)
        h_t = self.snake((1.0 - h.tanh()))
        scaled = self.scale(gate.sigmoid() * x + h_t)
        if self.residual_mode:
            return x + scaled
        return scaled


class AdaFusion(Model):
    def __init__(
        self,
        feature_dim: int,
        cond_size: int,
        alpha: float = 1.0,
        train_alpha: bool = True,
    ):
        super().__init__()
        self.fc = nn.Linear(cond_size, feature_dim * 2)
        self.norm = nn.InstanceNorm1d(feature_dim, affine=False)
        self.alpha = nn.Parameter(
            torch.tensor(alpha, dtype=torch.float32), requires_grad=train_alpha
        )

    def forward(
        self,
        inp: Tensor,
        cond: Tensor,
        alpha: Optional[Tensor] = None,
    ):
        h = self.fc(cond)
        h = h.view(h.size(0), h.size(-1), 1)
        gamma, beta = torch.chunk(h, chunks=2, dim=1)
        t = (1.0 + gamma) * self.norm(inp) + beta
        if alpha is not None:
            return t + (1 / alpha) * (torch.sin(alpha * t) ** 2)
        return t + (1 / self.alpha) * (torch.sin(self.alpha * t) ** 2)


class InterpFusion(Model):
    def __init__(
        self,
        d_model: int,
        cond_channels: int = 1,
        features_channels: int = 1,
        alpha: float = 1.0,
        mode: Literal[
            "nearest",
            "linear",
            "bilinear",
            "bicubic",
            "trilinear",
            "area",
        ] = "nearest",
        split_dim: int = -1,
        inner_activation: nn.Module = nn.LeakyReLU(0.1),
    ):
        super().__init__()
        assert d_model % 4 == 0
        if cond_channels != features_channels:
            self.proj_fn = nn.Conv1d(cond_channels, features_channels, kernel_size=1)
        else:
            self.proj_fn = nn.Identity()

        self.d_model = d_model
        self.quarter_size = d_model // 4
        self.alpha = alpha if alpha else 1.0
        self.split_dim = split_dim

        self.fc_list = nn.ModuleList(
            [
                nn.Sequential(
                    inner_activation,
                    nn.Linear(self.quarter_size, self.d_model),
                )
                for _ in range(4)
            ]
        )

        self.d_model = d_model
        self.mode = mode
        self.inter = lambda x: F.interpolate(x, size=self.d_model, mode=self.mode)

    def forward(self, a: Tensor, b: Tensor) -> Tensor:
        xt = torch.zeros_like(a, device=a.device)
        resized = self.inter(b).split(self.quarter_size, dim=self.split_dim)
        for i, fc in enumerate(self.fc_list):
            xt = xt + fc(resized[i])
        return a + self.proj_fn(xt * self.alpha).view_as(a)
