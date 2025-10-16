import math
from lt_utils.common import *
from lt_tensor.common import *
from einops import repeat
import torch.nn.functional as F
from torch.nn.utils.parametrizations import weight_norm
from lt_tensor.transform import get_sinusoidal_embedding


class MLPBase(Model):
    def __init__(
        self,
        d_model: int,
        ff_dim: int,
        n_classes: int,
        activation: nn.Module = nn.LeakyReLU(0.1),
        norm: nn.Module = nn.Dropout(0.01),
    ):
        """Creates a MLP block, with the chosen activation function and the normalizer."""
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, ff_dim),
            activation,
            norm,
            nn.Linear(ff_dim, n_classes),
        )

    def forward(self, x: Tensor):
        return self.net(x)


class SkipWrap(Model):

    def __init__(self, block: nn.Module, gain: float = 1.0, eps: float = 1e-7):
        super().__init__()
        self.block = block
        self.eps = eps
        self.gain = nn.Parameter(torch.tensor(gain), requires_grad=True)

    def forward(self, x, *args, **kwargs):
        out = self.block(x, *args, **kwargs)
        return out + ((self.gain + self.eps) * x)


class Scale(Model):
    def __init__(
        self,
        dim: Union[int, Sequence[int]],
        init_value: float = 1.0,
        requires_grad: bool = True,
    ):
        super().__init__()
        self.scale = nn.Parameter(
            init_value * torch.ones(dim),
            requires_grad=requires_grad,
        )

    def forward(self, x):
        return x * self.scale


class MLP(Model):
    def __init__(
        self,
        d_model: int,
        ff_dim: int,
        n_classes: int,
        activation: nn.Module = nn.LeakyReLU(0.1),
        norm: nn.Module = nn.Dropout(0.01),
        layers: int = 2,
    ):
        super().__init__()
        assert layers >= 1
        self.net = nn.Sequential()

        nc = n_classes if layers == 1 else ff_dim
        self.net.append(
            MLPBase(
                d_model=d_model,
                ff_dim=ff_dim,
                n_classes=nc,
                norm=norm,
                activation=activation,
            )
        )
        if layers > 1:
            if layers == 2:
                self.net.append(
                    MLPBase(
                        d_model=ff_dim,
                        ff_dim=ff_dim,
                        n_classes=n_classes,
                        norm=norm,
                        activation=activation,
                    )
                )
            else:
                for _ in range(layers - 1):
                    self.net.append(
                        MLPBase(
                            d_model=ff_dim,
                            ff_dim=ff_dim,
                            n_classes=ff_dim,
                            norm=norm,
                            activation=activation,
                        )
                    )
                self.net.append(
                    MLPBase(
                        d_model=ff_dim,
                        ff_dim=ff_dim,
                        n_classes=n_classes,
                        norm=norm,
                        activation=activation,
                    )
                )

    def forward(self, x: Tensor):
        return self.net(x)


class GRUBlock(Model):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        num_layers: int = 1,
        bidirectional: bool = False,
        dropout: float = 0.01,
        bias: bool = True,
        batch_first: bool = True,
        return_values: Literal["output", "hidden", "full"] = "output",
    ):
        super().__init__()
        self.gru = nn.GRU(
            input_dim,
            hidden_dim,
            num_layers=int(max(num_layers, 1)),
            batch_first=batch_first,
            bidirectional=bidirectional,
            bias=bias,
            dropout=0 if num_layers < 2 else dropout,
        )
        self.return_values = return_values
        self.output_dim = hidden_dim * (2 if bidirectional else 1)

    def forward(self, x: Tensor, hx: Optional[Tensor] = None) -> Tensor:
        if self.training is False:
            self.gru.flatten_parameters()
        output, hidden = self.gru.forward(x, hx=hx)
        if self.return_values == "output":
            return output
        elif self.return_values == "hidden":
            return hidden
        return output, hidden


