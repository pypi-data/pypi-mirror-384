# Copyright © 2023-2024 Apple Inc.

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import mlx.core as mx
import mlx.nn as nn
import math
import numpy as np

# Import from nested llm_common structure using relative imports
from .llm_common.base import (
    BaseModelArgs,
    create_attention_mask,
    scaled_dot_product_attention,
)
from .llm_common.rope_utils import initialize_rope


@dataclass
class VisionConfig:
    hidden_size: int = 1024
    intermediate_size: int = 4096
    num_heads: int = 16
    num_hidden_layers: int = 24
    patch_size: int = 16
    temporal_patch_size: int = 2
    in_channels: int = 3
    hidden_act: str = "gelu"
    spatial_merge_size: int = 2
    out_hidden_size: int = 2560
    num_position_embeddings: int = 2304
    deepstack_visual_indexes: List[int] = None

    def __post_init__(self):
        if self.deepstack_visual_indexes is None:
            self.deepstack_visual_indexes = [3, 7, 11]


@dataclass
class TextConfig(BaseModelArgs):
    model_type: str = "qwen3vl"
    hidden_size: int = 2560
    num_hidden_layers: int = 36
    intermediate_size: int = 9728
    num_attention_heads: int = 32
    num_key_value_heads: int = 8
    rms_norm_eps: float = 1e-6
    vocab_size: int = 151936
    max_position_embeddings: int = 32768
    rope_theta: float = 10000.0
    head_dim: int = 128
    tie_word_embeddings: bool = True
    attention_bias: bool = False
    attention_dropout: float = 0.0
    rope_scaling: Optional[Dict[str, Union[float, str]]] = None

    def __post_init__(self):
        if self.rope_scaling is None:
            # Use default RoPE for now since MRoPE is not implemented in rope_utils
            self.rope_scaling = None


@dataclass
class ModelArgs(BaseModelArgs):
    vision_config: VisionConfig = None
    text_config: TextConfig = None
    image_token_id: int = 151655
    vision_start_token_id: int = 151652
    vision_end_token_id: int = 151653

    def __post_init__(self):
        if self.vision_config is None:
            self.vision_config = VisionConfig()
        if self.text_config is None:
            self.text_config = TextConfig()


def rotate_half(x):
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return mx.concatenate([-x2, x1], axis=-1)


def apply_rotary_pos_emb_vision(q, k, cos, sin):
    cos = mx.expand_dims(cos, axis=-2)
    sin = mx.expand_dims(sin, axis=-2)
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


def apply_rotary_pos_emb(q, k, cos, sin, unsqueeze_dim=1):
    cos = mx.expand_dims(cos, axis=unsqueeze_dim)
    sin = mx.expand_dims(sin, axis=unsqueeze_dim)
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


class VisionMLP(nn.Module):
    def __init__(self, config: VisionConfig):
        super().__init__()
        self.hidden_size = config.hidden_size
        self.intermediate_size = config.intermediate_size
        self.linear_fc1 = nn.Linear(self.hidden_size, self.intermediate_size, bias=True)
        self.linear_fc2 = nn.Linear(self.intermediate_size, self.hidden_size, bias=True)

    def __call__(self, hidden_state):
        return self.linear_fc2(nn.gelu(self.linear_fc1(hidden_state)))


class VisionPatchEmbed(nn.Module):
    def __init__(self, config: VisionConfig):
        super().__init__()
        self.patch_size = config.patch_size
        self.temporal_patch_size = config.temporal_patch_size
        self.in_channels = config.in_channels
        self.embed_dim = config.hidden_size

        kernel_size = [self.temporal_patch_size, self.patch_size, self.patch_size]
        self.proj = nn.Conv3d(
            self.in_channels, self.embed_dim, kernel_size=kernel_size, stride=kernel_size, bias=True
        )

    def __call__(self, hidden_states: mx.array) -> mx.array:
        target_dtype = self.proj.weight.dtype

        # Reshape to 5D: [batch, channels, temporal, height, width] (PyTorch format)
        # This matches the PyTorch ground truth exactly
        hidden_states = hidden_states.reshape(
            -1, self.in_channels, self.temporal_patch_size, self.patch_size, self.patch_size
        )

        # Convert to MLX format: [batch, temporal, height, width, channels]
        hidden_states = hidden_states.transpose(0, 2, 3, 4, 1)

        # Apply conv3d with target dtype and reshape to match PyTorch output
        hidden_states = self.proj(hidden_states.astype(target_dtype)).reshape(-1, self.embed_dim)

        return hidden_states


class VisionRotaryEmbedding(nn.Module):
    def __init__(self, dim: int, theta: float = 10000.0):
        super().__init__()
        # Don't store inv_freq as a parameter since it causes loading issues
        self.dim = dim
        self.theta = theta

    def __call__(self, seqlen: int) -> mx.array:
        # Compute inv_freq on the fly
        inv_freq = 1.0 / (self.theta ** (mx.arange(0, self.dim, 2, dtype=mx.float32) / self.dim))
        seq = mx.arange(seqlen, dtype=inv_freq.dtype)
        freqs = mx.outer(seq, inv_freq)
        return freqs


class VisionPatchMerger(nn.Module):
    def __init__(self, config: VisionConfig, use_postshuffle_norm=False):
        super().__init__()
        self.hidden_size = config.hidden_size * (config.spatial_merge_size**2)
        self.use_postshuffle_norm = use_postshuffle_norm

        norm_size = self.hidden_size if use_postshuffle_norm else config.hidden_size
        self.norm = nn.LayerNorm(norm_size, eps=1e-6)
        self.linear_fc1 = nn.Linear(self.hidden_size, self.hidden_size)
        self.linear_fc2 = nn.Linear(self.hidden_size, config.out_hidden_size)

    def __call__(self, x: mx.array) -> mx.array:
        if self.use_postshuffle_norm:
            x = self.norm(x.reshape(-1, self.hidden_size)).reshape(-1, self.hidden_size)
        else:
            x = self.norm(x).reshape(-1, self.hidden_size)

        x = self.linear_fc2(nn.gelu(self.linear_fc1(x)))
        return x


