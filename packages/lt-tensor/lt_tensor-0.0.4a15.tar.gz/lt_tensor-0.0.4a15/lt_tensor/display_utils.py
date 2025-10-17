import math
import torch
import warnings
import numpy as np
from io import BytesIO
from torch import Tensor
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


CMAP_TP: TypeAlias = Literal[
    "aggrnyl",
    "agsunset",
    "blackbody",
    "bluered",
    "blues",
    "blugrn",
    "bluyl",
    "brwnyl",
    "bugn",
    "bupu",
    "burg",
    "burgyl",
    "cividis",
    "darkmint",
    "electric",
    "emrld",
    "gnbu",
    "greens",
    "greys",
    "hot",
    "inferno",
    "jet",
    "magenta",
    "magma",
    "mint",
    "orrd",
    "oranges",
    "oryel",
    "peach",
    "pinkyl",
    "plasma",
    "plotly3",
    "pubu",
    "pubugn",
    "purd",
    "purp",
    "purples",
    "purpor",
    "rainbow",
    "rdbu",
    "rdpu",
    "redor",
    "reds",
    "sunset",
    "sunsetdark",
    "teal",
    "tealgrn",
    "turbo",
    "viridis",
    "ylgn",
    "ylgnbu",
    "ylorbr",
    "ylorrd",
    "algae",
    "amp",
    "deep",
    "dense",
    "gray",
    "haline",
    "ice",
    "matter",
    "solar",
    "speed",
    "tempo",
    "thermal",
    "turbid",
    "armyrose",
    "brbg",
    "earth",
    "fall",
    "geyser",
    "prgn",
    "piyg",
    "picnic",
    "portland",
    "puor",
    "rdgy",
    "rdylbu",
    "rdylgn",
    "spectral",
    "tealrose",
    "temps",
    "tropic",
    "balance",
    "curl",
    "delta",
    "oxy",
    "edge",
    "hsv",
    "icefire",
    "phase",
    "twilight",
    "mrybm",
    "mygbm",
]


def plot_token_heatmap_grid(
    tokens_ids: List[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    decoded_tokens: List[str] = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    token_scores: List[float] = [
        0.9206,
        0.911,
        0.7963,
        0.9423,
        0.2089,
        0.2474,
        0.9381,
        0.0112,
        0.8727,
        0.7906,
    ],
    c_map: CMAP_TP = "deep",
    n_cols: int = 5,
    title: str = "Token Heatmap",
    template="plotly_dark",
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
            colorscale=c_map,
            colorbar=dict(title="Score"),
        )
    )

    fig.update_layout(
        title=title,
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=False, autorange="reversed"),
        height=300 + n_rows * 30,
        template=template,
    )
    return fig


def get_image(
    image_tensor: Tensor,
    c_map: Optional[CMAP_TP] = None,
    width: Optional[Number] = None,
    height: Optional[Number] = None,
    title: Optional[str] = None,
    color_first: bool = True,
    return_plot: bool = False,
    template: Optional[Union[Literal["plotly_dark"]]] = None,
    scale_factor: Number = 1.0,
    x_axes_visible: bool = False,
    y_axes_visible: bool = False,
):
    import PIL.Image
    import plotly.express as px

    image_tensor = torch.as_tensor(image_tensor)

    image_tensor = image_tensor.clone().detach().cpu()
    if image_tensor.ndim == 4:
        # dont process batched
        image_tensor = image_tensor[0, ...]
    if color_first:
        image_tensor = image_tensor.permute(1, 2, 0)
    H, W, C = image_tensor.shape
    image_tensor = image_tensor.numpy(force=True)

    top_space = 2
    if isinstance(title, str):
        if not title.strip():
            title = None
        else:
            top_space = 48

    if width is None:
        width = W
    if height is None:
        height = H

    image = px.imshow(
        image_tensor,
        color_continuous_scale=c_map,
        title=title,
        width=width,
        height=height,
    )
    image.update_layout(
        width=width * scale_factor,
        height=height * scale_factor,
        margin={"l": 2, "r": 2, "t": top_space, "b": 2},
        template=template,
    )
    image.update_xaxes(visible=x_axes_visible)
    image.update_yaxes(visible=y_axes_visible)
    if return_plot:
        return image
    return PIL.Image.open(BytesIO(image.to_image()))


