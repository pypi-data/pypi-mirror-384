from __future__ import annotations

from typing import (
    List,
    Optional,
)

import mlx.core as mx
import numpy as np
from PIL import Image as PILImage
import mlx.nn as nn
import os

from .stable_diffusion import StableDiffusion, StableDiffusionXL


class Image:
    def __init__(self, data: List[float], width: int, height: int, channels: int) -> None:
        """Initialize an image with pixel data"""
        self.data = data
        self.width = width
        self.height = height
        self.channels = channels

    @classmethod
    def from_numpy(cls, array: np.ndarray) -> 'Image':
        """Create Image from numpy array (H, W, C)"""
        height, width, channels = array.shape
        data = array.flatten().tolist()
        return cls(data, width, height, channels)

    @classmethod
    def from_pil(cls, pil_image: PILImage.Image) -> 'Image':
        """Create Image from PIL Image"""
        array = np.array(pil_image).astype(np.float32) / 255.0
        return cls.from_numpy(array)

    def to_numpy(self) -> np.ndarray:
        """Convert to numpy array (H, W, C)"""
        return np.array(self.data).reshape(self.height, self.width, self.channels)

    def to_pil(self) -> PILImage.Image:
        """Convert to PIL Image"""
        array = (self.to_numpy() * 255).astype(np.uint8)
        return PILImage.fromarray(array)


class ImageSamplerConfig:
    def __init__(
        self,
        method: str = "ddim",
        steps: int = 4,  # SDXL Turbo typically uses fewer steps
        guidance_scale: float = 0.0,  # SDXL Turbo works well with no guidance
        eta: float = 0.0,
        seed: int = -1,
    ) -> None:
        """Initialize sampler configuration optimized for SDXL Turbo"""
        self.method = method
        self.steps = steps
        self.guidance_scale = guidance_scale
        self.eta = eta
        self.seed = seed


class ImageGenerationConfig:
    def __init__(
        self,
        prompts: str | List[str],
        negative_prompts: str | List[str] | None = None,
        height: int = 512,
        width: int = 512,
        sampler_config: Optional[ImageSamplerConfig] = None,
        lora_id: int = -1,  # Not used but kept for compatibility
        init_image: Optional[Image] = None,
        strength: float = 1.0,
        n_images: int = 1,
        n_rows: int = 1,
        decoding_batch_size: int = 1,
    ) -> None:
        """Initialize image generation configuration"""
        self.prompts = prompts
        self.negative_prompts = negative_prompts or ""
        self.height = height
        self.width = width
        self.sampler_config = sampler_config or ImageSamplerConfig()
        self.lora_id = lora_id
        self.init_image = init_image
        self.strength = strength
        self.n_images = n_images
        self.n_rows = n_rows
        self.decoding_batch_size = decoding_batch_size


class ImageGen:
    def __init__(
        self,
        model_path: str,
        scheduler_config_path: Optional[str] = None,
        device: Optional[str] = None,
        float16: bool = True,
        quantize: bool = False,
    ) -> None:
        """Initialize the image generation model for SDXL Turbo"""
        self.model_path = model_path
        self.scheduler_config_path = scheduler_config_path
        self.float16 = float16
        self.quantize = quantize
        self.model = None

    @staticmethod
    def load_model(model_path: str, float16: bool = True, quantize: bool = False) -> StableDiffusion:
        """Load a model from the given path - following txt2img.py pattern"""

        # Check if it's a local path or HuggingFace repo
        # If it contains path separators or exists as a file/directory, treat as local
        is_local_path = (
            '/' in model_path or '\\' in model_path or os.path.exists(model_path))

        if is_local_path:
            # For local paths, determine model type from the path or model files
            if "xl" in model_path.lower() or "turbo" in model_path.lower():
                model = StableDiffusionXL(model_path, float16=float16)
            else:
                model = StableDiffusion(model_path, float16=float16)
        else:
            # For HuggingFace repo names, use the original logic
            if "xl" in model_path.lower() or "turbo" in model_path.lower():
                model = StableDiffusionXL(model_path, float16=float16)
            else:
                model = StableDiffusion(model_path, float16=float16)

        # Apply quantization if requested - same as txt2img.py
        if quantize:
            if "xl" in model_path.lower() or "turbo" in model_path.lower():
                nn.quantize(
                    model.text_encoder_1, class_predicate=lambda _, m: isinstance(
                        m, nn.Linear)
                )
                nn.quantize(
                    model.text_encoder_2, class_predicate=lambda _, m: isinstance(
                        m, nn.Linear)
                )
            else:
                nn.quantize(
                    model.text_encoder, class_predicate=lambda _, m: isinstance(
                        m, nn.Linear)
                )
            nn.quantize(model.unet, group_size=32, bits=8)
        return model

    def txt2img(self, prompt: str, config: ImageGenerationConfig, clear_cache: bool = True) -> Image:
        """Generate an image from a text prompt - following txt2img.py pattern"""
        if not self.model:
            self.model = self.load_model(self.model_path)
            if not self.model:
                raise RuntimeError("Model not loaded")

        sampler_config = config.sampler_config

        negative_prompt = ""
        if config.negative_prompts:
            negative_prompt = config.negative_prompts if isinstance(
                config.negative_prompts, str) else config.negative_prompts[0]

        # Generate latents - following txt2img.py approach
        latents_generator = self.model.generate_latents(
            prompt,
            n_images=1,
            num_steps=sampler_config.steps,
            cfg_weight=sampler_config.guidance_scale,
            negative_text=negative_prompt,
            seed=sampler_config.seed if sampler_config.seed >= 0 else None
        )

        # Get final latents - following txt2img.py pattern
        final_latents = None
        for latents in latents_generator:
            final_latents = latents
            mx.eval(final_latents)

        if final_latents is None:
            raise RuntimeError("No latents generated")

        # Decode to image - following txt2img.py pattern
        decoded_image = self.model.decode(final_latents)
        mx.eval(decoded_image)

        # Convert to numpy array
        image_array = np.array(decoded_image.squeeze(0))

        if clear_cache:
            mx.clear_cache()

        return Image.from_numpy(image_array)

    def img2img(self, init_image: Image, prompt: str, config: ImageGenerationConfig, clear_cache: bool = True) -> Image:
        """Generate an image from an initial image and a text prompt using SDXL Turbo"""
        if not self.model:
            self.model = self.load_model(self.model_path)
            if not self.model:
                raise RuntimeError("Model not loaded")

        sampler_config = config.sampler_config

        negative_prompt = ""
        if config.negative_prompts:
            negative_prompt = config.negative_prompts if isinstance(
                config.negative_prompts, str) else config.negative_prompts[0]

        img_tensor = _prepare_image_for_sd(
            init_image, config.width, config.height)

        # Generate latents from image
        latents_generator = self.model.generate_latents_from_image(
            img_tensor,
            prompt,
            n_images=1,
            strength=config.strength,
            num_steps=sampler_config.steps,
            cfg_weight=sampler_config.guidance_scale,
            negative_text=negative_prompt,
            seed=sampler_config.seed if sampler_config.seed >= 0 else None
        )

        # Get final latents
        final_latents = None
        for latents in latents_generator:
            final_latents = latents
            mx.eval(final_latents)

        if final_latents is None:
            raise RuntimeError("No latents generated")

        # Decode to image
        decoded_image = self.model.decode(final_latents)
        mx.eval(decoded_image)

        # Convert to numpy array
        image_array = np.array(decoded_image.squeeze(0))

        if clear_cache:
            mx.clear_cache()

        return Image.from_numpy(image_array)
