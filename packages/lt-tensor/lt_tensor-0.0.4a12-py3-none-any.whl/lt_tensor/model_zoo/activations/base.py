from torch import Tensor, nn
from .basic_utils import _ActivationBase
from lt_utils.common import *
from torch.nn import functional as F


class ScaleMinMax(_ActivationBase):
    def __init__(
        self,
        min_value: Optional[Number] = None,
        max_value: Optional[Number] = None,
        eps: float = 1e-7,
        dim: Optional[Union[int, Sequence[int]]] = None,
    ):
        super().__init__()
        self.min_value = min_value
        self.max_value = max_value
        self.eps = eps
        self.dim = dim

    def forward(self, x: Tensor) -> Tensor:
        if self.min_value is None and self.max_value is None:
            return x
        if self.dim is None:
            x_min, x_max = x.amin(), x.amax()
        else:
            x_min, x_max = x.amin(dim=self.dim), x.amax(dim=self.dim)

        min_val = x_min if self.min_value is None else self.min_value
        max_val = x_max if self.max_value is None else self.max_value
        return (x - x_min) / (x_max - x_min + self.eps) * (max_val - min_val) + min_val


class SoftCELU(_ActivationBase):
    def __init__(self, alpha=1.0):
        super().__init__()
        self.celu = nn.CELU(alpha=alpha)

    def forward(self, x):
        return F.softplus(x) * self.celu(x)


class _ActivationWP(_ActivationBase):
    def __init__(
        self,
        activation: Union[nn.Module, _ActivationBase, Callable[[Tensor], Tensor]],
        activ_norm: Optional[Union[nn.Module, Callable[[Tensor], Tensor]]] = None,
        op_norm: Optional[Union[nn.Module, Callable[[Tensor], Tensor]]] = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.activation = activation
        self.activ_norm = activ_norm
        self.op_norm = op_norm

    def _apply_norm_activ(self, x: Tensor):
        if self.activ_norm is not None:
            return self.activ_norm(x)
        return x

    def _apply_output_norm(self, x: Tensor):
        if self.op_norm is not None:
            return self.op_norm(x)
        return x


class SumActivation(_ActivationWP):
    def forward(self, x: Tensor):
        data = x + self._apply_norm_activ(self.activation(x))
        return self._apply_output_norm(data)


class MulActivation(_ActivationWP):
    def __init__(
        self,
        activation: Union[nn.Module, _ActivationBase, Callable[[Tensor], Tensor]],
        activ_norm: Optional[Union[nn.Module, Callable[[Tensor], Tensor]]] = None,
        op_norm: Optional[Union[nn.Module, Callable[[Tensor], Tensor]]] = None,
        base: Optional[float] = None,
        *args,
        **kwargs
    ):
        super().__init__(activation, activ_norm, op_norm, *args, **kwargs)
        self.__base_add = base

    def forward(self, x: Tensor):
        if self.__base_add:
            data = self._apply_norm_activ(self.__base_add + self.activation(x))
        else:
            data = self._apply_norm_activ(self.activation(x))
        return self._apply_output_norm(data)
