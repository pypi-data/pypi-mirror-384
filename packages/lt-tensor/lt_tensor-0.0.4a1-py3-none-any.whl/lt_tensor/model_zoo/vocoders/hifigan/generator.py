__all__ = ["HifiganGenerator"]


from lt_utils.common import *
import torch
from torch import nn, Tensor
from lt_tensor.model_zoo.convs import ConvBase, is_conv
from lt_utils.file_ops import is_file, load_json
from lt_tensor.tensor_ops import normalize_minmax
from .config import HifiganConfig


def init_weights(m, mean=0.0, std=0.01):
    if is_conv(m):
        nn.init.normal_(m.weight, mean, std)
    else:
        for module in m.modules():
            if is_conv(module):
                nn.init.normal_(module.weight, mean, std)


class HifiganGenerator(ConvBase):
    def __init__(
        self,
        cfg: Union[HifiganConfig, Dict[str, object]] = HifiganConfig(),
        extra_layer: nn.Module = nn.Identity(),
    ):
        super().__init__()
        cfg = cfg if isinstance(cfg, HifiganConfig) else HifiganConfig(**cfg)
        self.cfg = cfg

        self.num_kernels = len(cfg.resblock_kernel_sizes)
        self.num_upsamples = len(cfg.upsample_rates)
        self.conv_pre = self.get_1d_conv(
            self.cfg.in_channels,
            self.cfg.upsample_initial_channel,
            7,
            padding=3,
            norm="weight_norm",
        )

        if isinstance(self.cfg.groups, (list, tuple)):
            assert len(self.cfg.groups) == len(
                self.cfg.upsample_kernel_sizes
            ), "if Groups is a list, it must have the size of upsample kernel sizes."
            self.groups = self.cfg.groups
        else:
            self.groups = [
                self.cfg.groups for _ in range(len(self.cfg.upsample_kernel_sizes))
            ]

        if isinstance(self.cfg.residual_groups, (list, tuple)):
            assert len(self.cfg.residual_groups) == len(
                self.cfg.upsample_kernel_sizes
            ), "if Residual Groups is a list, it must have the size of upsample kernel sizes"
            self.resblocks_groups = self.cfg.residual_groups
        else:
            self.resblocks_groups = [
                self.cfg.residual_groups
                for _ in range(len(self.cfg.upsample_kernel_sizes))
            ]

        self.ups = nn.ModuleList()

        for i, (u, k, g) in enumerate(
            zip(cfg.upsample_rates, cfg.upsample_kernel_sizes, self.groups)
        ):
            in_ch = cfg.upsample_initial_channel // (2**i)
            self.ups.append(
                nn.ModuleDict(
                    dict(
                        up=nn.Sequential(
                            cfg.get_activation(
                                cfg.activation,
                                in_features=in_ch,
                                in_channels=in_ch,
                                channels=in_ch,
                            ),
                            self.get_1d_conv(
                                in_channels=in_ch,
                                out_channels=cfg.upsample_initial_channel
                                // (2 ** (i + 1)),
                                kernel_size=k,
                                stride=u,
                                padding=(k - u) // 2,
                                groups=g,
                                norm="weight_norm",
                                transposed=True,
                            ),
                        ),
                    ),
                )
            )

        if isinstance(self.cfg.residual_groups, (list, tuple)):
            if len(self.cfg.residual_groups) != len(self.ups):
                self.residual_groups = self.cfg.groups = [self.cfg.residual_groups]
            self.groups = self.cfg.groups

        self.resblocks = nn.ModuleList()
        for i in range(len(self.ups)):
            ch = cfg.upsample_initial_channel // (2 ** (i + 1))
            for j, (k, d) in enumerate(
                zip(cfg.resblock_kernel_sizes, cfg.resblock_dilation_sizes)
            ):
                self.resblocks.append(
                    self.cfg.retrieve_resblock(
                        ch,
                        d,
                        k,
                        activation_kwargs=dict(
                            in_features=ch,
                            channels=ch,
                            in_channels=ch,
                            out_channels=ch,
                        ),
                        groups=self.resblocks_groups[i],
                    )
                )

        out_ch = cfg.upsample_initial_channel // (2**i)
        self.conv_post = nn.Sequential(
            cfg.get_activation(
                cfg.last_activation,
                in_features=out_ch,
                in_channels=out_ch,
                channels=out_ch,
                out_channels=out_ch,
            ),
            self.get_1d_conv(
                ch,
                1,
                7,
                padding=3,
                bias=self.cfg.use_bias_on_final_layer,
                norm="weight_norm",
            ),
        )
        self.extra_layer = extra_layer

        self.conv_pre.apply(init_weights)
        self.conv_post[-1].apply(init_weights)
        self.resblocks.apply(init_weights)
        self.ups.apply(init_weights)
        for module in self.ups:
            init_weights(module["up"][-1])
        for md in self.resblocks:
            init_weights(md)

    def forward(self, x: Tensor):
        x = self.conv_pre(x)
        for i in range(self.num_upsamples):
            x = self.ups[i]["up"](x)
            xs = torch.zeros_like(x, device=x.device)
            for j in range(self.num_kernels):
                xs += self.resblocks[i * self.num_kernels + j](x)
            x = xs / self.num_kernels
        x = self.conv_post(x)
        x = self.extra_layer(x)
        if self.cfg.final_gate == "tanh":
            return x.tanh()
        if self.cfg.final_gate == "clamp":
            return torch.clamp(x, -1, 1)
        if self.cfg.final_gate == "norm":
            return normalize_minmax(x, min_val=-1.0, max_val=1.0)
        return x

    @classmethod
    def from_pretrained(
        cls,
        model_file: PathLike,
        model_config: Union[
            HifiganConfig, Dict[str, Any], Dict[str, Any], PathLike
        ] = HifiganConfig(),
        *,
        remove_norms: bool = False,
        strict: bool = False,
        map_location: Union[str, torch.device] = torch.device("cpu"),
        weights_only: bool = False,
        mmap: Optional[bool] = None,
        assign: bool = False,
        **kwargs,
    ):
        is_file(model_file, validate=True)
        if isinstance(map_location, str):
            map_location = torch.device(map_location)
        model_state_dict = torch.load(
            model_file,
            weights_only=weights_only,
            map_location=map_location,
            mmap=mmap,
        )

        if isinstance(model_config, (HifiganConfig, dict)):
            h = model_config
        elif isinstance(model_config, (str, Path, bytes)):
            h = HifiganConfig(**load_json(model_config, {}))

        model = cls(h)
        if remove_norms:
            model.remove_norms()
        try:
            model.load_state_dict(model_state_dict, strict=strict, assign=assign)
            return model
        except RuntimeError as e:
            if remove_norms:
                raise e
            print(f"[INFO] Removing norms...")
            model.remove_norms()
            model.load_state_dict(model_state_dict, strict=strict, assign=assign)
        return model
