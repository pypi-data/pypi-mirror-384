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
from .modeling.models.qwen3_vl.llm_common.generate import nexa_generate_step
from .modeling.models.qwen3_vl.llm_common.cache import make_prompt_cache
from .modeling.models.qwen3_vl.qwen3vl import (
    VEGModel, LLMModel, ModelArgs, VisionConfig, TextConfig, handle_multimodal_embeds
)
from .modeling.models.qwen3_vl.processor import Qwen3VLProcessor
from .generate import GenerationResult
from ml import ChatMessage

# Custom exception for context length exceeded
class ContextLengthExceededError(Exception):
    """Raised when input context length exceeds model's maximum context size"""
    pass 

@dataclass
class Qwen3VLBundledModel:
    """Container for Qwen3-VL vision and language models."""
    vision_model: VEGModel
    llm_model: LLMModel


def _ensure_list(x: Union[str, List[str], None]) -> Optional[List[str]]:
    if x is None:
        return None
    return x if isinstance(x, list) else [x]


def get_model_configs(model_name: str):
    """Get model configurations based on model name"""
    
    # 4B model configs (default)
    if model_name in ["qwen3vl", "qwen3vl-4b", "qwen3vl-4b-thinking"]:
        vision_config = VisionConfig(
            hidden_size=1024,
            intermediate_size=4096,
            num_heads=16,
            num_hidden_layers=24,
            patch_size=16,
            temporal_patch_size=2,
            in_channels=3,
            hidden_act="gelu",
            spatial_merge_size=2,
            out_hidden_size=2560,
            num_position_embeddings=2304,
            deepstack_visual_indexes=[5, 11, 17],
        )

        text_config = TextConfig(
            model_type="qwen3vl",
            hidden_size=2560,
            num_hidden_layers=36,
            intermediate_size=9728,
            num_attention_heads=32,
            num_key_value_heads=8,
            rms_norm_eps=1e-6,
            vocab_size=151936,
            max_position_embeddings=32768,
            rope_theta=5000000.0,
            head_dim=128,
            tie_word_embeddings=True,
            attention_bias=False,
            attention_dropout=0.0,
            rope_scaling={"mrope_section": [24, 20, 20],
                          "rope_type": "default", "type": "default"},
        )
        
    # 8B model configs
    elif model_name in ["qwen3vl-8b", "qwen3vl-8b-thinking"]:
        vision_config = VisionConfig(
            hidden_size=1152,
            intermediate_size=4304,
            num_heads=16,
            num_hidden_layers=27,
            patch_size=16,
            temporal_patch_size=2,
            in_channels=3,
            hidden_act="gelu",
            spatial_merge_size=2,
            out_hidden_size=4096,
            num_position_embeddings=2304,
            deepstack_visual_indexes=[8, 16, 24],
        )

        text_config = TextConfig(
            model_type="qwen3vl",
            hidden_size=4096,
            num_hidden_layers=36,
            intermediate_size=12288,
            num_attention_heads=32,
            num_key_value_heads=8,
            rms_norm_eps=1e-6,
            vocab_size=151936,
            max_position_embeddings=262144,
            rope_theta=5000000,
            head_dim=128,
            tie_word_embeddings=False,
            attention_bias=False,
            attention_dropout=0.0,
            rope_scaling={"mrope_section": [24, 20, 20], "rope_type": "default", "mrope_interleaved": True},
        )
    else:
        # Fallback to 4B config
        return get_model_configs("qwen3vl-4b")
        
    return vision_config, text_config

def get_weight_filenames(model_name: str, model_path: Path):
    """Get appropriate weight filenames based on model name and available files"""
    
    # Determine model size and type based on the actual file structure
    if "4b" in model_name:
        size_prefix = "4b"
    elif "8b" in model_name:
        size_prefix = "8b"
    else:
        size_prefix = "4b"
    
    # Determine model type
    if "thinking" in model_name:
        model_type = f"{size_prefix}_thinking"
    else:
        model_type = f"{size_prefix}_instruct"
    
    # Try different weight file patterns matching the actual file structure
    llm_patterns = [
        # New naming convention matching actual files
        f"qwen3vl-llm-{model_type}-q4_0.safetensors",
        f"qwen3vl-llm-{model_type}-q8_0.safetensors", 
        f"qwen3vl-llm-{model_type}-f16.safetensors",
        # Legacy naming convention
        f"qwen3vl-llm-{size_prefix.upper()}-q4_0.safetensors",
        f"qwen3vl-llm-{size_prefix.upper()}-q8_0.safetensors",
        f"qwen3vl-llm-{size_prefix.upper()}-f16.safetensors",
        f"qwen3vl-llm-{size_prefix.upper()}-f32.safetensors",
    ]
    
    vision_patterns = [
        f"qwen3vl-vision-{model_type}-f16.safetensors",
        f"qwen3vl-vision-{size_prefix.upper()}-f16.safetensors",
    ]
    
    # Find LLM weights
    llm_weights_path = None
    quantization_bits = None
    
    for pattern in llm_patterns:
        candidate_path = model_path / pattern
        if candidate_path.exists():
            llm_weights_path = candidate_path
            if "q4_0" in pattern:
                quantization_bits = 4
            elif "q8_0" in pattern:
                quantization_bits = 8
            else:
                quantization_bits = 16
            break
    
    # Find vision weights
    vision_weights_path = None
    for pattern in vision_patterns:
        candidate_path = model_path / pattern
        if candidate_path.exists():
            vision_weights_path = candidate_path
            break
    
    return llm_weights_path, vision_weights_path, quantization_bits

