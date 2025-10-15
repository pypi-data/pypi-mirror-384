import argparse
import json
import os
import mlx.core as mx
import mlx.nn as nn
import time
from PIL import Image
import requests
import numpy as np
from pathlib import Path
from huggingface_hub import snapshot_download
from dataclasses import dataclass
from typing import Any, Generator, List, Optional, Sequence, Tuple, Union

# Import required modules for quantized loading
from transformers import AutoTokenizer

# Import from the nested modeling structure
from .modeling.models.qwen3vl_moe.llm_common.generate import nexa_generate_step
from .modeling.models.qwen3vl_moe.llm_common.cache import make_prompt_cache
from .modeling.models.qwen3vl_moe.qwen3vl_moe import (
    VEGModel, LLMModel, ModelArgs, VisionConfig, TextConfig, handle_multimodal_embeds
)
from .modeling.models.qwen3vl_moe.processor import Qwen3VLProcessor
from .generate import GenerationResult
from ml import ChatMessage 

@dataclass
class Qwen3VLBundledModel:
    """Container for Qwen3-VL MoE vision and language models."""
    vision_model: VEGModel
    llm_model: LLMModel


def _ensure_list(x: Union[str, List[str], None]) -> Optional[List[str]]:
    if x is None:
        return None
    return x if isinstance(x, list) else [x]


def load_qwen3_vl(
    path_or_repo: str,
    adapter_path: Optional[str] = None,
    lazy: bool = False,
    revision: Optional[str] = None,
    **kwargs,
) -> Tuple[Qwen3VLBundledModel, Qwen3VLProcessor]:
    """Load Qwen3-VL MoE quantized models and processor.

    Parameters are aligned with .generate.load for compatibility.
    """
    model_path = Path(path_or_repo)
    if not model_path.exists():
        if "/" in path_or_repo:
            model_path = Path(snapshot_download(
                repo_id=path_or_repo, repo_type="model", revision=revision))
        else:
            # Fallback to local modelfiles directory relative to this file
            curr_dir = Path(__file__).parent
            model_path = curr_dir / "modeling" / "models" / "qwen3vl_moe" / "modelfiles"
            if not model_path.exists():
                model_path = curr_dir / "modelfiles"

    # Model configs - Updated to match Qwen3VL-MoE specifications
    vision_config = VisionConfig(
        hidden_size=1152,
        intermediate_size=4304,
        num_heads=16,
        num_hidden_layers=27,
        patch_size=16,
        temporal_patch_size=2,
        in_channels=3,
        hidden_act="gelu_pytorch_tanh",
        spatial_merge_size=2,
        out_hidden_size=2048,
        num_position_embeddings=2304,
        deepstack_visual_indexes=[8, 16, 24],
    )

    text_config = TextConfig(
        model_type="qwen3_vl_moe_text",
        hidden_size=2048,
        num_hidden_layers=48,
        intermediate_size=6144,
        num_attention_heads=32,
        num_key_value_heads=4,
        rms_norm_eps=1e-6,
        vocab_size=152064,
        max_position_embeddings=128000,
        rope_theta=1000000.0,
        head_dim=128,
        tie_word_embeddings=False,
        attention_bias=False,
        attention_dropout=0.0,
        rope_scaling={
            "mrope_interleaved": True,
            "mrope_section": [24, 20, 20],
            "rope_type": "default"
        },
        # MoE specific parameters
        num_experts=128,
        num_experts_per_tok=8,
        moe_intermediate_size=768,
        shared_expert_intermediate_size=0,
        norm_topk_prob=True,
        decoder_sparse_step=1,
        max_window_layers=48,
        sliding_window=32768,
        mlp_only_layers=[],
        use_qk_norm=True,
        layer_types=[],
    )

    vision_model = VEGModel(vision_config)
    llm_model = LLMModel(text_config)

    # Try to load LLM model from available files in order of preference
    preferred_order = [
        ("qwen3vl-moe-llm-30B-A3B-q4_0.safetensors", 4),
        ("qwen3vl-moe-llm-30B-A3B-q8_0.safetensors", 8),
        ("qwen3vl-moe-llm-30B-A3B-f32.safetensors", 32),
    ]

    llm_weights_path = None
    quantization_bits = None
    
    # Try loading in order of preference
    for filename, bits in preferred_order:
        candidate_path = model_path / filename
        if candidate_path.exists():
            llm_weights_path = candidate_path
            quantization_bits = bits
            break
    
    if llm_weights_path is None:
        # Fallback to original hardcoded path for backward compatibility
        llm_weights_path = model_path / "qwen3vl-moe-llm-30B-A3B-q4_0.safetensors"
        quantization_bits = 4

    vision_weights_path = model_path / "qwen3vl-moe-vision-30B-A3B-f16.safetensors"

    if not vision_weights_path.exists():
        raise FileNotFoundError(
            f"Missing vision weights: {vision_weights_path}"
        )

    # Load weights (vision fp16, llm with detected quantization)
    vision_model.set_dtype(mx.float16)
    vision_model.load_weights(str(vision_weights_path), strict=True)

    # Apply quantization if needed and load LLM weights
    if quantization_bits in [4, 8]:
        nn.quantize(llm_model, bits=quantization_bits, group_size=64,
                    class_predicate=quant_predicate)
    # For f32 (32-bit), no quantization needed
    
    llm_model.load_weights(str(llm_weights_path), strict=True)

    # Tokenizer and processor
    tokenizer = AutoTokenizer.from_pretrained(path_or_repo)
    processor = Qwen3VLProcessor(tokenizer=tokenizer)

    return Qwen3VLBundledModel(vision_model=vision_model, llm_model=llm_model), processor