def show_spectrogram_multiple(
    audios: List[Tuple[str, Tensor]],
    sample_rate: int = 24000,
    n_fft: int = 1024,
    hop_length: int = 256,
    win_length: int = 1024,
    window: str | Any = "hann",
    size_fig: Number = 12,
    center: bool = True,
    height_factor: float = math.pi,
    force_close: bool = False,  # useful for application such as gradio
):
    import librosa
    import matplotlib.pyplot as plt

    y_size = size_fig / height_factor
    fig, axs = plt.subplots(
        len(audios),
        1,
        figsize=(size_fig, y_size),
    )

    def plot_spec(ax, y: Tensor, title: str):
        if isinstance(y, torch.Tensor):
            y = y.detach().flatten().cpu().numpy(force=True)
        spec = librosa.amplitude_to_db(
            np.abs(
                librosa.stft(
                    y,
                    n_fft=n_fft,
                    win_length=win_length,
                    window=window,
                    center=center,
                    hop_length=hop_length,
                )
            ),
            ref=np.max,
        )
        img = librosa.display.specshow(
            spec,
            sr=sample_rate,
            hop_length=hop_length,
            x_axis="time",
            y_axis="hz",
            ax=ax,
            cmap="viridis",
        )
        ax.set_title(title)
        fig.colorbar(img, ax=ax, format="%+2.0f dB")

    for i, (name, norm_audio) in enumerate(audios):
        plot_spec(axs[i], norm_audio, name)

    plt.tight_layout()
    if force_close:
        plt.close(fig)
    return fig


def show_spectrogram(
    audio: Tensor,
    sample_rate: int = 22050,
    n_fft: int = 1024,
    hop_length: int = 256,
    win_length: int = 1024,
    window: str | Any = "hann",
    size_fig: Number = 12,
    center: bool = True,
    c_map: Optional[CMAP_TP] = "viridis",
    height_factor: float = math.pi,
    force_close: bool = False,  # useful for application such as gradio
):
    import librosa
    import matplotlib.pyplot as plt

    y_size = size_fig / height_factor
    fig, axs = plt.subplots(
        1,
        1,
        figsize=(size_fig, y_size),
    )
    # -------------
    if isinstance(audio, torch.Tensor):
        audio = audio.clone().detach().flatten().cpu().numpy(force=True)
    spec = librosa.amplitude_to_db(
        np.abs(
            librosa.stft(
                audio,
                n_fft=n_fft,
                win_length=win_length,
                window=window,
                center=center,
                hop_length=hop_length,
            )
        ),
        ref=np.max,
    )
    img = librosa.display.specshow(
        spec,
        sr=sample_rate,
        hop_length=hop_length,
        x_axis="time",
        y_axis="hz",
        ax=axs,
        cmap=c_map,
    )
    axs.set_title("spetrogram")
    fig.colorbar(img, ax=axs, format="%+2.0f dB")
    # ----
    plt.tight_layout()
    if force_close:
        plt.close(fig)
    return fig


def show_tempogram(
    audio: Tensor,
    sample_rate: int = 24000,
    hop_length: int = 256,
    win_length: int = 1024,
    center: bool = True,
    size_fig: Number = 12,
    c_map: Optional[CMAP_TP] = "magma",
    height_factor: float = math.pi,
    force_close: bool = False,
):
    import librosa
    import matplotlib.pyplot as plt

    y_size = size_fig / height_factor
    if isinstance(audio, Tensor):
        audio_np = audio.clone().detach().flatten().cpu().numpy(force=True)
    else:
        audio_np = np.asarray(audio)

    onset_env = librosa.onset.onset_strength(
        y=audio_np, sr=sample_rate, hop_length=hop_length
    )
    tempogram_ref = librosa.feature.tempogram(
        onset_envelope=onset_env,
        sr=sample_rate,
        hop_length=hop_length,
        win_length=win_length,
        center=center,
    )
    # === Visualization ===
    fig, axs = plt.subplots(1, 1, figsize=(size_fig, y_size))
    librosa.display.specshow(
        tempogram_ref,
        sr=sample_rate,
        hop_length=hop_length,
        x_axis="time",
        y_axis="tempo",
        ax=axs,
        cmap=c_map,
    )
    axs.set_title("Tempogram")

    plt.tight_layout()
    if force_close:
        plt.close(fig)
    return fig