class VisionAttention(nn.Module):
    def __init__(self, config: VisionConfig):
        super().__init__()
        self.dim = config.hidden_size
        self.num_heads = config.num_heads
        self.head_dim = self.dim // self.num_heads
        self.scaling = self.head_dim**-0.5

        self.qkv = nn.Linear(self.dim, self.dim * 3, bias=True)
        self.proj = nn.Linear(self.dim, self.dim)

    def __call__(
        self,
        hidden_states: mx.array,
        cu_seqlens: mx.array,
        rotary_pos_emb: Optional[mx.array] = None,
        position_embeddings: Optional[Tuple[mx.array, mx.array]] = None,
        **kwargs,
    ) -> mx.array:
        seq_length = hidden_states.shape[0]
        qkv = self.qkv(hidden_states).reshape(seq_length, 3, self.num_heads, -1)
        qkv = qkv.transpose(1, 0, 2, 3)
        query_states, key_states, value_states = qkv[0], qkv[1], qkv[2]

        cos, sin = position_embeddings
        query_states, key_states = apply_rotary_pos_emb_vision(query_states, key_states, cos, sin)

        query_states = query_states.transpose(1, 0, 2)
        key_states = key_states.transpose(1, 0, 2)
        value_states = value_states.transpose(1, 0, 2)

        query_states = mx.expand_dims(query_states, axis=0)
        key_states = mx.expand_dims(key_states, axis=0)
        value_states = mx.expand_dims(value_states, axis=0)

        lengths = cu_seqlens[1:] - cu_seqlens[:-1]

        split_indices = []
        cumsum = 0
        for length in lengths[:-1]:
            cumsum += int(length)
            split_indices.append(cumsum)

        if split_indices:
            q_splits = mx.split(query_states, split_indices, axis=1)
            k_splits = mx.split(key_states, split_indices, axis=1)
            v_splits = mx.split(value_states, split_indices, axis=1)
        else:
            q_splits = [query_states]
            k_splits = [key_states]
            v_splits = [value_states]

        attn_outputs = []
        for q, k, v in zip(q_splits, k_splits, v_splits):
            attn_out = scaled_dot_product_attention(
                q, k, v, scale=self.scaling, mask=None, cache=None
            )
            attn_outputs.append(attn_out)

        attn_output = mx.concatenate(attn_outputs, axis=1)

        attn_output = attn_output[0].transpose(1, 0, 2)
        attn_output = attn_output.reshape(seq_length, -1)
        attn_output = self.proj(attn_output)

        return attn_output


class VisionBlock(nn.Module):
    def __init__(self, config: VisionConfig):
        super().__init__()
        self.norm1 = nn.LayerNorm(config.hidden_size, eps=1e-6)
        self.norm2 = nn.LayerNorm(config.hidden_size, eps=1e-6)
        self.attn = VisionAttention(config)
        self.mlp = VisionMLP(config)

    def __call__(
        self,
        hidden_states: mx.array,
        cu_seqlens: mx.array,
        position_embeddings: Tuple[mx.array, mx.array],
    ) -> mx.array:
        hidden_states = hidden_states + self.attn(
            self.norm1(hidden_states),
            cu_seqlens=cu_seqlens,
            position_embeddings=position_embeddings,
        )
        hidden_states = hidden_states + self.mlp(self.norm2(hidden_states))
        return hidden_states


