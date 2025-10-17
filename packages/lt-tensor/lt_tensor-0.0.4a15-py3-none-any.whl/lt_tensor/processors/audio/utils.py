__all__ = ["convert_to_16_bits"]
from lt_utils.common import *
from lt_tensor.common import *


def convert_to_16_bits(
    audio: Tensor,
    max_norm: bool = False,
    out_mode: Literal["default", "half", "short"] = "default",
):
    """Convert and audio from float32 to float16"""
    if audio.dtype in [torch.float16, torch.bfloat16]:
        return audio
    if max_norm:
        data = audio / audio.abs().max()
    else:
        data = audio
    data = data * 32767
    if out_mode == "short":
        return data.short()
    elif out_mode == "half":
        return data.half()
    return data
