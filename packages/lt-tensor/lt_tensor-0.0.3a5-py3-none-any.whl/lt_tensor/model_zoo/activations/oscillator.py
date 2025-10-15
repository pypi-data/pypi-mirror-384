import math
import torch

from torch import nn, Tensor
from .basic_utils import _ActivationBase

from .base import ScaleMinMax
from typing import Callable
from torch.nn import functional as F


class Oscillator(_ActivationBase):
    def __init__(
        self,
        d_model: int = 3,
        base: float = 1.0,
        radius: float = math.pi / 2,
        signal: float = 32.0,
        signal_range: float = 8,
        requires_grad: bool = True,
        min_max_gate: bool = False,
        eps: float = 1e-7,
        lower_gate_fn: Callable[[Tensor], Tensor] = F.tanh,
        upper_gate_fn: Callable[[Tensor], Tensor] = F.tanh,
    ):
        super().__init__()
        radius_floor = math.pi * 1e-5
        self.eps = eps
        self.min_max_gate = min_max_gate
        self.upper_gate_fn = upper_gate_fn
        self.lower_gate_fn = lower_gate_fn

        radius = max(radius_floor, min(radius, math.pi - radius_floor))

        signal_range = max(abs(float(signal_range)), 1e-5)
        signal = max(abs(float(signal)), 1e-5)
        base = float(base)
        if base == 0:  # allows negative values
            base = 1e-5

        self.base = nn.Parameter(
            torch.ones((d_model,), dtype=torch.float32) * base,
            requires_grad=requires_grad,
        )
        self.signal = nn.Parameter(
            torch.linspace(signal, -signal, steps=d_model, dtype=torch.float32),
            requires_grad=requires_grad,
        )

        self.range = nn.Parameter(
            torch.linspace(
                -signal_range,
                signal_range,
                steps=d_model,
                dtype=torch.float32,
            ),
            requires_grad=requires_grad,
        )

        radius_tensor = torch.tensor(radius, dtype=torch.float32)
        self.register_buffer("radius", radius_tensor, persistent=True)

    def forward(self, x: Tensor):
        x = x.unsqueeze(-1)
        cos_x = x.cos()
        ranged_radius = self.range / (self.radius + self.eps)
        rr_signal = self.signal * ranged_radius * cos_x

        upper = self.base * self.upper_gate_fn(cos_x)
        lower = self.lower_gate_fn(torch.sin(0.5 * rr_signal))

        # Sum the bands, then mean across the d_model dimension
        return torch.mean(upper + lower, dim=-1)


class OscillatorSum(Oscillator):
    def forward(self, x: Tensor):
        return x + super().forward(x)


class OscillatorMul(Oscillator):
    def __init__(
        self,
        d_model: int = 3,
        base: float = 1.0,
        radius: float = math.pi / 2,
        signal: float = 32.0,
        signal_range: float = 8,
        requires_grad: bool = True,
        min_max_gate: bool = False,
        eps: float = 1e-7,
        lower_gate_fn: Callable[[Tensor], Tensor] = F.tanh,
        upper_gate_fn: Callable[[Tensor], Tensor] = F.tanh,
        norm_fn: Callable[[Tensor], Tensor] = F.tanh,
    ):
        super().__init__(
            d_model,
            base,
            radius,
            signal,
            signal_range,
            requires_grad,
            min_max_gate,
            eps,
            lower_gate_fn,
            upper_gate_fn,
        )
        self.norm_fn = norm_fn

    def forward(self, x: Tensor):
        return x * 1.0 + self.norm_fn(super().forward(x))