class VisionModel(nn.Module):
    def __init__(self, config: VisionConfig):
        super().__init__()
        self.config = config
        self.spatial_merge_size = config.spatial_merge_size
        self.patch_size = config.patch_size

        self.patch_embed = VisionPatchEmbed(config)
        self.pos_embed = nn.Embedding(config.num_position_embeddings, config.hidden_size)
        self.num_grid_per_side = int(config.num_position_embeddings**0.5)

        head_dim = config.hidden_size // config.num_heads
        self.rotary_pos_emb = VisionRotaryEmbedding(head_dim // 2)

        self.blocks = [VisionBlock(config) for _ in range(config.num_hidden_layers)]
        self.merger = VisionPatchMerger(config, use_postshuffle_norm=False)

        self.deepstack_visual_indexes = config.deepstack_visual_indexes
        self.deepstack_merger_list = [
            VisionPatchMerger(config, use_postshuffle_norm=True)
            for _ in range(len(config.deepstack_visual_indexes))
        ]

    def rot_pos_emb(self, grid_thw: mx.array) -> mx.array:
        merge_size = self.spatial_merge_size

        max_hw = int(grid_thw[:, 1:].max().item())
        freq_table = self.rotary_pos_emb(max_hw)  # (max_hw, dim // 2)

        pos_ids_parts = []

        for i in range(grid_thw.shape[0]):
            num_frames = int(grid_thw[i, 0].item())
            height = int(grid_thw[i, 1].item())
            width = int(grid_thw[i, 2].item())

            merged_h, merged_w = height // merge_size, width // merge_size

            block_rows = mx.arange(merged_h)  # block row indices
            block_cols = mx.arange(merged_w)  # block col indices
            intra_row = mx.arange(merge_size)  # intra-block row offsets
            intra_col = mx.arange(merge_size)  # intra-block col offsets

            # Compute full-resolution positions using broadcasting
            row_idx = block_rows[:, None, None, None] * merge_size + intra_row[None, None, :, None]
            col_idx = block_cols[None, :, None, None] * merge_size + intra_col[None, None, None, :]

            row_idx = mx.broadcast_to(
                row_idx, (merged_h, merged_w, merge_size, merge_size)
            ).reshape(-1)
            col_idx = mx.broadcast_to(
                col_idx, (merged_h, merged_w, merge_size, merge_size)
            ).reshape(-1)

            coords = mx.stack([row_idx, col_idx], axis=-1)

            if num_frames > 1:
                coords = mx.tile(coords, (num_frames, 1))

            pos_ids_parts.append(coords)

        # Concatenate all coordinate parts
        pos_ids = mx.concatenate(pos_ids_parts, axis=0)

        embeddings = freq_table[pos_ids]  # lookup rotary embeddings
        embeddings = embeddings.reshape(embeddings.shape[0], -1)
        return embeddings

    def fast_pos_embed_interpolate(self, grid_thw: mx.array):
        patch_pos_embeds = []

        for i in range(grid_thw.shape[0]):
            t = int(grid_thw[i, 0].item())
            h = int(grid_thw[i, 1].item())
            w = int(grid_thw[i, 2].item())

            # Simple position embedding interpolation
            h_idxs = mx.linspace(0, self.num_grid_per_side - 1, h)
            w_idxs = mx.linspace(0, self.num_grid_per_side - 1, w)

            h_idxs_floor = mx.floor(h_idxs).astype(mx.int32)
            w_idxs_floor = mx.floor(w_idxs).astype(mx.int32)
            h_idxs_ceil = mx.minimum(h_idxs_floor + 1, self.num_grid_per_side - 1)
            w_idxs_ceil = mx.minimum(w_idxs_floor + 1, self.num_grid_per_side - 1)

            dh = h_idxs - h_idxs_floor.astype(mx.float32)
            dw = w_idxs - w_idxs_floor.astype(mx.float32)

            base_h = h_idxs_floor * self.num_grid_per_side
            base_h_ceil = h_idxs_ceil * self.num_grid_per_side

            # Compute bilinear interpolation indices and weights
            indices_tl = (base_h[:, None] + w_idxs_floor[None, :]).reshape(-1)
            indices_tr = (base_h[:, None] + w_idxs_ceil[None, :]).reshape(-1)
            indices_bl = (base_h_ceil[:, None] + w_idxs_floor[None, :]).reshape(-1)
            indices_br = (base_h_ceil[:, None] + w_idxs_ceil[None, :]).reshape(-1)

            weights_tl = ((1 - dh)[:, None] * (1 - dw)[None, :]).reshape(-1)
            weights_tr = ((1 - dh)[:, None] * dw[None, :]).reshape(-1)
            weights_bl = (dh[:, None] * (1 - dw)[None, :]).reshape(-1)
            weights_br = (dh[:, None] * dw[None, :]).reshape(-1)

            # Get embeddings and interpolate
            pos_embed_tl = self.pos_embed(indices_tl) * weights_tl[:, None]
            pos_embed_tr = self.pos_embed(indices_tr) * weights_tr[:, None]
            pos_embed_bl = self.pos_embed(indices_bl) * weights_bl[:, None]
            pos_embed_br = self.pos_embed(indices_br) * weights_br[:, None]

            pos_embed = pos_embed_tl + pos_embed_tr + pos_embed_bl + pos_embed_br

            # Repeat for temporal dimension and apply spatial merging
            pos_embed = mx.tile(pos_embed, (t, 1))

            # Apply spatial merging pattern
            merge_size = self.config.spatial_merge_size
            pos_embed = pos_embed.reshape(
                t, h // merge_size, merge_size, w // merge_size, merge_size, -1
            )
            pos_embed = mx.transpose(pos_embed, (0, 1, 3, 2, 4, 5))
            pos_embed = pos_embed.reshape(-1, pos_embed.shape[-1])

            patch_pos_embeds.append(pos_embed)

        return mx.concatenate(patch_pos_embeds, axis=0)

    def __call__(
        self, hidden_states: mx.array, grid_thw: mx.array
    ) -> Tuple[mx.array, List[mx.array]]:
        hidden_states = self.patch_embed(hidden_states)

        pos_embeds = self.fast_pos_embed_interpolate(grid_thw)
        hidden_states = hidden_states + pos_embeds

        rotary_pos_emb = self.rot_pos_emb(grid_thw)
        seq_len = hidden_states.shape[0]

        emb = mx.concatenate([rotary_pos_emb, rotary_pos_emb], axis=-1)
        position_embeddings = (mx.cos(emb), mx.sin(emb))

        # Create cumulative sequence lengths (following HuggingFace implementation)
        # torch.repeat_interleave(grid_thw[:, 1] * grid_thw[:, 2], grid_thw[:, 0])
        seq_lens_per_image = grid_thw[:, 1] * grid_thw[:, 2]  # h * w for each image
        seq_lens = []
        for i, (seq_len, repeats) in enumerate(zip(seq_lens_per_image, grid_thw[:, 0])):
            seq_lens.extend([seq_len] * int(repeats))
        seq_lens = mx.array(seq_lens)

        # Then compute cumulative sum
        cu_seqlens = mx.cumsum(seq_lens)
        # Pad with 0 at the beginning
        cu_seqlens = mx.concatenate([mx.array([0]), cu_seqlens])

        deepstack_feature_lists = []
        for layer_num, blk in enumerate(self.blocks):
            hidden_states = blk(
                hidden_states,
                cu_seqlens=cu_seqlens,
                position_embeddings=position_embeddings,
            )
            if layer_num in self.deepstack_visual_indexes:
                idx = self.deepstack_visual_indexes.index(layer_num)
                deepstack_feature = self.deepstack_merger_list[idx](hidden_states)
                deepstack_feature_lists.append(deepstack_feature)

        hidden_states = self.merger(hidden_states)
        return hidden_states, deepstack_feature_lists


class TextRotaryEmbedding(nn.Module):
    def __init__(self, config: TextConfig):
        super().__init__()
        self.config = config
        self.max_seq_len_cached = config.max_position_embeddings
        self.original_max_seq_len = config.max_position_embeddings

        # MRoPE configuration
        if hasattr(config, "rope_scaling") and config.rope_scaling is not None:
            self.rope_type = config.rope_scaling.get("rope_type", "default")
            self.mrope_section = config.rope_scaling.get("mrope_section", [24, 20, 20])
        else:
            self.rope_type = "default"
            self.mrope_section = [24, 20, 20]

        # Store parameters for computing inv_freq on the fly
        self.head_dim = config.head_dim
        self.theta = config.rope_theta

        # Attention scaling (simplified - may need adjustment based on actual config)
        self.attention_scaling = 1.0

    def _get_inv_freq(self):
        """Compute inverse frequencies on the fly"""
        inv_freq = 1.0 / (
            self.theta ** (mx.arange(0, self.head_dim, 2).astype(mx.float32) / self.head_dim)
        )
        # Expand for 3 dimensions (T, H, W)
        return mx.broadcast_to(inv_freq[None, :], (3, len(inv_freq)))

    def apply_interleaved_mrope(self, freqs, mrope_section):
        """Apply interleaved MRoPE to 3D rotary embeddings.
        Reorganizes frequency layout from chunked [TTT...HHH...WWW] to
        interleaved [THTHWHTHW...TT], preserving frequency continuity.
        args:
            x: (3, bs, seq_len, head_dim // 2)
            mrope_section: (3,)
        returns:
            x_t: (bs, seq_len, head_dim // 2)
        """
        freqs_t = freqs[0]  # just overwrite the first dimension T
        for dim, offset in enumerate((1, 2), start=1):  # H, W
            length = mrope_section[dim] * 3
            idx = slice(offset, length, 3)
            freqs_t[..., idx] = freqs[dim, ..., idx]
        return freqs_t

    def __call__(self, x: mx.array, position_ids: mx.array) -> mx.array:
        """
        Args:
            x: Input tensor for dtype reference
            position_ids: Position indices, shape (3, batch_size, seq_len) for MRoPE

        Returns:
            cos, sin: Cosine and sine embeddings
        """
        # Handle 2D position_ids by expanding to 3D for MRoPE
        if position_ids.ndim == 2:
            position_ids = mx.broadcast_to(
                position_ids[None, ...], (3, position_ids.shape[0], position_ids.shape[1])
            )

        batch_size, seq_len = position_ids.shape[1], position_ids.shape[2]

        # Expand inverse frequencies: (3, 1, 1, dim//2) -> (3, batch_size, 1, dim//2)
        inv_freq_expanded = mx.broadcast_to(
            self._get_inv_freq()[:, None, None, :],
            (3, batch_size, 1, self._get_inv_freq().shape[-1]),
        )

        # Expand position ids: (3, batch_size, seq_len) -> (3, batch_size, seq_len, 1)
        position_ids_expanded = position_ids[..., None].astype(mx.float32)

        # Compute frequencies: (3, batch_size, seq_len, dim//2)
        freqs = inv_freq_expanded * position_ids_expanded

        # Apply interleaved MRoPE
        freqs = self.apply_interleaved_mrope(freqs, self.mrope_section)

        # Create embeddings
        emb = mx.concatenate([freqs, freqs], axis=-1)  # (batch_size, seq_len, head_dim)
        cos = mx.cos(emb) * self.attention_scaling
        sin = mx.sin(emb) * self.attention_scaling

        return cos.astype(x.dtype), sin.astype(x.dtype)


class TextAttention(nn.Module):
    def __init__(self, config: TextConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx

        dim = config.hidden_size
        self.n_heads = config.num_attention_heads
        self.n_kv_heads = config.num_key_value_heads
        self.head_dim = config.head_dim
        self.scale = self.head_dim**-0.5

        self.q_proj = nn.Linear(dim, self.n_heads * self.head_dim, bias=config.attention_bias)
        self.k_proj = nn.Linear(dim, self.n_kv_heads * self.head_dim, bias=config.attention_bias)
        self.v_proj = nn.Linear(dim, self.n_kv_heads * self.head_dim, bias=config.attention_bias)
        self.o_proj = nn.Linear(self.n_heads * self.head_dim, dim, bias=config.attention_bias)

        self.q_norm = nn.RMSNorm(self.head_dim, eps=config.rms_norm_eps)
        self.k_norm = nn.RMSNorm(self.head_dim, eps=config.rms_norm_eps)

        # Initialize rope directly
        self.rope = initialize_rope(
            config.head_dim,
            base=config.rope_theta,
            traditional=False,
            scaling_config=config.rope_scaling,
            max_position_embeddings=config.max_position_embeddings,
        )

    def __call__(
        self,
        hidden_states: mx.array,
        attention_mask: Optional[mx.array] = None,
        cache: Optional[Any] = None,
        cos: Optional[mx.array] = None,
        sin: Optional[mx.array] = None,
        rope_deltas: Optional[mx.array] = None,
    ) -> Tuple[mx.array, Optional[mx.array]]:
        B, L, D = hidden_states.shape

        queries = self.q_proj(hidden_states).reshape(B, L, self.n_heads, -1)
        keys = self.k_proj(hidden_states).reshape(B, L, self.n_kv_heads, -1)
        values = self.v_proj(hidden_states).reshape(B, L, self.n_kv_heads, -1)

        queries = self.q_norm(queries).transpose(0, 2, 1, 3)
        keys = self.k_norm(keys).transpose(0, 2, 1, 3)
        values = values.transpose(0, 2, 1, 3)

        # Apply rope directly to queries and keys
        if cos is not None and sin is not None:
            queries, keys = apply_rotary_pos_emb(queries, keys, cos, sin)
            if cache is not None:
                keys, values = cache.update_and_fetch(keys, values)
        else:
            if cache is not None:
                # Handle different types of rope_deltas: scalar, array, or None
                if rope_deltas is None:
                    offset_delta = 0
                elif isinstance(rope_deltas, (int, float)):
                    # rope_deltas is a scalar
                    offset_delta = rope_deltas
                elif hasattr(rope_deltas, 'size') and rope_deltas.size == 1:
                    # rope_deltas is an array with single element
                    offset_delta = rope_deltas.item()
                elif hasattr(rope_deltas, 'shape') and rope_deltas.shape:
                    # rope_deltas is an array with multiple elements, take first
                    offset_delta = rope_deltas.reshape(-1)[0].item()
                else:
                    offset_delta = 0
                
                queries = self.rope(queries, offset=cache.offset + offset_delta)
                keys = self.rope(keys, offset=cache.offset + offset_delta)
                keys, values = cache.update_and_fetch(keys, values)
            else:
                queries = self.rope(queries)
                keys = self.rope(keys)

        output = scaled_dot_product_attention(
            queries, keys, values, cache=cache, scale=self.scale, mask=attention_mask
        )
        output = output.transpose(0, 2, 1, 3).reshape(B, L, -1)
        return self.o_proj(output), None


class TextMLP(nn.Module):
    def __init__(self, config: TextConfig):
        super().__init__()
        self.gate_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.up_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.down_proj = nn.Linear(config.intermediate_size, config.hidden_size, bias=False)

    def __call__(self, x):
        return self.down_proj(nn.silu(self.gate_proj(x)) * self.up_proj(x))


class TextDecoderLayer(nn.Module):
    def __init__(self, config: TextConfig, layer_idx: int):
        super().__init__()
        self.hidden_size = config.hidden_size
        self.self_attn = TextAttention(config, layer_idx)
        self.mlp = TextMLP(config)
        self.input_layernorm = nn.RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = nn.RMSNorm(config.hidden_size, eps=config.rms_norm_eps)

    def __call__(
        self,
        hidden_states: mx.array,
        attention_mask: Optional[mx.array] = None,
        cache: Optional[Any] = None,
        cos: Optional[mx.array] = None,
        sin: Optional[mx.array] = None,
        rope_deltas: Optional[mx.array] = None,
    ) -> mx.array:
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)

        hidden_states, _ = self.self_attn(
            hidden_states=hidden_states,
            attention_mask=attention_mask,
            cache=cache,
            cos=cos,
            sin=sin,
            rope_deltas=rope_deltas,
        )
        hidden_states = residual + hidden_states
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states
        return hidden_states


class TextModel(nn.Module):
    def __init__(self, config: TextConfig):
        super().__init__()
        self.config = config
        self.vocab_size = config.vocab_size

        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.layers = [
            TextDecoderLayer(config, layer_idx) for layer_idx in range(config.num_hidden_layers)
        ]
        self.norm = nn.RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.rotary_emb = TextRotaryEmbedding(config)

    def _deepstack_process(
        self,
        hidden_states: mx.array,
        visual_pos_masks: mx.array,
        deepstack_visual_embeds: mx.array,
    ) -> mx.array:
        if visual_pos_masks is None or deepstack_visual_embeds is None:
            return hidden_states
        B, L, D = hidden_states.shape
        mask_flat = visual_pos_masks.astype(mx.int32).reshape(-1)
        idx_flat = mx.cumsum(mask_flat, axis=0) - 1
        N = deepstack_visual_embeds.shape[0]
        idx_flat = mx.maximum(idx_flat, 0)
        eq = (idx_flat[:, None] == mx.arange(N)[None, :]).astype(hidden_states.dtype)
        add_flat = eq @ deepstack_visual_embeds.astype(hidden_states.dtype)
        add_flat = add_flat * mask_flat[:, None].astype(hidden_states.dtype)
        add = add_flat.reshape(B, L, D)
        return hidden_states + add

    def __call__(
        self,
        input_ids: Optional[mx.array] = None,
        inputs_embeds: Optional[mx.array] = None,
        attention_mask: Optional[mx.array] = None,
        cache=None,
        visual_pos_masks: Optional[mx.array] = None,
        deepstack_visual_embeds: Optional[List[mx.array]] = None,
        cos: Optional[mx.array] = None,
        sin: Optional[mx.array] = None,
        rope_deltas: Optional[mx.array] = None,
    ):
        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        hidden_states = inputs_embeds

        if attention_mask is None:
            attention_mask = create_attention_mask(hidden_states, cache, return_array=True)

        if cache is None:
            cache = [None] * len(self.layers)

        for layer_idx, (decoder_layer, c) in enumerate(zip(self.layers, cache)):
            hidden_states = decoder_layer(
                hidden_states,
                attention_mask=attention_mask,
                cache=c,
                cos=cos,
                sin=sin,
                rope_deltas=rope_deltas,
            )
            if deepstack_visual_embeds is not None and layer_idx < len(deepstack_visual_embeds):
                hidden_states = self._deepstack_process(
                    hidden_states, visual_pos_masks, deepstack_visual_embeds[layer_idx]
                )
        hidden_states = self.norm(hidden_states)
        return hidden_states


# Standalone Vision Model
class VEGModel(nn.Module):
    def __init__(self, vision_config: VisionConfig):
        super().__init__()
        self.config = vision_config
        self.visual = VisionModel(vision_config)

    def __call__(self, pixel_values: mx.array, image_grid_thw: mx.array):
        return self.visual(pixel_values, image_grid_thw)

    def sanitize(self, weights):
        sanitized = {}
        for k, v in weights.items():
            if "visual." in k:
                # Remove prefixes to match our model structure
                clean_key = k.replace("model.visual.", "").replace("visual.", "")
                sanitized[f"visual.{clean_key}"] = v
        return sanitized


# Pure LLM Model (no vision components)
class LLMModel(nn.Module):
    def __init__(self, text_config: TextConfig):
        super().__init__()
        self.args = text_config
        self.config = text_config
        self.language_model = TextModel(text_config)
        if not text_config.tie_word_embeddings:
            self.lm_head = nn.Linear(text_config.hidden_size, text_config.vocab_size, bias=False)

    def get_rope_index(
        self,
        input_ids: Optional[mx.array] = None,
        image_grid_thw: Optional[mx.array] = None,
        attention_mask: Optional[mx.array] = None,
    ) -> Tuple[mx.array, mx.array]:
        """Simplified version for images only (no video support)."""

        spatial_merge_size = 2
        image_token_id = 151655
        vision_start_token_id = 151652
        mrope_position_deltas = []

        if input_ids is not None and image_grid_thw is not None:
            total_input_ids = input_ids
            if attention_mask is None:
                attention_mask = mx.ones_like(total_input_ids)

            batch_size, seq_len = input_ids.shape
            position_ids_list = []
            image_index = 0

            for i in range(batch_size):
                input_ids_seq = total_input_ids[i]
                mask_seq = attention_mask[i]

                # Use mask to get valid length
                valid_length = int(mx.sum(mask_seq).item())
                input_ids_seq = input_ids_seq[:valid_length]

                image_nums = 0
                # Find vision start tokens by iterating through the sequence
                vision_start_positions = []
                for pos in range(input_ids_seq.shape[0]):
                    if input_ids_seq[pos].item() == vision_start_token_id:
                        vision_start_positions.append(pos)

                if len(vision_start_positions) > 0:
                    for pos in vision_start_positions:
                        if pos + 1 < input_ids_seq.shape[0]:
                            if input_ids_seq[pos + 1].item() == image_token_id:
                                image_nums += 1

                input_tokens = input_ids_seq.tolist()
                llm_pos_ids_list = []
                st = 0
                remain_images = image_nums

                for _ in range(image_nums):
                    ed_image = input_tokens.index(image_token_id, st)

                    t = image_grid_thw[image_index, 0].item()
                    h = image_grid_thw[image_index, 1].item()
                    w = image_grid_thw[image_index, 2].item()
                    image_index += 1
                    remain_images -= 1
                    ed = ed_image

                    llm_grid_t = int(t)
                    llm_grid_h = int(h) // spatial_merge_size
                    llm_grid_w = int(w) // spatial_merge_size
                    text_len = ed - st

                    st_idx = (
                        llm_pos_ids_list[-1].max().item() + 1 if len(llm_pos_ids_list) > 0 else 0
                    )
                    text_pos = mx.arange(text_len).reshape(1, -1)
                    text_pos = mx.broadcast_to(text_pos, (3, text_len)) + st_idx
                    llm_pos_ids_list.append(text_pos)

                    # t_index is always 0 because llm_grid_t is always 1 for images
                    t_index = mx.arange(llm_grid_t).reshape(-1, 1)
                    t_index = mx.broadcast_to(
                        t_index, (llm_grid_t, llm_grid_h * llm_grid_w)
                    ).reshape(-1)

                    h_index = mx.arange(llm_grid_h).reshape(1, -1, 1)
                    h_index = mx.broadcast_to(
                        h_index, (llm_grid_t, llm_grid_h, llm_grid_w)
                    ).reshape(-1)

                    w_index = mx.arange(llm_grid_w).reshape(1, 1, -1)
                    w_index = mx.broadcast_to(
                        w_index, (llm_grid_t, llm_grid_h, llm_grid_w)
                    ).reshape(-1)

                    vision_pos = mx.stack([t_index, h_index, w_index]) + text_len + st_idx
                    llm_pos_ids_list.append(vision_pos)
                    st = ed + llm_grid_t * llm_grid_h * llm_grid_w

                if st < len(input_tokens):
                    st_idx = (
                        llm_pos_ids_list[-1].max().item() + 1 if len(llm_pos_ids_list) > 0 else 0
                    )
                    text_len = len(input_tokens) - st
                    text_pos = mx.arange(text_len).reshape(1, -1)
                    text_pos = mx.broadcast_to(text_pos, (3, text_len)) + st_idx
                    llm_pos_ids_list.append(text_pos)

                llm_positions = mx.concatenate(llm_pos_ids_list, axis=1).reshape(3, -1)

                # Create position_ids for this batch item, pad to seq_len
                batch_position_ids = mx.ones((3, seq_len), dtype=input_ids.dtype)
                valid_length = min(seq_len, llm_positions.shape[1])

                # Create new arrays for each dimension
                pos_dim0 = mx.concatenate(
                    [
                        llm_positions[0, :valid_length],
                        mx.ones(seq_len - valid_length, dtype=input_ids.dtype),
                    ]
                )
                pos_dim1 = mx.concatenate(
                    [
                        llm_positions[1, :valid_length],
                        mx.ones(seq_len - valid_length, dtype=input_ids.dtype),
                    ]
                )
                pos_dim2 = mx.concatenate(
                    [
                        llm_positions[2, :valid_length],
                        mx.ones(seq_len - valid_length, dtype=input_ids.dtype),
                    ]
                )

                batch_position_ids = mx.stack([pos_dim0, pos_dim1, pos_dim2])
                position_ids_list.append(batch_position_ids)

                mrope_position_deltas.append(
                    llm_positions.max().item() + 1 - len(total_input_ids[i])
                )

            # Stack all batch position_ids
            position_ids = mx.stack(position_ids_list, axis=1)  # Shape: (3, batch_size, seq_len)
            mrope_position_deltas = mx.array(mrope_position_deltas).reshape(-1, 1)
            return position_ids, mrope_position_deltas
        else:
            if attention_mask is not None:
                position_ids = mx.cumsum(attention_mask.astype(mx.int32), axis=-1) - 1
                position_ids = mx.where(attention_mask == 0, 1, position_ids)
                position_ids = mx.expand_dims(position_ids, axis=0)
                position_ids = mx.broadcast_to(
                    position_ids, (3, position_ids.shape[1], position_ids.shape[2])
                )
                max_position_ids = mx.max(
                    mx.max(position_ids, axis=0, keepdims=False), axis=-1, keepdims=True
                )
                mrope_position_deltas = max_position_ids + 1 - attention_mask.shape[-1]
            else:
                seq_len = input_ids.shape[1]
                batch_size = input_ids.shape[0]
                position_ids = mx.arange(seq_len).reshape(1, 1, -1)
                position_ids = mx.broadcast_to(position_ids, (3, batch_size, seq_len))
                mrope_position_deltas = mx.zeros((batch_size, 1), dtype=input_ids.dtype)

            return position_ids, mrope_position_deltas

    def __call__(
        self,
        inputs: mx.array = None,
        mask: mx.array = None,
        cache=None,
        inputs_embeds: Optional[mx.array] = None,
        visual_pos_masks: Optional[mx.array] = None,
        deepstack_visual_embeds: Optional[List[mx.array]] = None,
        cos: Optional[mx.array] = None,
        sin: Optional[mx.array] = None,
        rope_deltas: Optional[mx.array] = None,
    ):
        out = self.language_model(
            input_ids=inputs,
            inputs_embeds=inputs_embeds,
            attention_mask=mask,
            cache=cache,
            visual_pos_masks=visual_pos_masks,
            deepstack_visual_embeds=deepstack_visual_embeds,
            cos=cos,
            sin=sin,
            rope_deltas=rope_deltas,
        )
        if self.args.tie_word_embeddings:
            return self.language_model.embed_tokens.as_linear(out)
        else:
            return self.lm_head(out)

    def sanitize(self, weights):
        sanitized = {}
        for k, v in weights.items():
            if not ("visual." in k):
                # Handle key mapping from combined model to LLM-only model
                clean_key = k

                # Remove model. prefix if present
                if clean_key.startswith("model."):
                    clean_key = clean_key[6:]  # Remove 'model.'

                # Map language_ prefixed keys to language_model structure
                if clean_key.startswith("language_"):
                    if clean_key.startswith("language_layers."):
                        clean_key = (
                            "language_model.layers." + clean_key[16:]
                        )  # Map to language_model.layers.
                    elif clean_key.startswith("language_embed_tokens."):
                        clean_key = (
                            "language_model.embed_tokens." + clean_key[22:]
                        )  # Map to language_model.embed_tokens.
                    elif clean_key.startswith("language_norm."):
                        clean_key = (
                            "language_model.norm." + clean_key[14:]
                        )  # Map to language_model.norm.

                sanitized[clean_key] = v

        # Handle tied embeddings - remove lm_head if using tied embeddings
        if self.args.tie_word_embeddings:
            sanitized.pop("lm_head.weight", None)

        return sanitized

    @property
    def layers(self):
        return self.language_model.layers


# Combined Model (for compatibility and utility functions)
class Qwen3VLModel(nn.Module):
    def __init__(self, args: ModelArgs):
        super().__init__()
        self.args = args
        self.config = args
        self.visual = VisionModel(args.vision_config)
        self.language_model = TextModel(args.text_config)

    def sanitize(self, weights):
        # Map weights to match the combined model structure
        sanitized = {}
        for k, v in weights.items():
            # Remove 'model.' prefix if present to match our structure
            clean_key = k.replace("model.", "") if k.startswith("model.") else k
            sanitized[clean_key] = v
        return sanitized

    def get_image_features(self, pixel_values: mx.array, image_grid_thw: Optional[mx.array] = None):
        image_embeds, deepstack_visual_embeds = self.visual(pixel_values, image_grid_thw)
        # Split based on grid dimensions
        if image_grid_thw is not None:
            split_sizes = (
                mx.prod(image_grid_thw, axis=-1) // (self.visual.spatial_merge_size**2)
            ).tolist()
            # Convert sizes to indices for mx.split (cumulative sum, excluding the last)
            split_indices = []
            cumsum = 0
            for size in split_sizes[:-1]:  # Exclude last element
                cumsum += size
                split_indices.append(cumsum)

            if split_indices:  # Only split if we have indices
                image_embeds = mx.split(image_embeds, split_indices)
            else:
                image_embeds = [image_embeds]  # Single image case
        return image_embeds, deepstack_visual_embeds

    def __call__(
        self,
        input_ids: mx.array = None,
        attention_mask: Optional[mx.array] = None,
        inputs_embeds: Optional[mx.array] = None,
        pixel_values: Optional[mx.array] = None,
        image_grid_thw: Optional[mx.array] = None,
        cache=None,
        visual_pos_masks: Optional[mx.array] = None,
        deepstack_visual_embeds: Optional[List[mx.array]] = None,
        cos: Optional[mx.array] = None,
        sin: Optional[mx.array] = None,
        rope_deltas: Optional[mx.array] = None,
    ):
        if inputs_embeds is None:
            inputs_embeds = self.language_model.embed_tokens(input_ids)

        # Process images

        if pixel_values is not None:
            image_embeds, deepstack_visual_embeds = self.get_image_features(
                pixel_values, image_grid_thw
            )

            # Create masks and embed visual features
            if isinstance(image_embeds, list):
                image_embeds = mx.concatenate(image_embeds, axis=0)

            # Find image token positions and replace with visual embeddings
            image_mask = input_ids == self.args.image_token_id
            visual_pos_masks = image_mask

            # Replace image tokens with visual embeddings
            inputs_embeds = inputs_embeds.at[image_mask].set(
                image_embeds.astype(inputs_embeds.dtype)
            )

        outputs = self.language_model(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            cache=cache,
            visual_pos_masks=visual_pos_masks,
            deepstack_visual_embeds=deepstack_visual_embeds,
            cos=cos,
            sin=sin,
            rope_deltas=rope_deltas,
        )

        return outputs


def handle_multimodal_embeds(vision_model, llm_model, input_ids, pixel_values, image_grid_thw):
    """
    Handle the processing of multimodal embeddings including image features and position encoding.

    This function processes vision and text inputs to create unified embeddings that can be fed
    into the language model. It handles:
    - Vision feature extraction from pixel values
    - Deepstack visual embedding collection
    - Image token replacement in text embeddings
    - Position encoding setup for MRoPE (Multi-dimensional RoPE)

    Args:
        vision_model: The vision encoder model (VEGModel instance)
        llm_model: The language model (LLMModel instance)
        input_ids: Tokenized text input with image token placeholders [batch_size, seq_len]
        pixel_values: Preprocessed image pixel data [num_patches, feature_dim]
        image_grid_thw: Grid dimensions for each image [num_images, 3] (time, height, width)

    Returns:
        tuple: (inputs_embeds, deepstack_visual_embeds, visual_pos_masks, cos, sin, rope_deltas)
            - inputs_embeds: Combined text and image embeddings [batch_size, seq_len, hidden_size]
            - deepstack_visual_embeds: Multi-layer visual features for deepstack processing
            - visual_pos_masks: Boolean mask indicating image token positions
            - cos: Cosine values for rotary position encoding
            - sin: Sine values for rotary position encoding
            - rope_deltas: Position offset deltas for rope computation
    """
    inputs_embeds = llm_model.language_model.embed_tokens(input_ids.squeeze(0))
    deepstack_visual_embeds = None
    visual_pos_masks = None
    cos = None
    sin = None
    rope_deltas = 0

    if pixel_values is not None:
        if pixel_values.ndim == 4:
            pixel_values = mx.expand_dims(pixel_values, axis=2)

        # Process each image individually to prevent feature mixing
        image_embeds_list = []
        all_deepstack_embeds = []

        # Calculate cumulative indices for each image
        cumulative_patches = 0

        for i in range(image_grid_thw.shape[0]):
            # Calculate number of patches for current image
            current_patches = int(image_grid_thw[i, 1] * image_grid_thw[i, 2])
            start_idx = cumulative_patches
            end_idx = cumulative_patches + current_patches
            cumulative_patches += current_patches

            single_pixel_values = pixel_values[start_idx:end_idx]
            single_grid_thw = image_grid_thw[i : i + 1]

            # Use vision model directly
            single_embeds, single_deepstack = vision_model(single_pixel_values, single_grid_thw)

            # Split based on grid dimensions
            if single_grid_thw is not None:
                split_sizes = (
                    mx.prod(single_grid_thw, axis=-1) // (vision_model.visual.spatial_merge_size**2)
                ).tolist()
                split_indices = []
                cumsum = 0
                for size in split_sizes[:-1]:
                    cumsum += size
                    split_indices.append(cumsum)

                if split_indices:
                    single_embeds = mx.split(single_embeds, split_indices)
                else:
                    single_embeds = [single_embeds]

            image_embeds_list.extend(single_embeds)

            # Collect deepstack embeddings
            if i == 0:
                all_deepstack_embeds = single_deepstack
            else:
                # Concatenate deepstack embeddings from different images
                for j in range(len(all_deepstack_embeds)):
                    all_deepstack_embeds[j] = mx.concatenate(
                        [all_deepstack_embeds[j], single_deepstack[j]], axis=0
                    )

        deepstack_visual_embeds = all_deepstack_embeds

        # Concatenate all image embeddings for processing
        image_embeds = mx.concatenate(image_embeds_list, axis=0)

        # Find all image token positions
        image_token_id = 151655  # Default image token ID
        image_mask = input_ids.squeeze(0) == image_token_id
        image_mask_np = np.array(image_mask)
        image_token_positions = np.where(image_mask_np)[0]

        # Verify we have the correct number of image tokens
        expected_total_tokens = sum(embed.shape[0] for embed in image_embeds_list)
        assert (
            len(image_token_positions) == expected_total_tokens
        ), f"Expected {expected_total_tokens} image tokens, got {len(image_token_positions)}"

        # Replace image tokens with image embeddings
        seq_len = inputs_embeds.shape[0]
        result = inputs_embeds

        # Replace image tokens with image embeddings sequentially
        embed_idx = 0
        for img_embed in image_embeds_list:
            for patch_idx in range(img_embed.shape[0]):
                token_pos = image_token_positions[embed_idx]
                pos_mask = mx.arange(seq_len) == token_pos
                result = mx.where(
                    mx.expand_dims(pos_mask, axis=-1),
                    mx.expand_dims(img_embed[patch_idx], axis=0).astype(inputs_embeds.dtype),
                    result,
                )
                embed_idx += 1

        inputs_embeds = result
        position_ids, rope_deltas = llm_model.get_rope_index(input_ids, image_grid_thw)
        cos, sin = llm_model.language_model.rotary_emb(inputs_embeds, position_ids)
        if inputs_embeds.ndim == 2:
            inputs_embeds = mx.expand_dims(inputs_embeds, axis=0)

        if image_mask is not None:
            visual_pos_masks = image_mask

    return inputs_embeds, deepstack_visual_embeds, visual_pos_masks, cos, sin, rope_deltas


# Legacy Model wrapper (for backward compatibility)
class Model(nn.Module):
    def __init__(self, args: ModelArgs):
        super().__init__()
        self.args = args
        self.model = Qwen3VLModel(args)
        if not args.text_config.tie_word_embeddings:
            self.lm_head = nn.Linear(
                args.text_config.hidden_size, args.text_config.vocab_size, bias=False
            )

    def __call__(
        self,
        inputs: mx.array = None,
        mask: mx.array = None,
        cache=None,
        inputs_embeds: Optional[mx.array] = None,
        pixel_values: Optional[mx.array] = None,
        image_grid_thw: Optional[mx.array] = None,
        visual_pos_masks: Optional[mx.array] = None,
        deepstack_visual_embeds: Optional[List[mx.array]] = None,
        cos: Optional[mx.array] = None,
        sin: Optional[mx.array] = None,
        rope_deltas: Optional[mx.array] = None,
    ):
        out = self.model(
            input_ids=inputs,
            inputs_embeds=inputs_embeds,
            attention_mask=mask,
            cache=cache,
            pixel_values=pixel_values,
            image_grid_thw=image_grid_thw,
            visual_pos_masks=visual_pos_masks,
            deepstack_visual_embeds=deepstack_visual_embeds,
            cos=cos,
            sin=sin,
            rope_deltas=rope_deltas,
        )
        if self.args.text_config.tie_word_embeddings:
            return self.model.language_model.embed_tokens.as_linear(out)
        else:
            return self.lm_head(out)

    def sanitize(self, weights):
        # Remove any unnecessary weights
        sanitized = {}
        for k, v in weights.items():
            sanitized[k] = v

        # Handle tied embeddings - remove lm_head if using tied embeddings
        if self.args.text_config.tie_word_embeddings:
            sanitized.pop("lm_head.weight", None)

        return sanitized

    @property
    def layers(self):
        return self.model.language_model.layers
