import torch
from torch import Tensor
from lt_utils.common import *
import torch.nn.functional as F
from lt_tensor.misc_utils import plot_view
from lt_utils.misc_utils import get_current_time


class TrainTracker:
    last_file = f"logs/history_{get_current_time()}.npy"
    loss_history: Dict[str, List[Number]] = {}
    lr_history: Dict[str, List[Number]] = {}
    data_history: Dict[str, List[Any]] = {}
    steps: int = 0
    epochs: int = 0

    def __init__(self):
        pass

    def add_lr(
        self,
        lr: Union[float, Tensor],
        key: str = "main",
    ):
        if key not in self.lr_history:
            self.lr_history[key] = []

        if isinstance(lr, Tensor):
            lr = lr.item()

        self.lr_history[key].append(lr)

    def add_loss(
        self,
        loss: Union[float, Tensor],
        key: str = "main",
    ):
        if key not in self.loss_history:
            self.loss_history[key] = []
        if isinstance(loss, Tensor):
            loss = loss.item()
        self.loss_history[key].append(float(loss))

    def add_data(
        self,
        value: Any,
        key: str = "main",
    ):
        if key not in self.data_history:
            self.data_history[key] = []
        self.data_history[key].append(value)

    @staticmethod
    def _mean(values: List[Number]) -> float:
        if not values:
            return float("nan")
        return sum(values) / len(values)

    def add_step_data(
        self,
        losses: Dict[str, Union[float, Tensor]] = {},
        lrs: Dict[str, float] = {},
        *,
        count_step: bool = True,
    ):
        if losses:
            for k, v in losses.items():
                self.add_loss(k, v)
        if lrs:
            for k, v in lrs.items():
                self.add_lr(k, v)
        if count_step:
            self.steps += 1

    def add_epoch(
        self,
        losses: List[Dict[str, Union[float, Tensor]]] = [],
        lrs: List[Dict[str, float]] = [],
    ):
        for loss_info in losses:
            self.add_step_data(losses=loss_info, count_step=False)
        for lr_info in lrs:
            self.add_step_data(lrs=lr_info, count_step=False)
        self.steps += max(len(losses), len(lrs))

    def get_lr_average(self, key: str = "main", total: int = 0):
        lr = self.get_learning_rates(key, total)
        return self._mean(lr)

    def get_loss_average(self, key: str = "main", total: int = 0):
        losses = self.get_losses(key, total)
        return self._mean(losses)

    def get_learning_rates(self, key: str = "train", total: int = 0):
        total = max(int(total), 0)
        results = self.lr_history.get(key, [])
        if total:
            return results[-total:]
        return results

    def get_losses(self, key: str = "main", total: int = 0):
        total = max(int(total), 0)
        results = self.loss_history.get(key, [])
        if total:
            return results[-total:]
        return results

    def state_dict(self):
        return {
            "loss": self.loss_history.copy(),
            "lr": self.lr_history.copy(),
            "data": self.data_history.copy(),
        }

    def save(self, path: Optional[PathLike] = None):
        from lt_utils.file_ops import save_pickle

        if path is None:
            path = f"logs/history_{get_current_time()}.npy"
        if not str(path).endswith(".npy"):
            path += ".npy"
        save_pickle(
            str(path),
            self.state_dict(),
        )
        self.last_file = str(path)

    def load(self, path: Optional[PathLike] = None):
        self.clear_all()
        from lt_utils.file_ops import load_pickle

        if path is None:
            path = self.last_file
        data = load_pickle(path, {})
        import numpy as np

        if isinstance(data, np.ndarray):
            data = data.tolist()
        self.loss_history = data.get("loss", {})
        self.lr_history = data.get("lr", {})
        self.data_history = data.get("data", {})
        self.last_file = str(path)

    def plot(
        self,
        dict_target: Dict[str, List[float]],
        keys: Union[str, List[str]],
        title: str,
        max_amount: int = 0,
        smoothing: Optional[Literal["ema", "avg"]] = None,
        alpha: float = 0.5,
        yaxis_title: str = "Y",
        xaxis_title: str = "X",
        *args,
        **kwargs,
    ):

        if max_amount > 0:
            fn = (
                lambda x: F.interpolate(
                    torch.tensor([x]).view(1, 1, len(x)),
                    size=max_amount,
                    mode="nearest",
                )
                .flatten()
                .tolist()
            )
        else:
            fn = lambda x: x
        max_amount = max(int(max_amount), 0)
        if smoothing:
            if "smoothing_alpha" in kwargs:
                alpha = kwargs.get("smoothing_alpha")
            if isinstance(smoothing, bool):
                smoothing = "ema"
        if not max_amount:
            max_amount = int(2**32 - 1)
        return plot_view(
            {k: fn(v) for k, v in dict_target.items() if k in keys},
            title,
            smoothing=smoothing,
            alpha=alpha,
            yaxis_title=yaxis_title,
            xaxis_title=xaxis_title,
        )

    def clear_all(self):
        self.lr_history.clear()
        self.loss_history.clear()
        self.data_history.clear()

    def plot_loss(
        self,
        keys: Optional[Union[str, List[str]]] = None,
        max_amount: int = 0,
        smoothing: Optional[Literal["ema", "avg"]] = None,
        alpha: float = 0.5,
        title: Optional[str] = None,
        xaxis_title: str = "Step/Epoch",
        yaxis_title: str = "Loss",
        **kwargs,
    ):
        if isinstance(keys, str):
            keys = [keys]
        if not keys:
            keys = [x for x in self.loss_history]
        return self.plot(
            dict_target=self.loss_history,
            keys=keys,
            title=title or keys[0],
            max_amount=max_amount,
            smoothing=smoothing,
            alpha=alpha,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            **kwargs,
        )

    def plot_lr(
        self,
        keys: Optional[Union[str, List[str]]] = None,
        max_amount: int = 0,
        smoothing: Optional[Literal["ema", "avg"]] = None,
        alpha: float = 0.5,
        title: Optional[str] = None,
        xaxis_title: str = "Step/Epoch",
        yaxis_title: str = "Learning Rate(s)",
        **kwargs,
    ):
        if isinstance(keys, str):
            keys = [keys]
        if not keys:
            keys = [x for x in self.lr_history]
        return self.plot(
            dict_target=self.lr_history,
            keys=keys,
            title=title or keys[0],
            max_amount=max_amount,
            smoothing=smoothing,
            alpha=alpha,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            **kwargs,
        )
