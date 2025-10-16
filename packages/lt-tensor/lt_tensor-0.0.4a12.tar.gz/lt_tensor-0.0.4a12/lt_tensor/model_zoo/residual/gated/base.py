__all__ = [
    "ResBlock",
    "AMPBlock",
    "GatedResBlock",
    "ResBlock2d1x1",
    "PoolResBlock2D",
]
from abc import ABC, abstractmethod
from torch import nn, Tensor
from lt_utils.common import *
from lt_utils.misc_utils import ff_list
from lt_utils.type_utils import is_array
from lt_tensor.model_zoo.fusion import FiLMConv1d, FiLMConv2d
from lt_tensor.model_zoo.convs import ConvBase
from lt_tensor.misc_utils import enable_module


def _to_seq_of_size(
    item: Union[Any, List[Any]],
    target_size: int,
    filler: Optional[Any] = None,
    slice_extra: bool = False,
):
    if filler is None:
        if item is None or (is_array(item, False) and not item):
            raise ValueError(
                "Cannot process an item when there is no filler and the item is not valid."
            )
    result = []
    if is_array(item, False):
        if len(item) >= target_size:
            if slice_extra:
                return [x for x in item][:target_size]
            return item
        if item:
            [result.append(i) for i in item]

        if filler is None:
            filler = item[-1]

    else:
        if item is not None:
            result.append(item)
        if filler is None:
            filler = item
    missing = target_size - len(result)
    [result.append(filler) for _ in range(missing)]
    return result


_INIT_CALLABLE: TypeAlias = Callable[[Union[nn.Module, Tensor, nn.Parameter]], Any]


class _GatedResblockBase(ConvBase, ABC):
    def __init__(
        self,
        channels: int,
        kernel_size: Sequence[int] = 3,
        groups: Sequence[int] = 1,
        groups_bwd: Sequence[int] = 1,
        dilations: Sequence[int] = (1, 3, 5, 9),
        dilations_bwd: Sequence[int] = (5, 1, 9, 3),
        dilations_proj: Sequence[int] = (2, 4, 4, 1),
        activation: Callable[[None], nn.Module] = lambda: nn.LeakyReLU(0.1),
        norm: Optional[Literal["weight", "spectral"]] = None,
        use_cond: bool = False,
        cond_size: Optional[int] = None,
        cond_dilation: int = 1,
        cond_kernel: int = 3,
        cond_interp_match: bool = False,
        gating_direction: Literal["fwd_bwd", "bwd_fwd"] = "fwd_bwd",
        residual_type: Literal["1d", "2d"] = "1d",
        activ_kwargs: Dict[str, Any] = {},
        **kwargs,
    ):
        self.conditional = use_cond
        self.gating_direction = gating_direction
        self.dilation_blocks = nn.ModuleList()
        if is_array(groups, False):
            groups = ff_list(groups, int)
        groups = _to_seq_of_size(groups, len(dilations), filler=1)
        groups_bwd = _to_seq_of_size(groups_bwd, len(dilations), filler=1)
        kernel_size = _to_seq_of_size(kernel_size, len(dilations), filler=1)

        if residual_type == "1d":
            cnv = self.get_1d_conv
            biconv = self.get_bidirectional_conv_1d
            film = FiLMConv1d
        elif residual_type == "2d":
            cnv = self.get_2d_conv
            biconv = self.get_bidirectional_conv_2d
            film = FiLMConv2d
        else:
            raise ValueError(
                f"`residual_type` '{residual_type} not implemented! Use '1d' or '2d'"
            )

        self.cond = (
            nn.Identity()
            if not use_cond
            else FiLMConv1d(
                cond_channels=cond_size or channels,
                feat_channels=channels,
                kernel_size=cond_kernel,
                dilations=cond_dilation,
                padding=self.get_padding(
                    cond_kernel,
                    cond_dilation,
                ),
                interp_match=cond_interp_match,
                norm=norm,
            )
        )
        for d, db, k, g, gb in zip(
            dilations,
            dilations_bwd,
            kernel_size,
            groups,
            groups_bwd,
            dilations_proj,
        ):
            self.dilation_blocks.append(
                nn.ModuleDict(
                    {
                        "activ_1": enable_module(activation, **activ_kwargs),
                        "activ_2": enable_module(activation, **activ_kwargs),
                        "conv": biconv(
                            channels,
                            channels,
                            kernel_size=k,
                            dilation=d,
                            bwd_dilation=db,
                            padding=self.get_padding(k, d),
                            padding_bwd=self.get_padding(k, db),
                            norm=norm,
                            groups=g,
                            groups_bwd=gb,
                            return_tuple=True,
                            transposed=False,
                        ),
                        "proj": cnv(channels, norm=norm, kernel_size=3, padding=1),
                    }
                )
            )
        self.total_layers = len(self.dilation_blocks)
        self.skip_sz = 1.0 / self.total_layers

    def apply_init(
        self,
        init_fn: _INIT_CALLABLE,
        init_fn_bias: Optional[_INIT_CALLABLE] = None,
        init_film: Optional[_INIT_CALLABLE] = None,
    ):
        self.dilation_blocks: List[Dict[str, Union[nn.Module, nn.Conv1d]]]
        for block in self.dilation_blocks:
            init_fn(block["conv"].weight)
            init_fn(block["proj"].weight)
            if init_fn_bias is not None:
                if block["conv"].bias is not None:
                    init_fn_bias(block["conv"].bias)
                if block["proj"].bias is not None:
                    init_fn_bias(block["proj"].bias)
        if self.conditional and init_film is not None:
            init_film(self.conditional)

    def _get_gated(
        self,
        y_fwd: Tensor,
        y_bwd: Tensor,
    ):
        if self.gating_direction == "bwd_fwd":
            return y_bwd.sigmoid() * y_fwd.tanh()
        return y_fwd.sigmoid() * y_bwd.tanh()

    def _apply_cond(self, y_spec: Tensor, cond: Optional[Tensor]):
        if not self.conditional or cond is None:
            return y_spec
        return y_spec + self.cond(y_spec, cond)

    @abstractmethod
    def forward(
        self, x: Tensor, cond: Optional[Tensor] = None
    ) -> Union[Tensor, Tuple[Tensor, Tensor]]: ...
