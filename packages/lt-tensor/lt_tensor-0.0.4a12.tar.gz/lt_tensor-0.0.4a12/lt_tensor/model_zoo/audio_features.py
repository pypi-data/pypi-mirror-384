__all__ = ["JDCNet", "SineGen"]

from lt_utils.common import *
from lt_tensor.common import *
import torch.nn.functional as F
from lt_tensor.model_zoo.convs import ConvBase, is_conv
from lt_tensor.model_zoo.residual import PoolResBlock2D 


class JDCNet(ConvBase):
    """
    Implementation of model from:
    Kum et al. - "Joint Detection and Classification of Singing Voice Melody Using
    Convolutional Recurrent Neural Networks" (2019)
    Link: https://www.semanticscholar.org/paper/Joint-Detection-and-Classification-of-Singing-Voice-Kum-Nam/60a2ad4c7db43bace75805054603747fcd062c0d
    Joint Detection and Classification Network model for singing voice melody.
    """

    def __init__(
        self,
        num_classes: int = 722,
        n_mels: int = 80,
        d_model: int = 512,
        norm: Optional[Literal["weight_norm", "spectral_norm"]] = None,
    ):
        super().__init__()
        self.num_class = num_classes
        self.d_model = d_model
        self.n_mels = n_mels
        self.proj_in = nn.Conv1d(self.n_mels, 64, kernel_size=3, padding=1, bias=False)

        self.enc_conv_block = nn.Sequential(
            self.get_2d_conv(
                in_channels=1,
                out_channels=64,
                kernel_size=3,
                padding=1,
                bias=False,
                norm=norm,
            ),
            nn.BatchNorm2d(num_features=64),
            nn.LeakyReLU(0.1, inplace=True),
            self.get_2d_conv(64, 64, 3, padding=1, bias=False),
        )
        self.pool_residual = PoolResBlock2D(
            pool_features=256,
            pool_activation=nn.LeakyReLU(0.1, inplace=True),
            pool_kernel_size=(1, 4),
            resblock_activation=lambda: nn.LeakyReLU(0.1, inplace=True),
            residual_sizes=[(64, 128), (128, 192), (192, 256)],
            residual_dilation_sizes=[1, 1, 1],
            residual_hidden_sizes=[128, 192, 256],
            residual_kernel_sizes=[3, 3, 3],
            residual_pool_kernel_sizes=[
                (1, 2),
                (1, 2),
                (1, 2),
            ],
            dropout=0.0,
            norm=norm,
        )

        self.bi_net_classifier = nn.GRU(
            input_size=self.d_model,
            hidden_size=self.d_model // 2,
            batch_first=True,
            bidirectional=True,
        )  # (b, wt, 512)

        # input: (b, w*h, 512)
        self.classifier = nn.Linear(
            in_features=self.d_model, out_features=self.num_class
        )  # (b, h*w, num_class)

        # initialize weights
        self.apply(self._init_weights)

    def _classifier(self, enc_seq: Tensor, batch_size: int = 1) -> Tensor:
        self.bi_net_classifier.flatten_parameters()
        out_cls, _ = self.bi_net_classifier(enc_seq)
        output = self.classifier(out_cls.view((batch_size, -1, 512)))
        return output

    def forward(self, x: Tensor):
        """
        args:
            x: [B, n_mels, T]

        Returns:
            classification_prediction 'size: (B, T, n_classes)'
        """
        ###############################
        # forward pass for classifier #
        ###############################
        B = x.size(0)
        T = x.size(-1)
        x = self.proj_in(x)
        x = x.view(B, 1, -1, T)
        enc_block = self.enc_conv_block(x.transpose(-1, -2))
        enc = self.pool_residual(enc_block)
        enc_seq = enc.permute(0, 2, 1, 3).contiguous().view((B, -1, 512))
        classifier_out = self._classifier(enc_seq, B).view((B, T, self.num_class))

        return classifier_out.tanh()

    @staticmethod
    def _init_weights(m):
        if isinstance(m, nn.Linear):
            nn.init.kaiming_uniform_(m.weight)

        elif isinstance(m, nn.LSTM) or isinstance(m, nn.LSTMCell):
            for p in m.parameters():
                if p.data is None:
                    continue

                if len(p.shape) >= 2:
                    nn.init.orthogonal_(p.data)
                else:
                    nn.init.normal_(p.data)

        elif is_conv(m):
            nn.init.xavier_normal_(m.weight)
            if m.bias is not None:
                nn.init.zeros_(m.bias)


class SineGen(Model):

    def __init__(
        self,
        sample_rate: int = 24000,
        upscale_rate: int = 9,
        harmonic_num: int = 8,
        sine_amp: float = 0.1,
        noise_std: float = 0.003,
        voiced_threshold: float = 10,
    ):
        super().__init__()
        self.sine_amp = sine_amp
        self.noise_std = noise_std
        self.harmonic_num = harmonic_num
        self.sample_rate = sample_rate
        self.upscale_rate = upscale_rate
        self.voiced_threshold = voiced_threshold
        self.register_buffer(
            "hum", torch.arange(1, self.harmonic_num + 1, dtype=torch.float32)
        )

    def __call__(self, *args, **kwds) -> Tensor:
        return super().__call__(*args, **kwds)

    def forward(self, f0: Tensor):
        f0 = f0 * self.hum

        rad_values = (f0 / self.sample_rate) % 1

        rand_ini = torch.randn(f0.size(0), f0.size(-1), device=f0.device)
        rand_ini[:, 0] = 0
        rad_values[:, 0, :] = rad_values[:, 0, :] + rand_ini
        sine_waves = (
            F.interpolate(
                rad_values.transpose(1, 2),
                scale_factor=1 / self.upscale_rate,
                mode="linear",
            )
            .transpose(1, 2)
            .sin()
        )
        uv = (f0 > self.voiced_threshold).to(dtype=torch.float32)
        noise_amp = uv * self.noise_std + (1 - uv) * self.sine_amp / 3
        noise = torch.randn_like(sine_waves)
        proj = sine_waves * uv + (noise * noise_amp)
        return dict(
            sine=proj,
            noise=noise,
            uv=uv,
            noise_amp=noise_amp,
        )
