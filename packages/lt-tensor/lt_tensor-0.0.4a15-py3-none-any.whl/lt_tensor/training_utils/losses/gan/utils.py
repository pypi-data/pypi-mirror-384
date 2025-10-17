import torch
from torch import Tensor
from lt_utils.common import *
from torch.nn import functional as F


def discriminator_loss_lsgan(
    d_real: Tensor,
    d_fake: Tensor,
    lambda_loss_real: float = 1.0,
    lambda_loss_fake: float = 1.0,
):
    """LSGAN discriminator loss"""
    loss_real = torch.mean((d_real - 1.0) ** 2) * lambda_loss_real
    loss_fake = torch.mean(d_fake**2) * lambda_loss_fake
    return loss_real + loss_fake


def generator_loss_lsgan(d_fake: Tensor, lambda_loss: float = 1.0):
    """LSGAN generator loss"""
    return torch.mean((d_fake - 1.0) ** 2) * lambda_loss


def feature_matching_loss(
    feats_real: List[Tensor], feats_fake: List[Tensor], lambda_loss: float = 1.0
):
    loss = 0
    for rf, ff in zip(feats_real, feats_fake):
        loss += torch.mean(torch.abs(rf - ff)) * lambda_loss
    return loss


def discriminator_loss_bce(
    d_real: Tensor,
    d_fake: Tensor,
    lambda_loss_real: float = 1.0,
    lambda_loss_fake: float = 1.0,
):
    """Compares real and fakes with `0` and `1`"""
    real_loss = (
        F.binary_cross_entropy_with_logits(d_real, torch.ones_like(d_real))
        * lambda_loss_real
    )
    fake_loss = (
        F.binary_cross_entropy_with_logits(d_fake, torch.zeros_like(d_fake))
        * lambda_loss_fake
    )
    return real_loss + fake_loss


def generator_loss_bce(d_fake: Tensor):
    return F.binary_cross_entropy_with_logits(d_fake, torch.ones_like(d_fake))
