__all__ = ["FilterDiscriminator"]
from lt_utils.common import *
from lt_tensor.common import *

from lt_tensor.model_zoo.convs import ConvBase
from lt_tensor.model_zoo import BidirectionalConv
from lt_tensor.processors.audio.misc import BandFilter


class FilterDiscriminator(ConvBase):
    """This is an unfinished work, but seems to work in parts at least."""

    def __init__(
        self,
        hidden_dim: int = 128,
        sr: Number = 24000,
        q_factors: List[float] = [0.3673, 1.1539, 3.6249],
        central_freq: List[float] = [4.1416, 32.0062, 1225.0787],
        gain: List[float] = [6.25, 12.5, 25.0],
        eps: float = 1e-5,
        noise_csg: List[bool] = [False, False, True],
        filter_requires_grad: bool = True,
        filter_gain_requires_grad: bool = True,
        types_fn: List[
            Literal[
                "band",
                "lowpass",
                "highpass",
                "allpass",
                "bandpass",
                "bandreject",
                "bass",
                "treble",
                "equalizer",
            ]
        ] = ["highpass", "lowpass", "equalizer"],
        bi_conv_dilation_fwd: int = 1,
        bi_conv_dilation_bwd: int = 1,
        seed: Optional[int] = None,
    ) -> None:
        super().__init__(seed=seed)
        self.bn_models = nn.ModuleList()
        filter_kw = dict(
            sr=sr,
            eps=eps,
            requires_grad=filter_requires_grad,
            gain_requires_grad=filter_gain_requires_grad,
        )
        self.activ = nn.LeakyReLU()
        for q, cf, gn, noise, tp in zip(
            q_factors, central_freq, gain, noise_csg, types_fn
        ):
            self.bn_models.append(
                nn.ModuleDict(
                    dict(
                        fn=BandFilter(
                            type_fn=tp,
                            q_factor=q,
                            central_freq=cf,
                            gain=gn,
                            noise_csg=noise,
                            **filter_kw,
                        ),
                        conv=nn.Conv1d(
                            1,
                            16,
                            kernel_size=3,
                            padding=1,
                            bias=False,
                        ),
                    )
                )
            )

        layers = len(self.bn_models)

        self.bi_conv2d = BidirectionalConv(
            in_channels=16,
            out_channels=layers,
            kernel_size=7,
            dilation=bi_conv_dilation_fwd,
            dilation_bwd=bi_conv_dilation_bwd,
            padding=(7 - 1) * bi_conv_dilation_fwd // 2,
            padding_bwd=(7 - 1) * bi_conv_dilation_bwd // 2,
            return_tuple=True,
        )
        self.process = nn.ModuleList(
            [
                nn.Sequential(
                    nn.LeakyReLU(0.2),
                    nn.Conv2d(layers * 2, hidden_dim, 3, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.ConvTranspose2d(hidden_dim, hidden_dim, 4, 2, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.MaxPool2d(2),
                ),
                nn.Sequential(
                    nn.LeakyReLU(0.2),
                    nn.Conv2d(hidden_dim, hidden_dim, 3, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.ConvTranspose2d(hidden_dim, hidden_dim, 4, 2, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.MaxPool2d(2),
                ),
                nn.Sequential(
                    nn.LeakyReLU(0.2),
                    nn.Conv2d(hidden_dim, hidden_dim, 3, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.ConvTranspose2d(hidden_dim, hidden_dim // 2, 4, 2, padding=1),
                    nn.LeakyReLU(0.2),
                    nn.MaxPool2d(2),
                ),
                nn.Sequential(
                    nn.LeakyReLU(0.2),
                    nn.Conv2d(hidden_dim // 2, 1, 3, padding=1),
                    nn.MaxPool2d(1, 2),
                    nn.Flatten(-2, -1),
                    nn.LeakyReLU(0.2),
                    nn.Conv1d(1, 1, 3, padding=1),
                ),
            ]
        )

    def pass_proc_layers(self, ct: Tensor):
        for i, P in enumerate(self.process):
            ct = P(ct)
        return ct

    def pass_encoder_layers(self, x: Tensor):
        data = []
        for i, C in enumerate(self.bn_models):
            u = C["conv"](C["fn"](x))
            data.append(u)
        return torch.cat(data, dim=-1)

    def generator_loss(self, inputs: Tensor):
        res = self(inputs)
        return torch.mean((res - 1.0) ** 2)

    def discriminator_loss(
        self,
        inputs: Tensor,
        labels: Tensor,
    ):
        fake = self.train_step(inputs.clone().detach())
        real = self.train_step(labels)
        loss_real = torch.mean((real - 1.0) ** 2)
        loss_fake = torch.mean(fake**2)
        return loss_real, loss_fake

    def forward(self, x: Tensor):
        data_bn = self.pass_encoder_layers(x)
        bi_conv = torch.cat(self.bi_conv2d(data_bn), dim=1)

        # expand to 2D
        B, C, T = bi_conv.shape
        bi_conv = bi_conv.view(B, C, 1, T)
        out = self.pass_proc_layers(bi_conv)
        return out