class SwiGLU(Model):
    def __init__(self, d_model: int, d_hidden: int, dropout: float = 0.1):
        super().__init__()
        self.w1 = nn.Linear(d_model, d_hidden)
        self.w2 = nn.Linear(d_model, d_hidden)
        self.w3 = nn.Linear(d_hidden, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        return self.dropout(self.w3(F.silu(self.w1(x)) * self.w2(x)))


class ExClassifier(Model):
    def __init__(self, in_features: int = 1, num_classes=5):
        super().__init__()
        self.model = nn.Sequential(
            nn.Conv1d(in_features, 256, kernel_size=3, padding=1),
            nn.LeakyReLU(0.2),
            nn.Conv1d(256, 256, kernel_size=7, padding=3, groups=2),
            nn.BatchNorm1d(256),
            nn.LeakyReLU(0.2),
            nn.Conv1d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm1d(256),
            nn.LeakyReLU(0.2),
            nn.AdaptiveAvgPool1d(1),  # Output shape: [B, 64, 1]
            nn.Flatten(),  # -> [B, 64]
            nn.Linear(256, num_classes),
        )
        self.eval()

    def forward(self, x):
        return self.model(x)


class Shift(nn.Module):
    def __init__(
        self, shifts: Union[int, Sequence[int]], dims: Union[int, Sequence[int]]
    ):
        super().__init__()
        self.shifts = shifts
        self.dims = dims

    def forward(self, x: Tensor):
        return torch.roll(x, shifts=self.shifts, dims=self.dims)


class LoRALinearLayer(Model):

    def __init__(
        self,
        in_features: int,
        out_features: int,
        rank: int = 4,
        alpha: float = 1.0,
    ):
        super().__init__()
        self.down = nn.Linear(in_features, rank, bias=False)
        self.up = nn.Linear(rank, out_features, bias=False)
        self.alpha = alpha
        self.rank = rank
        self.out_features = out_features
        self.in_features = in_features
        self.ah = self.alpha / self.rank
        self._down_dt = self.down.weight.dtype

        nn.init.normal_(self.down.weight, std=1 / rank)
        nn.init.zeros_(self.up.weight)

    def forward(self, hidden_states: Tensor) -> Tensor:
        orig_dtype = hidden_states.dtype
        down_hidden_states = self.down(hidden_states.to(self._down_dt))
        up_hidden_states = self.up(down_hidden_states) * self.ah
        return up_hidden_states.to(orig_dtype)


class LoRAConv1DLayer(Model):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        kernel_size: Union[int, Tuple[int, ...]] = 1,
        rank: int = 4,
        alpha: float = 1.0,
    ):
        super().__init__()
        self.down = nn.Conv1d(
            in_features, rank, kernel_size, padding=kernel_size // 2, bias=False
        )
        self.up = nn.Conv1d(
            rank, out_features, kernel_size, padding=kernel_size // 2, bias=False
        )
        self.ah = alpha / rank
        self._down_dt = self.down.weight.dtype
        nn.init.kaiming_uniform_(self.down.weight, a=math.sqrt(5))
        nn.init.zeros_(self.up.weight)

    def forward(self, inputs: Tensor) -> Tensor:
        orig_dtype = inputs.dtype
        down_hidden_states = self.down(inputs.to(self._down_dt))
        up_hidden_states = self.up(down_hidden_states) * self.ah
        return up_hidden_states.to(orig_dtype)


class LoRAConv2DLayer(Model):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        kernel_size: Union[int, Tuple[int, ...]] = (1, 1),
        rank: int = 4,
        alpha: float = 1.0,
    ):
        super().__init__()
        self.down = nn.Conv2d(
            in_features,
            rank,
            kernel_size,
            padding="same",
            bias=False,
        )
        self.up = nn.Conv2d(
            rank,
            out_features,
            kernel_size,
            padding="same",
            bias=False,
        )
        self.ah = alpha / rank

        nn.init.kaiming_normal_(self.down.weight, a=0.2)
        nn.init.zeros_(self.up.weight)

    def forward(self, inputs: Tensor) -> Tensor:
        orig_dtype = inputs.dtype
        down_hidden_states = self.down(inputs.to(self._down_dt))
        up_hidden_states = self.up(down_hidden_states) * self.ah
        return up_hidden_states.to(orig_dtype)
