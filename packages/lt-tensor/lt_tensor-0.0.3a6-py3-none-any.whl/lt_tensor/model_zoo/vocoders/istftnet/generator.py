__all__ = ["iSTFTNetGenerator", "iSTFTNetConfig"]
import torch
from lt_utils.common import *
from torch import nn, Tensor
from lt_tensor.model_zoo.convs import ConvBase, is_conv
from .config import iSTFTNetConfig, ResBlock, AMPBlock
from lt_tensor.misc_utils import log_tensor


def padding_fn1(k: int, u: int):
    return (k - u) // 2, 0


def padding_fn2(k: int, u: int):
    return ((k - u) // 2) + u % 2, u % 2


def init_weights(m, mean=0.0, std=0.01):
    if is_conv(m):
        nn.init.normal_(m.weight, mean, std)
    else:
        for module in m.modules():
            if is_conv(module):
                nn.init.normal_(module.weight, mean, std)


class iSTFTNetGenerator(ConvBase):
    def __init__(
        self, cfg: Union[iSTFTNetConfig, Dict[str, object]] = iSTFTNetConfig()
    ):
        super().__init__()
        cfg = cfg if isinstance(cfg, iSTFTNetConfig) else iSTFTNetConfig(**cfg)
        self.cfg = cfg
        self.num_kernels = len(cfg.resblock_kernel_sizes)
        self.num_upsamples = len(cfg.upsample_rates)

        self.conv_pre = self.get_1d_conv(
            cfg.in_channels,
            cfg.upsample_initial_channel,
            7,
            padding=3,
            norm="weight_norm",
        )

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
        pad_fn = padding_fn1 if cfg.sample_rate % 16000 else padding_fn2

        for i, (u, k) in enumerate(zip(cfg.upsample_rates, cfg.upsample_kernel_sizes)):
            pd, pd_out = pad_fn(k, u)

            in_ch = cfg.upsample_initial_channel // (2**i)
            self.ups.append(
                nn.Sequential(
                    cfg.get_activation(
                        cfg.activation,
                        in_features=in_ch,
                        in_channels=in_ch,
                        out_channels=in_ch,
                        channels=in_ch,
                    ),
                    self.get_1d_conv(
                        in_ch,
                        cfg.upsample_initial_channel // (2 ** (i + 1)),
                        k,
                        u,
                        padding=pd,
                        output_padding=pd_out,
                        norm="weight_norm",
                        transposed=True,
                    ),
                )
            )

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

        self.post_n_fft = cfg.gen_istft_n_fft
        self.conv_post = self.get_1d_conv(
            ch,
            self.post_n_fft + 2,
            7,
            padding=3,
            norm="weight_norm",
            bias=self.cfg.use_bias_on_final_layer,
        )
        self.activation = nn.LeakyReLU(0.1)
        self.reflection_pad = nn.ReflectionPad1d((1, 0))
        self.conv_pre.apply(init_weights)
        self.conv_post.apply(init_weights)
        self.resblocks.apply(init_weights)
        self.ups.apply(init_weights)
        for module in self.ups:
            init_weights(module[-1])
        for md in self.resblocks:
            init_weights(md)

    def forward(self, x: Tensor):
        x = self.conv_pre(x)
        for i in range(self.num_upsamples):
            x = self.activation(x)
            x = self.ups[i](x)
            xs = torch.zeros_like(x, device=x.device)
            for j in range(self.num_kernels):
                xs += self.resblocks[i * self.num_kernels + j](x)
            x = xs / self.num_kernels
        x = self.activation(x)

        x = self.reflection_pad(x)
        x = self.conv_post(x)
        spec = x[:, : self.post_n_fft // 2 + 1, :].exp()
        phase = x[:, self.post_n_fft // 2 + 1 :, :].sin()
        return spec, phase
