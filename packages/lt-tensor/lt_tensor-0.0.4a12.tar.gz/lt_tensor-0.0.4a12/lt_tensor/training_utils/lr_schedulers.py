import math
from lt_utils.common import *
from torch.optim import Optimizer
from typing_extensions import override
from torch.optim.lr_scheduler import LRScheduler
from torch import Tensor


class CustomLRSchedulerBase(LRScheduler):
    def __init__(
        self,
        optimizer: Optimizer,
        last_epoch: int = -1,
        floor_lr: float = 1e-7,
        ceil_lr: Optional[float] = None,
        initial_lr: Optional[float] = None,
        reset_cycle_gamma: float = 1.0,
    ):
        if initial_lr is not None:
            initial_lr = float(initial_lr)
            for p_group in self.optimizer.param_groups:
                if "initial_lr" in p_group and isinstance(
                    p_group["initial_lr"], Tensor
                ):
                    p_group["initial_lr"].fill_(initial_lr)
                else:
                    p_group["initial_lr"] = initial_lr

        self.disabled = False
        self.floor_lr = floor_lr
        self.reset_cycle_gamma = reset_cycle_gamma
        self.ceil_lr = ceil_lr

        super().__init__(optimizer, last_epoch)

    def clamp_lr(self, new_value: float):
        floor = max(new_value, self.floor_lr)
        if self.ceil_lr is None:
            return floor
        return min(floor, self.ceil_lr)

    def reset_lr(self):
        self.disabled = False
        base_lrs = []
        _last_lr = []
        for p_group in self.optimizer.param_groups:
            lr = p_group["initial_lr"] * self.reset_cycle_gamma
            p_group["initial_lr"] = lr
            p_group["lr"] = lr
            base_lrs.append(lr)
            _last_lr.append(lr)

        self.base_lrs = base_lrs.copy()
        self._last_lr = _last_lr.copy()

    @override
    def get_lr(self):
        return self._get_closed_form_lr()

    def _get_closed_form_lr(self) -> List[Union[float, Tensor]]:
        return [x["lr"] for x in self.optimizer.param_groups]


class WarmupDecayLR(CustomLRSchedulerBase):
    def __init__(
        self,
        optimizer: Optimizer,
        last_epoch: int = -1,
        warmup_steps: int = 128,
        floor_lr: float = 1e-7,
    ):
        self.warmup_steps = warmup_steps + (warmup_steps % 2)
        super().__init__(optimizer, last_epoch, floor_lr=floor_lr)

    @override
    def get_lr(self):
        if self.disabled:
            return [x["lr"] for x in self.optimizer.param_groups]
        if self.last_epoch >= self.warmup_steps:
            self.disabled = True
            return self.base_lrs

        lrs = []
        step = self.last_epoch + 1
        base = 1 + (-math.cos(math.pi * (step / self.warmup_steps)))
        for base_lr in self.base_lrs:
            lr = base_lr * 1.0 * base
            lrs.append(self.clamp_lr(lr))

        return lrs


class WarmupDecayWithResetsLR(CustomLRSchedulerBase):
    def __init__(
        self,
        optimizer: Optimizer,
        last_epoch: int = -1,
        warmup_steps: int = 128,
        total_resets: int = 3,
        target_lr: Optional[float] = None,
        floor_lr: float = 1e-7,
        fallback_speed: Union[int, float] = 2,
    ):
        self.warmup_steps = (warmup_steps + (warmup_steps % 2)) * 2
        self.current_resets = 0
        self.total_resets = int(max(total_resets, 1))
        self.on_reverse = False
        self.fallback_speed = fallback_speed
        self.target_lr = (
            target_lr if target_lr is not None else optimizer.param_groups[0]["lr"]
        )
        self.current_step = 1
        super().__init__(optimizer, last_epoch, floor_lr=floor_lr)
        self.ceil_lr = self.optimizer.param_groups[0]["initial_lr"]

    @override
    def get_lr(self):
        if self.disabled:
            return [x["lr"] for x in self.optimizer.param_groups]

        if self.current_resets >= self.total_resets:
            self.disabled = True
            return [self.target_lr for _ in range(len(self.optimizer.param_groups))]

        lrs = []
        if not self._is_initial:
            if self.on_reverse:
                self.current_step = max(self.current_step - self.fallback_speed, 0)
            else:
                self.current_step = min(self.current_step + 1, self.warmup_steps)

        step = self.current_step + 1

        base = 1 - math.cos(math.pi * (step / self.warmup_steps))
        for base_lr in self.base_lrs:
            lr = base_lr * base
            lrs.append(self.clamp_lr(lr))

        if not self._is_initial:
            if not self.on_reverse:
                if max(lrs) == self.ceil_lr:
                    self.on_reverse = True
                    self.current_resets += 1
            else:
                if min(lrs) == self.floor_lr:
                    self.on_reverse = False
        return lrs


class WaveDecayLR(CustomLRSchedulerBase):
    def __init__(
        self,
        optimizer: Optimizer,
        target_lr: float = 1e-5,
        floor_lr: float = 1e-7,
        ceil_lr: Optional[float] = None,
        decay_rate: float = 0.1,
        wave_amplitude: float = 0.1,
        period: int = 90,
        last_epoch: int = -1,
        damp: float = 0.1,
        wave_amp_decay: bool = False,
        disable_on_target: bool = False,
    ):
        assert decay_rate != 0.0, "decay_rate must be non-zero"

        self.target_lr = target_lr
        self.decay_rate = decay_rate
        self.decay_rate = decay_rate
        self.wave_amp_decay = wave_amp_decay
        self.wave_amplitude = wave_amplitude
        self.period = period
        self.damp = damp
        self.disable_on_target = disable_on_target
        super().__init__(optimizer, last_epoch, floor_lr=floor_lr, ceil_lr=ceil_lr)

    @override
    def get_lr(self):
        if self.disabled:
            return [x["lr"] for x in self.optimizer.param_groups]
        step = self.last_epoch + 1
        cycles = step / self.period
        t = step % self.period

        exp_cycle_decay = math.exp(-self.decay_rate * cycles)
        phase = 2 * math.pi * (self.damp + t / self.period)
        wave = math.sin(phase) * math.cos(phase)

        lrs = []
        centers = []
        for base in self.base_lrs:
            center = base * exp_cycle_decay
            centers.append(center)
            if self.wave_amp_decay:
                amp = self.wave_amplitude * max(center, self.target_lr)
            else:
                amp = self.wave_amplitude * base
            lr = center + amp * wave
            lrs.append(self.clamp_lr(lr))

        if self.disable_on_target:
            if min(centers) <= self.target_lr:
                self.disabled = True
                lrs = [max(self.target_lr, lr) for lr in lrs]

        return lrs