def apply_chat_template_qwen3_vl(messages: Sequence[ChatMessage], num_images: int = 0, num_audios: int = 0, tools: Optional[str] = None, enable_thinking: bool = False) -> str:
    """Apply chat template: serialize messages with content as a list of typed items."""
    messages_dict = []
    for msg in messages:
        content_items = [{"type": "text", "text": msg.content}]
        messages_dict.append({"role": msg.role, "content": content_items})
    return json.dumps(messages_dict)


def stream_generate_qwen3_vl(
    model: Qwen3VLBundledModel,
    processor: Qwen3VLProcessor,
    prompt: str,
    image: Union[str, List[str]] = None,
    audio: Union[str, List[str]] = None,
    max_tokens: int = 512,
    **kwargs,

) -> Generator[Any, None, None]:
    """Stream generation yielding .generate.GenerationResult-compatible chunks."""
    messages = json.loads(prompt)
    if image is not None:
        image_list = image if isinstance(image, list) else [image]
        pil_images = []
        for p in image_list:
            try:
                pil_images.append(Image.open(p))
            except Exception:
                continue
        contents = [{"type": "image", "image": img} for img in pil_images]
        if messages:
            if "content" not in messages[-1] or not isinstance(messages[-1]["content"], list):
                messages[-1]["content"] = []
            messages[-1]["content"].extend(contents)

    raw_text, processed_images = processor.messages_to_text(
        messages, add_generation_prompt=True)

    inputs = processor.text_to_input_ids(
        raw_text, images=processed_images, return_tensors="mlx")

    input_ids = inputs["input_ids"]
    pixel_values = inputs.get("pixel_values")
    image_grid_thw = inputs.get("image_grid_thw")

    inputs_embeds, deepstack_visual_embeds, visual_pos_masks, cos, sin, rope_deltas = handle_multimodal_embeds(
        model.vision_model, model.llm_model, input_ids, pixel_values, image_grid_thw
    )

    prompt_cache = make_prompt_cache(model.llm_model, max_kv_size=4096)
    tokenizer = processor.tokenizer

    # Rough prompt TPS estimation based on input size
    prompt_start = time.perf_counter()
    prompt_tps = input_ids.size / max(1e-6, (time.perf_counter() - prompt_start))

    gen_count = 0
    tic = time.perf_counter()

    for token, logprobs in nexa_generate_step(
        model=model.llm_model,
        prompt=None,
        input_embeddings=inputs_embeds,
        max_tokens=max_tokens,
        max_kv_size=4096,
        prompt_cache=prompt_cache,
        visual_pos_masks=visual_pos_masks,
        deepstack_visual_embeds=deepstack_visual_embeds,
        cos=cos,
        sin=sin,
        rope_deltas=rope_deltas,
    ):
        if token == tokenizer.eos_token_id:
            break

        text_piece = tokenizer.decode([token])
        gen_count += 1

        yield GenerationResult(
            text=text_piece,
            token=token,
            logprobs=logprobs,
            prompt_tokens=int(input_ids.size),
            generation_tokens=gen_count,
            prompt_tps=float(prompt_tps),
            generation_tps=float(
                gen_count / max(1e-6, (time.perf_counter() - tic))),
            peak_memory=float(mx.get_peak_memory() / 1e9),
        )

def quant_predicate(path: str, mod: nn.Module) -> bool:
    """Quantization predicate to exclude certain layers from quantization."""
    if path.endswith("lm_head") or "norm" in path.lower() or "embed" in path.lower():
        return False
    return isinstance(mod, (nn.Linear, nn.Embedding))
