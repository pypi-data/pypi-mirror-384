__all__ = ["AttentionHead"]

from lt_utils.common import *
from lt_tensor.common import *

import torch.nn.functional as F
import math

TC: TypeAlias = Callable[[Any], Tensor]


def get_alibi_slopes(n_heads: int):
    """ALiBi slopes per head (from paper)."""

    def get_slopes_power_of_2(n):
        start = 2 ** (-(2 ** -(math.log2(n) - 3)))
        ratio = start
        return [start * ratio**i for i in range(n)]

    if math.log2(n_heads).is_integer():
        return torch.tensor(get_slopes_power_of_2(n_heads))
    else:
        closest_power_of_2 = 2 ** math.floor(math.log2(n_heads))
        return torch.tensor(
            get_slopes_power_of_2(closest_power_of_2)
            + get_alibi_slopes(2 * closest_power_of_2).tolist()[
                : n_heads - closest_power_of_2
            ]
        )


class RotaryEmbedding(nn.Module):
    def __init__(self, dim: int, base: int = 10000):
        """
        dim: head dimension (d_head)
        base: RoPE base frequency
        """
        super().__init__()
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)

    def forward(self, q: torch.Tensor, k: torch.Tensor, pos: int):
        """
        q, k: (B, nh, 1, hs)   -> only the last token
        pos: int, position index in sequence
        """
        t = torch.tensor([pos], dtype=self.inv_freq.dtype, device=q.device)  # [1]
        freqs = torch.einsum("i,j->ij", t, self.inv_freq)  # [1, hs/2]
        emb = torch.cat((freqs, freqs), dim=-1)  # [1, hs]

        cos = emb.cos()[None, None, :, :]  # (1, 1, 1, hs)
        sin = emb.sin()[None, None, :, :]  # (1, 1, 1, hs)

        def rotate(x):
            x1, x2 = x[..., ::2], x[..., 1::2]
            return torch.cat((-x2, x1), dim=-1)

        q = q * cos + rotate(q) * sin
        k = k * cos + rotate(k) * sin
        return q, k


class AttentionHead(nn.Module):
    def __init__(
        self,
        d_model: int,
        n_heads: int = 4,
        dropout: float = 0.1,
        bias: bool = True,
        std_init: float = 0.02,
        pos_encoding: Literal["absolute", "rope", "alibi"] = "rope",
        rope_base: int = 10000,
    ):
        super().__init__()
        assert d_model % n_heads == 0

        self.d_head = d_model // n_heads
        self.n_heads = n_heads
        self.d_embed = d_model
        self.pos_encoding = pos_encoding.lower()
        self.dropout = dropout

        # projections
        self.qkv_proj = nn.Linear(d_model, 3 * d_model, bias=bias)
        self.out_proj = nn.Linear(d_model, d_model, bias=bias)
        self.drop_layer = nn.Dropout(dropout)

        # init
        self._init_weights(std_init)

        # extras for RoPE / ALiBi
        if self.pos_encoding == "rope":
            self.rope = RotaryEmbedding(self.d_head, base=rope_base)

        elif self.pos_encoding == "alibi":
            slopes = get_alibi_slopes(self.n_heads)
            self.register_buffer("alibi_slopes", slopes, persistent=False)

    def _init_weights(self, std: float = 0.02):
        for pn, p in self.named_parameters():
            if "qkv_proj" in pn:
                nn.init.normal_(p, mean=0.0, std=std)

    def forward(self, x: torch.Tensor):
        B, T, C = x.shape

        # q, k, v projections
        q, k, v = self.qkv_proj(x).split(self.d_embed, dim=2)
        q = q.view(B, T, self.n_heads, self.d_head).transpose(1, 2)  # (B, nh, T, hs)
        k = k.view(B, T, self.n_heads, self.d_head).transpose(1, 2)
        v = v.view(B, T, self.n_heads, self.d_head).transpose(1, 2)

        # apply RoPE if needed
        if self.pos_encoding == "rope":
            q, k = self.rope(q, k, T)

        # build attn mask for ALiBi if needed
        attn_mask = None
        if self.pos_encoding == "alibi":
            pos_ids = torch.arange(T, device=x.device)
            # (nh, T)
            alibi = self.alibi_slopes[:, None] * pos_ids[None, :]
            # expand to (1, nh, T_q, T_k)
            attn_mask = alibi.unsqueeze(0).unsqueeze(2)

        # fused attention
        y = (
            F.scaled_dot_product_attention(
                q,
                k,
                v,
                attn_mask=attn_mask,
                dropout_p=self.dropout if self.training else 0.0,
                is_causal=True,
            )
            .transpose(1, 2)
            .contiguous()
            .view(B, T, C)
        )
        return self.drop_layer(self.out_proj(y))
