import torch
from torch import nn, Tensor
from abc import ABC, abstractmethod

from lt_utils.common import *
from .base import _GatedResblockBase
from lt_utils.misc_utils import filter_kwargs, ff_list
from lt_tensor.model_zoo.fusion import FiLMConv1d
from lt_tensor.model_zoo.convs import ConvBase, BidirectionalConv
from lt_tensor.model_zoo.activations import alias_free
from lt_tensor.model_zoo.basic import Scale
from lt_tensor.tensor_ops import normalize_minmax
from lt_utils.type_utils import is_array


class GatedResidualBlock(_GatedResblockBase):
    def forward(self, x: Tensor, cond: Optional[Tensor] = None):
        res_base = x
        x = self._apply_cond(x=x, cond=cond)
        residual = torch.zeros_like(x)
        for i, b in enumerate(self.dilation_blocks):
            y_fwd, y_bwd = b["conv"](b["activ_1"](res_base))
            skip = self._get_gated(y_fwd, y_bwd)
            res_base = b["proj"](b["activ_2"]((skip)))
            residual = (res_base * self.skip_sz) + residual
        return x + residual
