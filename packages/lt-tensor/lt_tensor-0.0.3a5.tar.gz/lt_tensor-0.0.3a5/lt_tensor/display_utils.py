import torch
import warnings
import numpy as np

from torch import Tensor
import warnings
import numpy as np
from lt_utils.common import *
from lt_tensor.tensor_ops import to_torch_tensor, to_numpy_array


def time_weighted_avg(data: Union[Tensor, np.ndarray], alpha: float = 0.9) -> Tensor:
    """
    Compute time-weighted moving average for smoothing.
    Args:
        data: [T] or [N, T] tensor (time series)
        alpha: smoothing factor (0 < alpha < 1), higher = smoother
    Returns:
        smoothed tensor of same shape
    """
    data = to_torch_tensor(data).squeeze()
    if data.ndim == 1:
        out = torch.zeros_like(data)
        out[0] = data[0]
        for t in range(1, len(data)):
            out[t] = alpha * out[t - 1] + (1 - alpha) * data[t]
        return out
    elif data.ndim == 2:
        out = torch.zeros_like(data)
        out[:, 0] = data[:, 0]
        for t in range(1, data.shape[1]):
            out[:, t] = alpha * out[:, t - 1] + (1 - alpha) * data[:, t]
        return out
    else:
        raise ValueError("Data must be 1D or 2D time series")


def time_weighted_ema(data: Union[Tensor, np.ndarray], alpha: float = 0.5):
    """
    Compute the time-weighted Exponential Moving Average (EMA) for a given data array.

    Parameters:
    - data: array-like, the input data to smooth.
    - alpha: float, the smoothing factor (0 < alpha ≤ 1). Higher alpha discounts older observations faster.

    Returns:
    - ema: numpy array, the smoothed data.
    """
    data = to_numpy_array(data)
    ema = np.zeros_like(data)
    alpha = min(max(float(alpha), 0.00001), 0.99999)
    ema[0] = data[0]  # Initialize with the first data point
    for t in range(1, len(data)):
        ema[t] = alpha * data[t] + alpha * ema[t - 1]
    return ema


def plot_view(
    data: Dict[str, List[Any]],
    title: str = "Loss",
    xaxis_title="Step/Epoch",
    yaxis_title="Loss",
    template="plotly_dark",
    smoothing: Optional[Literal["ema", "avg"]] = None,
    alpha: float = 0.5,
    *args,
    **kwargs,
):
    try:
        import plotly.graph_objs as go
    except ModuleNotFoundError:
        warnings.warn(
            "No installation of plotly was found. To use it use 'pip install plotly' and restart this application!"
        )
        return
    fig = go.Figure()
    for mode, values in data.items():
        if values:
            if not smoothing:
                items = values
            elif smoothing == "avg":
                items = time_weighted_avg(values, kwargs.get("smoothing_alpha", alpha))
            else:
                items = time_weighted_ema(values, kwargs.get("smoothing_alpha", alpha))
            fig.add_trace(go.Scatter(y=items, name=mode.capitalize()))
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template=template,
    )
    return fig


def plot_token_heatmap_grid(
    tokens_ids: List[int],
    decoded_tokens: List[str],
    token_scores: List[float],
    n_cols: int = 8,
    title: str = "Token Heatmap",
):
    import math
    from plotly import graph_objects as go

    n_tokens = len(tokens_ids)
    n_rows = math.ceil(n_tokens / n_cols)

    # Pad so grid is rectangular
    pad_size = n_rows * n_cols - n_tokens
    tokens_ids = tokens_ids + [None] * pad_size
    decoded_tokens = decoded_tokens + [""] * pad_size
    token_scores = token_scores + [np.nan] * pad_size

    # Reshape into grid
    ids_grid = np.array(tokens_ids).reshape(n_rows, n_cols)
    txts_grid = np.array(decoded_tokens).reshape(n_rows, n_cols)
    scores_grid = np.array(token_scores).reshape(n_rows, n_cols)

    # Build hover text
    hover_grid = np.empty_like(txts_grid, dtype=object)
    for i in range(n_rows):
        for j in range(n_cols):
            if ids_grid[i, j] is None:
                hover_grid[i, j] = ""
            else:
                hover_grid[i, j] = (
                    f"Token: {txts_grid[i, j]}<br>"
                    f"ID: {ids_grid[i, j]}<br>"
                    f"Score: {scores_grid[i, j]:.4f}"
                )

    # Create heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=scores_grid,
            text=txts_grid,  # show tokens in cells
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverinfo="text",
            customdata=hover_grid,
            hovertemplate="%{customdata}<extra></extra>",
            colorscale="RdBu",
            colorbar=dict(title="Score"),
        )
    )

    fig.update_layout(
        title=title,
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False, autorange="reversed"),
        height=300 + n_rows * 30,
    )
    return fig
