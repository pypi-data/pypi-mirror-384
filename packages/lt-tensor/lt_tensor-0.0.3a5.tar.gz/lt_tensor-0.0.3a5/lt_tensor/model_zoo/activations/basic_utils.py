from torch import nn, Tensor
from lt_tensor.model_base import Model

from typing import List, Literal, Optional


def _ones_init(x: nn.Parameter, base: float = 1e-5):
    nn.init.ones_(x)
    x.data = x.data * base
    return x


class _ActivationBase(Model):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialize_params: List[str] = []

    def __call__(self, *args, **kwds) -> Tensor:
        return super().__call__(*args, **kwds)

    def reset_parameters(
        self,
        restart_type: Literal["ones", "orthogonal", "xavier", "normal"] = "ones",
        base_ones: float = 5e-3,
        std: float = 0.1,
        mean=0,
        gain: float = 1,
        seed: Optional[int] = None,
    ):
        match restart_type:
            case "normal":
                init_fn = lambda x: nn.init.normal_(x, mean=mean, std=std)
            case "orthogonal":
                init_fn = lambda x: nn.init.orthogonal_(x, gain=gain)
            case "xavier":
                init_fn = lambda x: nn.init.xavier_normal_(x, gain=gain)
            case _:
                init_fn = lambda x: _ones_init(x, base_ones)

        def _validate(name: str):
            if not self._initialize_params:
                return False
            for x in self._initialize_params:
                if x in name or name in x:
                    return True
            return False

        if seed is not None:
            self.set_seed(seed)
        for name, param in self.named_parameters():
            if not _validate(name):
                continue
            init_fn(param)

    def forward(self, x: Tensor, *args, **kwargs) -> Tensor:
        raise NotImplementedError()
