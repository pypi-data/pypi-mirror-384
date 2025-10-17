import torch
from torch import Tensor
from lt_utils.common import *
from torch.nn import functional as F
from lt_tensor.tensor_ops import normalize_minmax


def contrastive_loss(x1: Tensor, x2: Tensor, label: Tensor, margin: float = 1.0):
    # label == 1: similar, label == 0: dissimilar
    dist = F.pairwise_distance(x1, x2)
    loss = label * dist**2 + (1 - label) * torch.clamp(margin - dist, min=0.0) ** 2
    return loss.mean()


def normalized_l1(
    input: Tensor, target: Tensor, min_floor: float = 0.0, max_ceil: float = 255
) -> Tensor:
    target = normalize_minmax(target.view_as(input), min_floor, max_ceil)
    input = normalize_minmax(input, min_floor, max_ceil)
    return F.l1_loss(input, target)


def normalized_mse(
    input: Tensor,
    target: Tensor,
    min_floor: float = 0.0,
    max_ceil: float = 255,
) -> Tensor:
    target = normalize_minmax(target.view_as(input), min_floor, max_ceil)
    input = normalize_minmax(input, min_floor, max_ceil)
    return F.mse_loss(input, target)


def normalized_any(
    input: Tensor,
    target: Tensor,
    loss_fn: Callable[[Tensor, Tensor], Tensor],
    min_floor: float = 0.0,
    max_ceil: float = 255,
) -> Tensor:
    target = normalize_minmax(target.view_as(input), min_floor, max_ceil)
    input = normalize_minmax(input, min_floor, max_ceil)
    return loss_fn(input, target)


def cos_sim_loss(inp: Tensor, tgt: Tensor) -> Tensor:
    return 1.0 - F.cosine_similarity(inp, tgt).mean().abs()


def masked_cross_entropy(
    logits: torch.Tensor,  # [B, T, V]
    targets: torch.Tensor,  # [B, T]
    lengths: torch.Tensor,  # [B]
    reduction: str = "mean",
) -> torch.Tensor:
    """
    CrossEntropyLoss with masking for variable-length sequences.
    - logits: unnormalized scores [B, T, V]
    - targets: ground truth indices [B, T]
    - lengths: actual sequence lengths [B]
    """
    B, T, V = logits.size()
    logits = logits.view(-1, V)
    targets = targets.view(-1)

    # Create mask
    mask = torch.arange(T, device=lengths.device).expand(B, T) < lengths.unsqueeze(1)
    mask = mask.reshape(-1)

    # Apply CE only where mask == True
    loss = F.cross_entropy(
        logits[mask], targets[mask], reduction="mean" if reduction == "mean" else "none"
    )
    if reduction == "none":
        return loss
    return loss
