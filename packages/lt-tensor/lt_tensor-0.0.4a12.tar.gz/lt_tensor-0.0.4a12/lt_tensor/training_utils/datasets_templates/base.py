from lt_utils.common import *
from lt_tensor.common import *
import random
import copy
from lt_tensor.misc_utils import set_seed
from lt_tensor.tensor_ops import is_tensor, move_dict_to_device, move_list_to_device
from torch.utils.data import Dataset, DataLoader, random_split
from abc import ABC, abstractmethod

ANY_BATCH_CONTENT: TypeAlias = Union[
    Tensor, Any, Dict[str, Union[Tensor, Any]], Sequence[Union[Tensor, Any]]
]
ANY_BATCH: TypeAlias = Sequence[Union[Tensor, Sequence[ANY_BATCH_CONTENT]]]


class DatasetLoaderHelper(Dataset):
    data: List[ANY_BATCH_CONTENT] = []

    def __init__(self, data: List[Tensor], do_shuffle: bool = True):
        super().__init__()
        try:
            self.data = copy.deepcopy(data)
        except:
            self.data = data
        if do_shuffle:
            for _ in range(5):
                random.shuffle(self.data)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index: int):
        return self.data[index]


class DatasetBase(DatasetLoaderHelper, ABC):
    data: List[ANY_BATCH_CONTENT] = []

    def __init__(self, data: List[Tensor] = [], do_shuffle: bool = True):
        super().__init__(data, do_shuffle)

    def move_data_to_device(self, device: Union[str, torch.device], max_depth: int = 3):
        self.data = move_list_to_device(
            self.data,
            device=device,
            max_depth=max_depth,
        )

    def sample(self, seed: Optional[int] = None):
        total = len(self)
        if not total:
            raise RuntimeError("The dataset is empty!")
        item_ids: List[int] = torch.arange(0, total).tolist()
        if seed is not None:
            set_seed(seed)
        idx = random.choice(item_ids)
        return self.__getitem__(idx)

    def samples(
        self,
        number: int = 1,
        auto_adjust: bool = False,
        seed: Optional[int] = None,
        randomized: bool = True,
    ):
        total = len(self)
        if not total:
            raise RuntimeError("The dataset is empty!")
        number = int(max(number, 1))

        if total < number:
            if not auto_adjust:
                raise RuntimeError(
                    f"The dataset does not contain {number} of items available. It only has {len(self.data)}."
                )
            number = total
        items_ids: List[int] = torch.arange(0, total).tolist()
        if not randomized:
            item_ids = items_ids[:number]
        else:
            if seed is not None:
                set_seed(seed)
            item_ids = random.sample(items_ids, k=number)
        return [self.__getitem__(i) for i in item_ids]

    def collate_fn(self, batch: ANY_BATCH) -> ANY_BATCH_CONTENT:
        """This is very generic, you must override this function to a proper one for your project."""
        if all([is_tensor(x) for x in batch]):
            largest_total = max([x.size(-1) for x in batch])
            return torch.stack(
                [F.pad(x, pad=(0, largest_total - x.size(-1))) for x in batch], dim=0
            )
        raise ValueError("Cannot handle non-tensor sequences!")

    def get_dataloader(
        self,
        train_batch_size: int = 1,
        eval_batch_size: int = 1,
        train_shuffle: bool = True,
        eval_shuffle: bool = False,
        eval_ratio: float = 0.0,
        seed: Optional[int] = None,
        total_items: Optional[int] = None,
        num_workers: int = 0,
        collate_fn: Optional[Callable[[ANY_BATCH], ANY_BATCH_CONTENT]] = None,
        **kwargs,
    ) -> Tuple[DataLoader, Optional[DataLoader]]:
        total = len(self)
        if not total:
            raise RuntimeError("The dataset is empty!")
        if total_items is not None:
            total = min(total, max(total_items, 1))
        eval_size = 0
        train_size = total
        if eval_ratio > 0:
            if total < 10:
                raise RuntimeError(
                    "Not enough data to create an eval split. It will require at least 10 items."
                )
            eval_ratio = min(0.5, eval_ratio)

            eval_size = max(int(total * eval_ratio), 1)
            train_size = total - eval_size

        sampled_data = self.samples(
            total, randomized=train_shuffle and eval_shuffle, seed=seed
        )
        dataset = DatasetLoaderHelper(sampled_data, train_shuffle and eval_shuffle)
        if collate_fn is None:
            collate_fn = self.collate_fn
        if eval_size:
            generator = None
            if seed is not None:
                set_seed(seed)
                generator = torch.Generator().manual_seed(seed)
            train_set, val_set = random_split(
                dataset,
                [train_size, eval_size],
                generator=generator,
            )
            train_loader = DataLoader(
                train_set,
                batch_size=train_batch_size,
                shuffle=train_shuffle,
                num_workers=num_workers,
                collate_fn=collate_fn,
            )
            val_loader = DataLoader(
                val_set,
                batch_size=eval_batch_size,
                shuffle=eval_shuffle,
                num_workers=num_workers,
                collate_fn=collate_fn,
            )
            return train_loader, val_loader

        return (
            DataLoader(
                dataset,
                batch_size=train_batch_size,
                shuffle=train_shuffle,
                num_workers=num_workers,
                collate_fn=self.collate_fn,
            ),
            None,
        )

    def __bool__(self):
        return bool(self.data)
