from lt_utils.common import *
from lt_tensor.common import *
import warnings
import math
from torch.nn import functional as F
from lt_tensor.misc_utils import is_fused_available
from lt_tensor.model_zoo.transformer.attention import *
from lt_tensor.model_zoo.transformer.logits_processors import (
    LogitsProcessorList,
    TemperatureLogitsProcessor,
    TopPLogitsProcessor,
    TopKLogitsProcessor,
    BanTokensLogitsProcessor,
    RepetitionPenaltyLogitsProcessor,
)

TC: TypeAlias = Callable[[Any], Tensor]


class GPTConfig(ModelConfig):
    vocab_size: int
    max_seq_len: int = 2048
    d_model: int = 768
    n_head: int = 8
    n_layer: int = 8
    dropout: int = 0.1
    attention_bias: bool = True
    pos_encoding: Literal["absolute", "rope", "alibi"] = "alibi"
    rope_base: int = 10000
    extended_mlp_settings: Dict[str, List[Union[int, float]]] = dict(
        hidden=[768, 256, 1560], strength=[0.75, 0.5, 1.0]
    )
    use_extended_mlp: bool = False
    decoder_mlp_version: Literal["swiglu", "gelu"] = "gelu"
    layer_norm_bias: bool = False

    def __init__(
        self,
        vocab_size: int,
        max_seq_len: int = 2048,
        d_model: int = 768,
        n_head: int = 8,
        n_layer: int = 8,
        dropout: float = 0.1,
        attention_bias: bool = True,
        pos_encoding: Literal["absolute", "rope", "alibi"] = "alibi",
        rope_base: int = 10000,
        decoder_mlp_version: Literal["swiglu", "gelu"] = "gelu",
        use_extended_mlp: bool = False,
        extended_mlp_settings: Dict[str, List[Union[int, float]]] = dict(
            d_hidden=[768, 256, 1560],
            strength=[0.75, 0.5, 1.0],
            dropout=[0.2, 0.1, 0.01],
        ),
        layer_norm_bias: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(
            vocab_size=vocab_size,
            max_seq_len=max_seq_len,
            d_model=d_model,
            n_head=n_head,
            n_layer=n_layer,
            dropout=dropout,
            attention_bias=attention_bias,
            pos_encoding=pos_encoding,
            rope_base=rope_base,
            use_extended_mlp=use_extended_mlp,
            extended_mlp_settings=extended_mlp_settings,
            decoder_mlp_version=decoder_mlp_version,
            layer_norm_bias=layer_norm_bias,
        )


class LayerNorm(nn.Module):
    def __init__(
        self,
        d_model: int,
        bias: bool = False,
        eps: float = 1e-5,
        init_bias_eps: float = 0.0,
    ):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d_model), requires_grad=True)
        self.eps = eps
        if bias:
            self.bias = nn.Parameter(
                torch.zeros(d_model) + init_bias_eps, requires_grad=True
            )
        else:
            self.register_parameter("bias", None)

    def forward(self, input):
        return F.layer_norm(
            input,
            normalized_shape=self.weight.shape,
            weight=self.weight,
            bias=self.bias,
            eps=self.eps,
        )


