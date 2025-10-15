__all__ = ["TokenizerWP"]
from lt_utils.file_ops import (
    is_path_valid,
    find_files,
    is_pathlike,
    save_json,
    load_json,
)
from lt_utils.common import *
import torch
from torch import Tensor
from functools import lru_cache
from torch.nn import functional as F


from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.implementations import ByteLevelBPETokenizer

from .utils import get_phonetic_tokens, get_default_tokens
from lt_utils.misc_utils import updateDict


def get_special_tokens():
    return {
        "pad": "<pad>",
        "unk": "<unk>",
        "sep": "<sep>",
        "bos": "<s>",
        "eos": "</s>",
        "mask": "<mask>",
        "cls": "<cls>",
    }


class TokenizerWP:

    @property
    def vocab_size(self):
        return self.tokenizer.get_vocab_size()

    @property
    def vocab(self):
        return self.tokenizer.get_vocab()

    def __init__(
        self,
        tokenizer_or_file: Union[Tokenizer, str, Path],
        special_tokens: Optional[Dict[str, str]] = None,
        save_location: Optional[Union[str, Path]] = None,
        use_default_decoder=False,
    ):
        self.unk_text = ""
        self.pad_token_id = 999
        self.use_default_decoder = use_default_decoder
        if isinstance(tokenizer_or_file, (str, Path)):
            self.load_from_file(tokenizer_or_file)
            save_location = None
        else:
            self.tokenizer: Tokenizer = tokenizer_or_file
            self._post_process_setup(special_tokens)

        if save_location is not None:
            self.save_tokenizer(save_location)

    def __len__(self):
        return self.vocab_size

    def _setup_special_tokens(self, pad="<pad>", unk="<unk>", **kwargs):
        self.special_tokens: Dict[
            str, Union[Dict[str, Optional[Union[str, int]]], List[int]]
        ] = {"data": {}, "ids": [], "pad_id": self.vocab_size - 1}
        # resets the ids
        kwargs.update({"pad": pad, "unk": unk})
        for nm, tk in kwargs.items():
            current = self.tokenizer.token_to_id(tk)
            if current is None:
                if nm == "pad":
                    self.tokenizer.add_special_tokens([tk])
                    current = self.tokenizer.token_to_id(tk)

            if nm == "pad":
                self.pad_token_id = current
                self.special_tokens["pad_id"] = current
            elif nm == "unk":
                self.unk_text = tk

            att_name = f"{nm}_token"
            self.special_tokens["data"][att_name] = {
                "id": current,
                "text": tk,
            }
            if current is not None:
                self.special_tokens["ids"].append(current)
        self._dec_id.cache_clear()

    def reset_decoder_cache(self):
        self._dec_id.cache_clear()

    def token_to_id(self, token: str) -> int:
        return self.tokenizer.token_to_id(token)

    def id_to_token(self, token: int) -> str:
        return self.tokenizer.id_to_token(token)

    def encode(
        self,
        texts: Union[str, List[str]],
        padding: bool = False,
        truncation: Union[bool, str, None] = None,
        max_size: Optional[int] = None,
        truncation_direction: Literal["left", "right"] = "left",
        padding_from: Literal["left", "right"] = "right",
    ) -> Union[Tensor, List[Tensor]]:
        assert isinstance(texts, (str, list, tuple)) and texts
        _kw_unit = dict(
            max_size=max_size if truncation else None,
            truncation=truncation_direction,
        )
        if isinstance(texts, str):
            result = self._encode_unit(texts, **_kw_unit)
            if max_size and padding:
                return self.pad(
                    [result], from_left=padding_from == "left", to_size=max_size
                )
            return result.view(1, result.shape[-1])
        # else:
        B = len(texts)
        tokens = [self._encode_unit(x, **_kw_unit) for x in texts]

        if padding:
            return self.pad(tokens, from_left=padding_from == "left", to_size=max_size)
        return tokens

    def decode(
        self,
        tokenized: Union[int, list[Tensor], List[int], Tensor],
        return_special_tokens: bool = False,
    ):
        B = 1
        tok_kwargs = dict(return_special_tokens=return_special_tokens)

        if isinstance(tokenized, Tensor):
            if tokenized.ndim > 1:
                B = tokenized.shape[0]
        elif isinstance(tokenized, int):
            return self.id_to_token(tokenized)
        elif isinstance(tokenized, (list, tuple)):
            if not tokenized:
                return ""
            if isinstance(tokenized[0], Tensor):
                assert all(
                    list(map(lambda x: isinstance(x, Tensor), tokenized))
                ), "Not all items provided in the list is a valid tensor"
                B = len(tokenized)
                if B == 1:
                    tokenized = tokenized[0]
            else:
                assert all(
                    list(map(lambda x: isinstance(x, int), tokenized))
                ), "Not all items provided in the list is a valid token"

        if B == 1:
            return self._decode(tokenized, **tok_kwargs)
        return [self._decode(tokenized[i], **tok_kwargs) for i in range(B)]

    def pad(
        self,
        input_ids: list[Tensor],
        from_left: bool = False,
        to_size: Optional[int] = None,
    ):
        assert input_ids, "No value has been provided!"
        if len(input_ids) > 1:
            largest_text = max([x.size(-1) for x in input_ids])
            if to_size:
                largest_text = max(largest_text, to_size)
            if from_left:
                fn = lambda x: (largest_text - x.size(-1), 0)
            else:
                fn = lambda x: (0, largest_text - x.size(-1))
        else:
            if not to_size or to_size <= input_ids[0].shape[-1]:
                return input_ids[0].view(1, input_ids[0].shape[-1])
            if from_left:
                fn = lambda x: (to_size - x.size(-1), 0)
            else:
                fn = lambda x: (0, to_size - x.size(-1))
            return F.pad(
                input_ids[0],
                pad=fn(input_ids[0]),
                mode="constant",
                value=self.pad_token_id,
            ).view(1, to_size)
        B = len(input_ids)
        return torch.stack(
            [
                F.pad(
                    x,
                    pad=fn(x),
                    mode="constant",
                    value=self.pad_token_id,
                )
                for x in input_ids
            ],
            dim=0,
        ).view(B, largest_text)

    def _encode_output_processor(self, output: List[int]):
        return torch.tensor([output], dtype=torch.long)

    @lru_cache(maxsize=65536)
    def _dec_id(self, token: int, return_special_tokens: bool = False):
        if token in self.special_tokens["ids"]:
            if not return_special_tokens:
                return ""
            return self.id_to_token(token) or self.unk_text

        return self.id_to_token(token) or (
            self.unk_text if return_special_tokens else ""
        )

    def _encode_unit(
        self,
        text: str,
        max_size: Optional[int] = None,
        truncation: Literal["left", "right"] = "left",
        **kwargs,
    ):
        tokens = self.tokenizer.encode(text, add_special_tokens=False).ids
        _length = len(tokens)
        if max_size is not None:
            if truncation and _length > max_size:
                if truncation == "left":
                    tokens = tokens[-max_size:]
        return torch.tensor([tokens], dtype=torch.long)

    def _decode(
        self,
        tokens: Union[List[int], Tensor],
        return_special_tokens: bool = False,
    ):
        if isinstance(tokens, Tensor):
            tokens = tokens.flatten().tolist()
        if self.use_default_decoder:
            return self.tokenizer.decode(tokens, skip_special_tokens=not return_special_tokens)
        return "".join(
            [
                self._dec_id(tok, return_special_tokens)
                for tok in tokens
                if isinstance(tok, int)
            ]
        )

    def _post_process_setup(self, special_tokens: Optional[Dict[str, str]] = None):
        self._dec_vocab = {
            value: txt for txt, value in self.tokenizer.get_vocab().items()
        }
        if isinstance(special_tokens, dict) and special_tokens:
            if (
                "pad_id" in special_tokens
                and "data" in special_tokens
                and "ids" in special_tokens
            ):
                self.special_tokens = special_tokens.copy()
                self.pad_token_id = self.special_tokens["data"]["pad_token"]["id"]
                self.unk_text = (
                    self.special_tokens["data"]
                    .get("unk_token", {})
                    .get("text", "<unk>")
                )
            else:
                self._setup_special_tokens(**special_tokens)
        self._dec_id.cache_clear()

    def load_from_file(self, path: Union[str, Path]):
        is_path_valid(path, validate=True)
        path = Path(path)
        if path.is_file():
            path = path.parent
        tokenizer_file = "tokenizer.json"
        special_token_map_file = "special_token_map.json"
        config_file = "tokenizer_config.json"
        self.tokenizer = Tokenizer.from_file(str(path / tokenizer_file))
        special_tokens = load_json(path / special_token_map_file, {})
        settings = load_json(path / config_file, {})
        self.use_default_decoder = settings.get("use_default_decoder", False)
        self._post_process_setup(special_tokens)

    def save_tokenizer(self, path: Union[str, Path]):
        is_pathlike(path, check_if_empty=False, validate=True)
        path = Path(path)
        if "." in path.name:
            path = path.parent
        path.mkdir(exist_ok=True, parents=True)
        self.tokenizer.save(str(path / "tokenizer.json"))
        save_json(
            str(path / "tokenizer_config.json"),
            {"use_default_decoder": self.use_default_decoder},
        )
        save_json(path / "special_token_map.json", self.special_tokens)

    @classmethod
    def create_tokenizer_a(
        cls,
        tokens: List[str] = get_default_tokens(),
        merges: List[str] = [],
        reserved_tokens: int = 0,
        save_location: Optional[Union[str, Path]] = None,
        special_tokens: Dict[str, str] = {
            "pad": "<pad>",
            "unk": "<unk>",
        },
        byte_fallback=False,
        use_default_decoder: bool = False,
    ):
        vocab = {}
        for i, token in enumerate(tokens):
            vocab[token] = i

        if reserved_tokens:
            base = len(vocab)
            for i in range(base, base + reserved_tokens):
                vocab[f"<|reserved_{i-base}|>"] = i

        tokenizer = Tokenizer(
            BPE(vocab=vocab, merges=merges, byte_fallback=byte_fallback)
        )
        return cls(tokenizer, special_tokens, save_location, use_default_decoder)

    @classmethod
    def create_tokenizer_b(
        cls,
        tokens: List[str] = get_default_tokens(),
        merges: List[str] = [],
        reserved_tokens: int = 0,
        save_location: Optional[Union[str, Path]] = None,
        special_tokens: Dict[str, str] = {
            "pad": "<pad>",
            "unk": "<unk>",
        },
        add_prefix_space: bool = False,
        lowercase: bool = False,
        dropout: Optional[float] = None,
        unicode_normalizer: Optional[str] = None,
        continuing_subword_prefix: Optional[str] = None,
        end_of_word_suffix: Optional[str] = None,
        trim_offsets: bool = False,
        use_default_decoder: bool = False,
    ):
        vocab = {}
        for i, token in enumerate(tokens):
            vocab[token] = i

        if reserved_tokens:
            base = len(vocab)
            for i in range(base, base + reserved_tokens):
                vocab[f"<|reserved_{i-base}|>"] = i

        tokenizer = ByteLevelBPETokenizer(
            vocab=vocab,
            merges=merges,
            add_prefix_space=add_prefix_space,
            lowercase=lowercase,
            dropout=dropout,
            unicode_normalizer=unicode_normalizer,
            continuing_subword_prefix=continuing_subword_prefix,
            end_of_word_suffix=end_of_word_suffix,
            trim_offsets=trim_offsets,
        )
        return cls(tokenizer, special_tokens, save_location, use_default_decoder)
