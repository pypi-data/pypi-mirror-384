__all__ = ["MultiPeriodDiscriminator", "MPDConfig", "MultiPeriodDiscriminator"]
from lt_utils.common import *


from lt_tensor.common import F, torch, Tensor, nn, Model, ModelConfig
from lt_tensor.model_zoo.convs import ConvBase

# Typing helpers
TP_C1_O1: TypeAlias = Callable[[Tensor], Tensor]  #  modules related
TP_C2_O1: TypeAlias = Callable[[Tensor, Tensor], Tensor]  # loss related


def ch_size_lambda(multiplier: float):
    """Helps to resize channels in a fast manner."""
    return lambda x: max(int(x * multiplier), 1)


class MPDConfig(ModelConfig):
    def __init__(
        self,
        mpd_reshapes: list[int] = [2, 3, 5, 7, 11],
        kernels: list[int] = [1, 6, 3, 8, 3],
        strides: list[int] = [4, 2, 4, 2, 4],
        dilations: list[int] = [1, 4, 1, 4, 1],
        post_dilations: list[int] = [1, 2, 2, 2, 1],
        groups: list[int] = [1, 2, 2, 2, 1],
        scales: list[int] = [1.25, 0.75, 1.0, 0.75, 1.25],
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = "weight_norm",
        *args,
        **kwargs
    ):
        super().__init__(
            mpd_reshapes=mpd_reshapes,
            kernels=kernels,
            strides=strides,
            groups=groups,
            scales=scales,
            norm=norm,
            dilations=dilations,
            post_dilations=post_dilations,
        )


class PeriodDiscriminator(ConvBase):
    def __init__(
        self,
        period: int,
        discriminator_channel_multi: Number = 1,
        kernel_size: int = 5,
        stride: int = 3,
        dilation: int = 1,
        post_dilation: int = 1,
        groups: int = 1,
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = "weight_norm",
        loss_fn: TP_C2_O1 = nn.L1Loss(),
    ):
        super().__init__()
        self.period = period
        ch_m = ch_size_lambda(discriminator_channel_multi)
        _sec_dil = dilation // 2 + 1
        kwargs_cnns = dict(
            kernel_size=(kernel_size, 1),
            stride=(stride, 1),
            dilation=(dilation, _sec_dil),
            padding=(
                self.get_padding(kernel_size, dilation),
                self.get_padding(1, _sec_dil),
            ),
            norm=norm,
        )
        self.loss_fn = loss_fn
        self.activation = nn.LeakyReLU(0.1)
        self.convs = nn.ModuleList(
            [
                self.get_2d_conv(1, ch_m(32), **kwargs_cnns),
                nn.Sequential(
                    self.activation,
                    self.get_2d_conv(ch_m(32), ch_m(128), **kwargs_cnns, groups=groups),
                ),
                nn.Sequential(
                    self.activation,
                    self.get_2d_conv(
                        ch_m(128), ch_m(512), **kwargs_cnns, groups=groups
                    ),
                ),
                nn.Sequential(
                    self.activation,
                    self.get_2d_conv(
                        ch_m(512), ch_m(1024), **kwargs_cnns, groups=groups
                    ),
                ),
            ]
        )
        self.convs.append(
            nn.Sequential(
                self.activation,
                self.get_2d_conv(
                    ch_m(1024),
                    ch_m(1024),
                    kernel_size=(kernel_size, 1),
                    dilation=_sec_dil,
                    padding=(
                        self.get_padding(kernel_size, _sec_dil),
                        self.get_padding(1, _sec_dil),
                    ),
                ),
            )
        )

        self.conv_post: TP_C1_O1 = self.get_2d_conv(
            ch_m(1024),
            1,
            (3, 1),
            dilation=post_dilation,
            padding=(
                self.get_padding(3, post_dilation),
                self.get_padding(1, post_dilation),
            ),
            norm=norm,
        )
        self.activation = nn.LeakyReLU(0.1)

    def _forward(
        self,
        x: Tensor,
        current_fake: bool = False,
        step_type: Literal["discriminator", "generator"] = "discriminator",
    ) -> Union[Tensor, List[Tensor], Tuple[List[Tensor], Tensor]]:
        if step_type == "generator":
            feat_map = []

        # 1d to 2d [unchanged from original]
        b, c, t = x.shape
        if t % self.period != 0:  # pad first
            n_pad = self.period - (t % self.period)
            x = F.pad(x, (0, n_pad), "reflect")
            t = t + n_pad
        x = x.view(b, c, t // self.period, self.period)

        for l in self.convs:
            x = l(x)
            if step_type == "generator":
                feat_map.append(x)
        x = self.conv_post(x).flatten(1, -1)

        if step_type == "generator":
            feat_map.append(x)
            if current_fake:
                return feat_map, torch.mean((1.0 - x) ** 2)
            return feat_map

        if current_fake:  # lsquare loss for discriminator
            return torch.mean(x**2)
        return torch.mean((1.0 - x) ** 2)

    def _compute_feature_loss(self, feat_gen: List[Tensor], feat_disc: List[Tensor]):
        loss = 0.0
        for fg, fd in zip(feat_gen, feat_disc):
            loss += torch.mean(torch.abs(fd - fg))
        return loss

    def forward(
        self,
        generated: Tensor,
        target: Tensor,
        step_type: Literal["discriminator", "generator"] = "discriminator",
    ):
        if step_type == "discriminator":
            r_loss: Tensor = self._forward(target, False, "discriminator")
            g_loss: Tensor = self._forward(generated.detach(), True, "discriminator")
            return r_loss + g_loss

        with torch.no_grad():
            tgt_feat: List[Tensor] = self._forward(target, False, "generator")
        gen_feat, gen_loss = self._forward(generated, True, "generator")
        feature_loss = self._compute_feature_loss(gen_feat, tgt_feat)
        return gen_loss, feature_loss


class MultiPeriodDiscriminator(Model):
    def __init__(self, cfg: MPDConfig = MPDConfig()):
        super().__init__()
        self.cfg = cfg if isinstance(cfg, MPDConfig) else MPDConfig(**cfg)
        self.discriminators: List[PeriodDiscriminator] = nn.ModuleList(
            [
                PeriodDiscriminator(
                    mp,
                    kernel_size=ks,
                    stride=st,
                    dilation=dl,
                    norm=self.cfg.norm,
                    discriminator_channel_multi=sc,
                    groups=gp,
                    post_dilation=pdl,
                )
                for (mp, ks, st, gp, sc, dl, pdl) in (
                    zip(
                        self.cfg.mpd_reshapes,
                        self.cfg.kernels,
                        self.cfg.strides,
                        self.cfg.groups,
                        self.cfg.scales,
                        self.cfg.dilations,
                        self.cfg.post_dilations,
                    )
                )
            ]
        )
        self.init_weights(
            base_norm_type="normal",
            small_norm_type="zeros",
            base_norm_kwargs={"mean": 0.0, "std": 0.03},
        )

    def forward(
        self,
        generated: Tensor,
        target: Tensor,
        step_type: Literal["discriminator", "generator"] = "discriminator",
    ):
        loss_gen = 0.0
        loss_features = 0.0
        loss_disc = 0.0
        for md in self.discriminators:
            losses = md.forward(generated, target, step_type)
            if step_type == "discriminator":
                loss_disc += losses
            else:
                loss_gen += losses[0]
                loss_features += losses[1]
        if step_type == "discriminator":
            return loss_disc
        return loss_gen, loss_features