class MLP(Model):
    def __init__(self, d_model: int, d_hidden: int, dropout: float = 0.1):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(d_model, d_hidden),
            nn.GELU(),
            nn.Linear(d_hidden, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.mlp(x)


class SwiGLU(Model):
    def __init__(self, d_model: int, d_hidden: int, dropout: float = 0.1):
        super().__init__()
        self.w1 = nn.Linear(d_model, d_hidden)
        self.w2 = nn.Linear(d_model, d_hidden)
        self.w3 = nn.Linear(d_hidden, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        return self.dropout(self.w3(F.silu(self.w1(x)) * self.w2(x)))


class ExpandableMLP(Model):
    def __init__(
        self,
        d_model: int,
        d_hidden: List[int],
        dropout: List[float],
        strength: List[float],
        decoder_mlp_version: Literal["swiglu", "gelu"] = "gelu",
    ):
        super().__init__()
        self.layers = nn.ModuleList()
        self.strength = strength
        for d_h, dp in zip(d_hidden, dropout):
            if decoder_mlp_version == "gelu":
                self.layers.append(MLP(d_model=d_model, d_hidden=d_h, dropout=dp))
            else:
                self.layers.append(SwiGLU(d_model=d_model, d_hidden=d_h, dropout=dp))
        self.total_layers = len(self.layers)

    def freeze_layer_by_id(self, idx: int):
        for param in self.layers[idx].parameters():
            param.requires_grad_(False)

    def unfreeze_layer_by_id(self, idx: int):
        for param in self.layers[idx].parameters():
            param.requires_grad_(True)

    def forward(self, x: Tensor) -> Tensor:
        for i, layer in enumerate(self.layers, 1):
            residual = x
            x = layer(x)
            x = residual + (x * self.strength[i - 1])
        return x


class DecoderLayer(nn.Module):
    def __init__(
        self,
        cfg: GPTConfig,
        attn_std: float = 0.02,
    ):
        super().__init__()
        self.ln1 = LayerNorm(cfg.d_model, bias=cfg.layer_norm_bias)
        self.attn = AttentionHead(
            d_model=cfg.d_model,
            n_heads=cfg.n_head,
            dropout=cfg.dropout,
            bias=cfg.attention_bias,
            std_init=attn_std,
            pos_encoding=cfg.pos_encoding,
            rope_base=cfg.rope_base,
        )

        self.ln2 = LayerNorm(cfg.d_model, bias=cfg.layer_norm_bias)
        if cfg.use_extended_mlp:
            self.mlp = ExpandableMLP(
                cfg.d_model,
                **cfg.extended_mlp_settings,
                decoder_mlp_version=cfg.decoder_mlp_version,
            )
        else:
            if cfg.decoder_mlp_version == "gelu":
                self.mlp = MLP(cfg.d_model, int(cfg.d_model * 4), cfg.dropout)
            else:
                self.mlp = SwiGLU(cfg.d_model, int(cfg.d_model * 4), cfg.dropout)

        # place holder weights []:
        self.ph_sta = nn.Identity()
        self.ph_mid = nn.Identity()
        self.ph_fin = nn.Identity()

    def forward(self, x, output_attentions=False):
        outputs = {
            "hidden_states": None,
            "attention": None,
        }
        residual = x
        x = self.ph_sta(x)
        x_ln = self.ln1(x)

        attn_out = self.attn(x_ln)
        if output_attentions:
            outputs["attention"] = attn_out

        x = residual + attn_out
        x = self.ph_mid(x)

        residual = x
        x = self.ln2(x)

        x = residual + self.mlp(x)

        x = self.ph_fin(x)
        outputs["hidden_states"] = x

        return outputs


class GPTModel(Model):
    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.cfg = cfg

        self.d_embed = cfg.d_model
        self.max_seq_len = cfg.max_seq_len
        self.vocab_size = cfg.vocab_size
        self.dropout = cfg.dropout
        self.n_heads = cfg.n_head
        self.n_layers = cfg.n_layer
        self.pos_encoding = cfg.pos_encoding

        # token embeddings
        self.wte = nn.Embedding(cfg.vocab_size, cfg.d_model)

        # position embeddings only if absolute
        if self.pos_encoding == "absolute":
            self.wpe = nn.Embedding(cfg.max_seq_len, cfg.d_model)
        else:
            self.wpe = None  # disabled for RoPE / ALiBi

        attn_std = 0.02 / math.sqrt(2 * cfg.n_layer)
        self.blocks = nn.ModuleList(
            [
                DecoderLayer(
                    cfg,
                    attn_std=attn_std,
                )
                for _ in range(cfg.n_layer)
            ]
        )
        self.ln_f = nn.LayerNorm(cfg.d_model)

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(
        self,
        input_ids: Optional[torch.LongTensor] = None,
        inputs_embeds: Optional[Tensor] = None,
        position_ids: Optional[Tensor] = None,
        past_key_values: Optional[Tensor] = None,
        use_cache: bool = False,
        output_hidden_states: bool = False,
        output_attentions: bool = False,
    ):
        if inputs_embeds is None:
            inputs_embeds = self.wte(input_ids)
        if inputs_embeds.ndim > 3:
            inputs_embeds = inputs_embeds.squeeze(1)
        B, T = inputs_embeds.shape[:2]

        if self.pos_encoding == "absolute":
            if position_ids is None:
                position_ids = (
                    torch.arange(T, device=inputs_embeds.device)
                    .unsqueeze(0)
                    .expand(B, T)
                )
            pos_emb = self.wpe(position_ids)
            hidden_states = inputs_embeds + pos_emb
        else:
            # rope / alibi: no pos_emb outside
            hidden_states = inputs_embeds

        outputs = {"last_hidden_state": None, "hidden_states": [], "states": []}
        for i, block in enumerate(self.blocks):
            if output_hidden_states:
                outputs["hidden_states"].append(hidden_states)

            past = past_key_values[i] if past_key_values is not None else None
            block_out = block.forward(hidden_states, output_attentions)

            hidden_states = block_out.pop("hidden_states", hidden_states)
            if output_hidden_states:
                outputs["hidden_states"].append(hidden_states)
            if any([output_attentions, output_hidden_states, use_cache]):
                outputs["states"].append(block_out)

        last_hidden_state = self.ln_f(hidden_states)
        outputs["last_hidden_state"] = last_hidden_state
        if output_hidden_states:
            outputs["hidden_states"].append(last_hidden_state)

        return outputs


class GPTLMHead(Model):
    def __init__(
        self,
        config: Union[GPTConfig, Dict[str, Any]],
    ):
        super().__init__()
        if not isinstance(config, GPTConfig):
            config = GPTConfig(**config)
        self.cfg = config
        self.transformer = GPTModel(cfg=self.cfg)
        self.lm_head = nn.Linear(self.cfg.d_model, self.cfg.vocab_size, bias=False)

    def forward(
        self,
        input_ids: Optional[torch.LongTensor] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[Tuple[Tuple[Tensor, Tensor]]] = None,
        use_cache: bool = False,
        output_hidden_states: bool = False,
        output_attentions: bool = False,
        return_dict: bool = False,
    ):
        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("Specify either input_ids or inputs_embeds, not both.")

        outputs = self.transformer.forward(
            input_ids,
            inputs_embeds=inputs_embeds,
            position_ids=position_ids,
            past_key_values=past_key_values,
            use_cache=use_cache,
            output_hidden_states=output_hidden_states,
            output_attentions=output_attentions,
        )
        logits = self.lm_head(outputs["last_hidden_state"])
        if not return_dict:
            return logits
        outputs["logits"] = logits
        return outputs

    @torch.no_grad()
    def get_next_token(
        self,
        input_ids: torch.LongTensor,
        logits_proc: LogitsProcessorList = LogitsProcessorList(),
        multinomial: bool = False,
        return_scores: bool = False,
        return_next_input: bool = False,
        max_token_to_keep: Optional[int] = None,
    ):
        if max_token_to_keep is None:
            max_token_to_keep = self.max_tokens - 2

        logits = self.inference(input_ids.to(device=self.device))
        scores = logits_proc(input_ids, logits[:, -1, :]).softmax(-1)

        if multinomial:
            next_token = torch.multinomial(scores, 1)
        else:
            next_token = torch.argmax(scores, dim=-1, keepdim=True)

        outputs = {"next_token": next_token.item()}
        if return_scores:
            outputs["scores"] = scores
        if return_next_input:
            outputs["next"] = torch.cat(
                (
                    input_ids[..., -max_token_to_keep:].to(self.device),
                    next_token.to(self.device),
                ),
                dim=1,
            )
        return outputs

    def generate(
        self,
        input_ids: Tensor,
        max_new_tokens: int = 64,
        do_sample: bool = False,
        temperature: float = 1.0,
        top_k: int = 0,
        top_p: float = 1.0,
        repetition_penalty: float = 1.0,
        return_prompt: bool = False,
        ban_token_ids: Optional[List[int]] = None,
        stop_tokens: List[int] = [],
        stream: bool = False,
        **kwargs,
    ):
        kw = dict(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=do_sample,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            return_prompt=return_prompt,
            ban_token_ids=ban_token_ids,
            stop_tokens=stop_tokens,
            repetition_penalty=repetition_penalty,
        )
        kw.update(kwargs)
        if stream:
            return self._generate(**kw)  # returns the generator object
        else:
            response = []
            for resp in self._generate(**kw):
                response.append(resp)
            return response

    def _generate(
        self,
        input_ids: Tensor,
        max_new_tokens: int = 64,
        do_sample: bool = False,
        temperature: float = 1.0,
        top_k: int = 0,
        top_p: float = 1.0,
        repetition_penalty: float = 1.0,
        return_prompt: bool = False,
        ban_token_ids: Optional[List[int]] = None,
        stop_tokens: List[int] = [],
        **kwargs,
    ):
        current_seq = input_ids.clone().to(device=self.device)
        if return_prompt:
            yield input_ids
        # sampling check
        _keep_tokens = self.cfg.max_seq_len - 2

        if do_sample:

            logits_proc = LogitsProcessorList(
                [
                    BanTokensLogitsProcessor(ban_token_ids),
                    TemperatureLogitsProcessor(temperature),
                    RepetitionPenaltyLogitsProcessor(repetition_penalty),
                    TopKLogitsProcessor(
                        top_k=top_k,
                        min_tokens_to_keep=kwargs.get("top_k_min_to_keep", 1),
                    ),
                    TopPLogitsProcessor(
                        top_p=top_p,
                        min_tokens_to_keep=kwargs.get("top_p_min_to_keep", 1),
                    ),
                ]
            )
        else:
            logits_proc = LogitsProcessorList()

        for _ in range(max_new_tokens):
            response = self.get_next_token(
                input_ids=current_seq,
                logits_proc=logits_proc,
                multinomial=do_sample,
                return_scores=False,
                return_next_input=True,
                max_token_to_keep=_keep_tokens,
            )
            next_token = response["next_token"]
            current_seq = response["next"]
            yield next_token
            if next_token in stop_tokens:
                break

    def get_optimizer(
        self,
        weight_decay: float = 0.1,
        learning_rate: float = 1e-3,
        betas: Tuple = (0.9, 0.999),
        verbose: bool = True,
    ) -> optim.AdamW:
        decay_params = []
        no_decay_params = []
        for param in self.parameters():
            if not param.requires_grad:
                continue
            if param.ndim < 2:
                no_decay_params.append(param)
            else:
                decay_params.append(param)
        optim_groups = [
            {"params": decay_params, "weight_decay": weight_decay},
            {"params": no_decay_params, "weight_decay": 0.0},
        ]
        if verbose:
            num_decay_params = format(
                sum(p.numel() for p in decay_params), ","
            ).replace(",", ".")
            num_no_decay_params = format(
                sum(p.numel() for p in no_decay_params), ","
            ).replace(",", ".")
            print(
                f"num decayed parameter tensors: {len(decay_params)}, with {num_decay_params} parameters"
            )
            print(
                f"num non-decayed parameter tensors: {len(no_decay_params)}, with {num_no_decay_params} parameters"
            )
        kwargs = dict()
        if is_fused_available() and self.device.type == "cuda":
            kwargs["fused"] = True

        optimizer = optim.AdamW(optim_groups, lr=learning_rate, betas=betas, **kwargs)
        return optimizer

    def save_weights(
        self,
        path,
        optimizer: optim.AdamW,
        step: int = 0,
        epoch: int = 0,
        train_losses: List[float] = [],
        eval_losses: List[float] = [],
    ):
        torch.save(
            {
                "model": self.state_dict(),
                "optimizer": optimizer.state_dict(),
                "step": step,
                "epoch": epoch,
                "train_losses": train_losses,
                "eval_losses": eval_losses,
            },
            path,
        )

    def _save_weights(
        self,
        path: Union[Path, str],
        replace: bool = False,
    ):
        super().save_weights(path=path, replace=replace)

    def _load_weights(
        self,
        path: Union[Path, str],
        raise_if_not_exists: bool = False,
        strict: bool = False,
        assign: bool = False,
        weights_only: bool = False,
        mmap: Optional[bool] = None,
        **pickle_load_args,
    ):
        return super().load_weights(
            path_or_state_dict=path,
            raise_if_not_exists=raise_if_not_exists,
            strict=strict,
            assign=assign,
            weights_only=weights_only,
            mmap=mmap,
            **pickle_load_args,
        )

    def load_weights(
        self,
        path,
        optimizer: optim.AdamW,
        strict=False,
        assign=False,
        weights_only=False,
    ):
        from lt_utils.file_ops import is_file

        step = 0
        epoch = 0
        train_losses = []
        eval_losses = []
        if is_file(path, False):
            try:
                past_state = torch.load(path, weights_only=weights_only)
                if "model" in past_state:
                    self.load_state_dict(
                        past_state["model"], strict=strict, assign=assign
                    )
                if "optimizer" in past_state:
                    optimizer.load_state_dict(past_state["optimizer"])
                step = past_state.get("step", 0)
                epoch = past_state.get("epoch", 0)
                train_losses = past_state.get("train_losses", [])
                eval_losses = past_state.get("eval_losses", [])
            except:
                pass
        return optimizer, step, epoch, train_losses, eval_losses
