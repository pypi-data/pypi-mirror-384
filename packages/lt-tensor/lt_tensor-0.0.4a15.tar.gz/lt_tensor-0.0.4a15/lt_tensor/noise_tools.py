from lt_utils.common import *
from lt_tensor.model_base import Model
import torch
from torch import nn, Tensor
import math
import random
from lt_tensor.misc_utils import set_seed
from torch.nn import functional as F


def add_gaussian_noise(x: Tensor, noise_level: float = 0.025) -> Tensor:
    noise = torch.randn_like(x) * noise_level
    return x + noise


def add_uniform_noise(x: Tensor, noise_level: float = 0.025) -> Tensor:
    noise = (torch.rand_like(x) - 0.5) * 2 * noise_level
    return x + noise


def add_linear_noise(x, noise_level=0.05) -> Tensor:
    T = x.shape[-1]
    ramp = torch.linspace(0, noise_level, T, device=x.device)
    for _ in range(x.dim() - 1):
        ramp = ramp.unsqueeze(0)
    return x + ramp.expand_as(x)


def add_impulse_noise(x: Tensor, noise_level: float = 0.025) -> Tensor:
    # For image inputs
    probs = torch.rand_like(x)
    x_clone = x.detach().clone()
    x_clone[probs < (noise_level / 2)] = 0.0  # salt
    x_clone[probs > (1 - noise_level / 2)] = 1.0  # pepper
    return x_clone


def add_pink_noise(x: Tensor, noise_level: float = 0.05) -> Tensor:
    # pink noise: divide freq spectrum by sqrt(f)
    if x.ndim == 3:
        x = x.view(-1, x.shape[-1])  # flatten to 2D [B*C, T]
    pink_noised = []

    for row in x:
        white = torch.randn_like(row)
        f = torch.fft.rfft(white)
        freqs = torch.fft.rfftfreq(row.numel(), d=1.0)
        freqs[0] = 1.0  # prevent div by 0
        f /= freqs.sqrt()
        pink = torch.fft.irfft(f, n=row.numel())
        pink_noised.append(pink.to(x.device))

    pink_noised = torch.stack(pink_noised, dim=0).view_as(x)
    return x + pink_noised * noise_level


def add_clipped_gaussian_noise(x: Tensor, noise_level: float = 0.025) -> Tensor:
    noise = torch.randn_like(x) * noise_level
    return torch.clamp(x + noise, 0.0, 1.0)


def add_multiplicative_noise(x: Tensor, noise_level: float = 0.025) -> Tensor:
    noise = 1 + torch.randn_like(x) * noise_level
    return x * noise


class NoiseScheduler(Model):
    """
    Diffusion-style noise scheduler for ε-prediction training.

    Returns (x_t, eps, t) for training, where
        x_t = sqrt(alpha_bar_t) * x0 + sqrt(1 - alpha_bar_t) * eps
    """

    def __init__(
        self,
        max_steps: int = 50,
        beta_start: float = 1e-4,
        beta_end: float = 0.05,
    ):
        super().__init__()
        self.scheduler_steps = max_steps

        # beta/alpha schedules
        betas = torch.linspace(beta_start, beta_end, max_steps)
        alphas = 1.0 - betas
        alpha_bars = torch.cumprod(alphas, dim=0)

        # register as buffers so .to(device) works automatically
        self.register_buffer("betas", betas)
        self.register_buffer("alphas", alphas)
        self.register_buffer("alpha_bars", alpha_bars)

    # ------------------------------------------------------------------ #
    # Core utilities
    # ------------------------------------------------------------------ #
    def _sample_timesteps(self, batch: int) -> Tensor:
        """Uniform random timestep per sample, shape (B,)"""
        return torch.randint(
            0, self.scheduler_steps, (batch,), device=self.device, dtype=torch.long
        )

    def q_sample(self, x0: Tensor, t: Tensor = None) -> tuple[Tensor, Tensor, Tensor]:
        """
        Forward diffusion: sample x_t and return (x_t, noise, t).
        x0 : clean waveform, shape (B, C, L)
        t  : optional LongTensor of shape (B,)
        """
        B = x0.size(0)
        if t is None:
            t = self._sample_timesteps(B)
        else:
            t = torch.as_tensor(t, dtype=torch.long, device=self.device)

        eps = torch.randn_like(x0)
        a_bar = self.alpha_bars[t].view(B, 1, 1)  # (B,1,1)
        x_t = a_bar.sqrt() * x0 + torch.sqrt(1.0 - a_bar) * eps
        return x_t, eps, t

    def loss(self, model: Model, x0: Tensor, cond: Tensor = None) -> Tensor:
        """
        DDPM ε-prediction loss.
        Samples x_t ~ q(x_t|x0) and computes MSE between
        predicted and true noise.
        """
        if not model.training:
            model.train()
        x_t, eps, t = self.q_sample(x0)  # x_t, ε, t
        eps_pred = model(x_t, t, cond)  # your net outputs ε̂
        return F.l1_loss(eps_pred, eps)

    @torch.no_grad()
    def p_sample(self, model: Model, x: Tensor, t: int, cond: Tensor = None) -> Tensor:
        """
        Single reverse step: x_{t-1} from x_t using predicted ε.
        """

        beta_t = self.betas[t]
        a_t = self.alphas[t]
        a_bar_t = self.alpha_bars[t]
        t = torch.as_tensor(t, dtype=torch.long, device=x.device).view(1, -1)

        eps_pred = model(x, t, cond.to(x.device))
        # torch.full((x.size(0),), t, device=model.device, dtype=torch.long)

        coef1 = 1.0 / torch.sqrt(a_t)
        coef2 = beta_t / torch.sqrt(1.0 - a_bar_t)
        mean = coef1 * (x - coef2 * eps_pred)
        if t > 0:
            noise = torch.randn_like(x)
            sigma = torch.sqrt(beta_t)
            return mean + (sigma * noise)
        else:
            return mean

    def sample(
        self,
        model: Model,
        cond: Optional[Tensor] = None,
        latent: Optional[Tensor] = None,
        hop_length: int = 256,
        steps: Optional[int] = None,
    ) -> Tensor:
        """
        Iteratively sample x_0 from pure noise.
        shape: (B, C, L)
        """
        assert (
            cond is not None or latent is not None
        ), "Either a condition should be given or a latent should be given."
        if steps is None:
            steps = self.scheduler_steps
        else:
            steps = int(min(self.scheduler_steps, steps))
        if hasattr(model, "device"):
            device = model.device
        else:
            device = self.device
            model.to(self.device)
        if model.training:
            model.eval()

        if latent is not None:
            x = latent.clone().to(device=device)
        else:
            x = torch.randn(1, 1, hop_length * cond.size(-1), device=device)

        for t in reversed(range(steps)):
            x = self.p_sample(model, x, t, cond)
        return x
