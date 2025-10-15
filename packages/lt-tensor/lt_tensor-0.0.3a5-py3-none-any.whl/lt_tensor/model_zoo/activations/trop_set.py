import math
import torch

from torch import nn, Tensor
from .basic_utils import _ActivationBase
from typing import Union, Sequence


class SepHermite(_ActivationBase):
    def __init__(
        self,
        degree: int = 3,
        base_value: float = 2e-3,
        requires_grad: bool = True,
    ):
        super().__init__()
        degree = int(degree)
        assert (
            degree >= 1
        ), f"degree must be equal or larger than 1, received instead: {degree}"
        self.degree = degree
        # Learnable coefficients for each polynomial degree
        self.coeffs = nn.Parameter(
            torch.ones(degree + 1) * base_value, requires_grad=requires_grad
        )
        self.step_ld = 1.0 / (math.sqrt(degree) * math.pi)

    def forward(self, x: Tensor):
        h0, h1 = torch.ones_like(x), 2 * x
        if self.degree == 1:
            return h0 * self.coeffs[0] + h1 * self.coeffs[1]
        out = h0 * self.coeffs[0] + h1 * self.coeffs[1]
        for n in range(2, self.degree + 1):
            h0, h1 = h1, 2 * x * h1 - 2 * (n - 1) * h0
            out = out + h1 * self.coeffs[n] * self.step_ld
        return out


class Hermite(_ActivationBase):
    def __init__(
        self,
        degree: int = 3,
        base_value: float = 2e-3,
        requires_grad: bool = True,
    ):
        super().__init__()
        degree = int(degree)
        assert (
            degree >= 1
        ), f"degree must be equal or larger than 1, received instead: {degree}"
        self.degree = int(degree)
        # Learnable coefficients for each polynomial degree
        self.coeffs = nn.Parameter(
            torch.ones(degree + 1) * base_value, requires_grad=requires_grad
        )
        self.step_ld = 1.0 / (math.sqrt(degree) * math.pi)

    def forward(self, x: Tensor):
        H = [torch.ones_like(x), 2 * x]  # H0 and H1

        for n in range(2, self.degree + 1):
            Hn = 2 * x * H[-1] - 2 * (n - 1) * H[-2]
            H.append(Hn * self.step_ld)
        H_stack = torch.stack(H[: self.degree + 1], dim=-1)
        return (H_stack * self.coeffs).sum(-1)


class MaxShiftPoly(_ActivationBase):
    def __init__(
        self,
        degree: int = 3,
        dim: Union[Sequence[int], int] = -1,
        base_value: float = 2e-3,
        requires_grad: bool = True,
    ):
        super().__init__()
        # version 0 shows the best quality, but slower
        self.degree = degree
        self.a = nn.Parameter(
            torch.ones(degree + 1) * base_value, requires_grad=requires_grad
        )
        self.dim = dim
        k = torch.arange(self.degree + 1, dtype=torch.float32)
        self.register_buffer("k", k, True)

    def forward(self, x: Tensor):
        out = self.a[0]  # scalar bias
        for k in range(1, self.degree + 1):
            out = torch.maximum(out, self.a[k] + k * x)
        return out


class TropicalPoly(_ActivationBase):
    def __init__(
        self,
        degree: int = 3,
        base_value: float = 2e-3,
        requires_grad: bool = True,
    ):
        super().__init__()
        # version 0 shows the best quality, but slower
        self.degree = degree
        self.a = nn.Parameter(
            torch.ones(degree + 1) * base_value, requires_grad=requires_grad
        )
        k = torch.arange(self.degree + 1, dtype=torch.float32)
        self.register_buffer("k", k, True)

    def forward(self, x: Tensor):
        xk = x.unsqueeze(-1) * self.k
        return torch.amax(self.a * xk, dim=-1)


class FourierComplex(_ActivationBase):
    def __init__(
        self,
        max_freq: int = 3,
        base_value: float = 2e-3,
        requires_grad: bool = True,
    ):
        super().__init__()
        self.max_freq = max_freq
        self.imag_base = nn.Parameter(
            torch.ones(max_freq, dtype=torch.float32) * base_value,
            requires_grad=requires_grad,
        )
        self.real_base = nn.Parameter(
            torch.ones(max_freq, dtype=torch.float32) * base_value,
            requires_grad=requires_grad,
        )
        k = torch.arange(1, self.max_freq + 1, dtype=torch.float32)
        self.register_buffer("k", k)

    def forward(self, x: Tensor):
        xk = x.unsqueeze(-1) * self.k
        complex_set = torch.polar(torch.ones_like(xk), xk)  # complex repr: exp(i xk)
        # sin = imag, cos = real
        return torch.sum(
            complex_set.real * self.real_base + complex_set.imag * self.imag_base,
            dim=-1,
        )


class FourierBase(_ActivationBase):
    def __init__(
        self,
        max_freq: int = 3,
        base_value: float = 2e-3,
        requires_grad: bool = True,
    ):
        super().__init__()
        self.max_freq = max_freq
        self.imag_base = nn.Parameter(
            torch.ones(max_freq, dtype=torch.float32) * base_value,
            requires_grad=requires_grad,
        )
        self.real_base = nn.Parameter(
            torch.ones(max_freq, dtype=torch.float32) * base_value,
            requires_grad=requires_grad,
        )
        k = torch.arange(1, self.max_freq + 1, dtype=torch.float32)
        self.register_buffer("k", k)

    def forward(self, x: Tensor):
        xk = x.unsqueeze(-1) * self.k
        sin_terms = torch.sin(xk) * self.imag_base
        cos_terms = torch.cos(xk) * self.real_base
        # Sum over frequencies
        return torch.sum(sin_terms + cos_terms, dim=-1)