# Update the load_qwen3_vl function signature and implementation:
def load_qwen3_vl(
    path_or_repo: str,
    adapter_path: Optional[str] = None,
    lazy: bool = False,
    revision: Optional[str] = None,
    model_name: Optional[str] = None,
    **kwargs,
) -> Tuple[Qwen3VLBundledModel, Qwen3VLProcessor]:
    """Load Qwen3-VL quantized models and processor with support for different model sizes."""
    
    model_path = Path(path_or_repo)
    if not model_path.exists():
        if "/" in path_or_repo:
            model_path = Path(snapshot_download(
                repo_id=path_or_repo, repo_type="model", revision=revision))
        else:
            # Fallback to local modelfiles directory relative to this file
            curr_dir = Path(__file__).parent
            model_path = curr_dir / "modeling" / "models" / "qwen3_vl" / "modelfiles"
            if not model_path.exists():
                model_path = curr_dir / "modelfiles"

    # Get model configurations based on model name
    if model_name:
        vision_config, text_config = get_model_configs(model_name)
    else:
        # Default to 4B config
        vision_config, text_config = get_model_configs("qwen3vl-4b")

    vision_model = VEGModel(vision_config)
    llm_model = LLMModel(text_config)

    # Get appropriate weight filenames
    llm_weights_path, vision_weights_path, quantization_bits = get_weight_filenames(
        model_name or "qwen3vl-4b", model_path
    )

    if not vision_weights_path or not llm_weights_path:
        raise FileNotFoundError(
            f"Missing safetensors. Vision: {vision_weights_path}, LLM: {llm_weights_path}"
        )

    # Load weights (vision fp16, llm with detected quantization)
    vision_model.set_dtype(mx.float16)
    vision_model.load_weights(str(vision_weights_path), strict=True)

    # Apply quantization if needed and load LLM weights
    if quantization_bits in [4, 8]:
        nn.quantize(llm_model, bits=quantization_bits, group_size=64,
                    class_predicate=quant_predicate)
    
    llm_model.load_weights(str(llm_weights_path), strict=True)

    try:
        tokenizer = AutoTokenizer.from_pretrained(str(model_path))
    except Exception:
        try:
            tokenizer = AutoTokenizer.from_pretrained(path_or_repo)
        except Exception:
            raise Exception("Failed to load tokenizer from the same path where model weights are loaded and original path_or_repo.")
    
    processor = Qwen3VLProcessor(tokenizer=tokenizer)

    return Qwen3VLBundledModel(vision_model=vision_model, llm_model=llm_model), processor

def apply_chat_template_qwen3_vl(messages: Sequence[ChatMessage], num_images: int = 0, num_audios: int = 0, tools: Optional[str] = None, enable_thinking: bool = False) -> str:
    """Apply chat template: serialize messages with content as a list of typed items."""
    
    messages_dict = []
    for i, msg in enumerate(messages):
        content_items = [{"type": "text", "text": msg.content}]
        messages_dict.append({"role": msg.role, "content": content_items})
    
    result = json.dumps(messages_dict)
    
    return result


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
    
    try:
        messages = json.loads(prompt)
    except json.JSONDecodeError as e:
        raise
    
    if image is not None:
        image_list = image if isinstance(image, list) else [image]
        pil_images = []
        for i, p in enumerate(image_list):
            try:
                img = Image.open(p)
                pil_images.append(img)
            except Exception as e:
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
    
    
    # Check if input context exceeds KV cache size and raise error
    max_kv_size = 4096  # This should match the max_kv_size used in make_prompt_cache and nexa_generate_step
    if input_ids.size > max_kv_size:
        error_msg = f"Input context length ({input_ids.size} tokens) exceeds maximum supported context size ({max_kv_size} tokens). Please reduce the input length."
        raise ContextLengthExceededError(error_msg)

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
    

    try:
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

            current_tps = gen_count / max(1e-6, (time.perf_counter() - tic))
            
            yield GenerationResult(
                text=text_piece,
                token=token,
                logprobs=logprobs,
                prompt_tokens=int(input_ids.size),
                generation_tokens=gen_count,
                prompt_tps=float(prompt_tps),
                generation_tps=float(current_tps),
                peak_memory=float(mx.get_peak_memory() / 1e9),
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
        

def quant_predicate(path: str, mod: nn.Module) -> bool:
    """Quantization predicate to exclude certain layers from quantization."""
    if path.endswith("lm_head") or "norm" in path.lower() or "embed" in path.lower():
        return False
    return isinstance(mod, (nn.Linear, nn.Embedding))
