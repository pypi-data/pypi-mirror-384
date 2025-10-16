from __future__ import annotations
import os
from typing import Optional

from ml import ImageGenCreateInput, ImageGenerationConfig, ImageGenImg2ImgInput, ImageGenTxt2ImgInput, ImageGenOutput
from profiling import ProfilingMixin, StopReason

from .generate_sd import ImageGen as SDImageGen, Image, ImageGenerationConfig as SDImageGenerationConfig, ImageSamplerConfig


class ImageGen(ProfilingMixin):
    sd_gen: Optional[SDImageGen] = None

    def __init__(self, input: ImageGenCreateInput):
        """Initialize the image generation model"""
        self.sd_gen = SDImageGen(model_path=input.model_path)

    def destroy(self) -> None:
        """Clean up resources"""
        self.sd_gen = None

    def txt2img(self, input: ImageGenTxt2ImgInput) -> ImageGenOutput:
        """Generate an image from a text prompt - public interface"""
        height = input.config.height
        width = input.config.width
        assert height % 16 == 0, f"Height must be divisible by 16 ({height}/16={height/16})"
        assert width % 16 == 0, f"Width must be divisible by 16 ({width}/16={width/16})"

        internal_config = SDImageGenerationConfig(
            prompts=input.prompt,
            negative_prompts=input.config.negative_prompts,
            height=height,
            width=width,
            sampler_config=ImageSamplerConfig(
                steps=input.config.sampler_config.steps,
                guidance_scale=input.config.sampler_config.guidance_scale,
                seed=input.config.sampler_config.seed
            ),
            strength=input.config.strength
        )

        result_image = self.sd_gen.txt2img(input.prompt, internal_config)

        parent_dir = os.path.dirname(input.output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        result_image.to_pil().save(input.output_path)

        return ImageGenOutput(output_image_path=input.output_path)

    def img2img(self, input: ImageGenImg2ImgInput) -> ImageGenOutput:
        """Generate an image from an initial image and a text prompt - public interface"""
        height = input.config.height
        width = input.config.width
        assert height % 16 == 0, f"Height must be divisible by 16 ({height}/16={height/16})"
        assert width % 16 == 0, f"Width must be divisible by 16 ({width}/16={width/16})"

        init_image = Image.from_pil(input.init_image_path)

        internal_config = SDImageGenerationConfig(
            prompts=input.prompt,
            negative_prompts=input.config.negative_prompts,
            height=height,
            width=width,
            sampler_config=ImageSamplerConfig(
                steps=input.config.sampler_config.steps,
                guidance_scale=input.config.sampler_config.guidance_scale,
                seed=input.config.sampler_config.seed
            ),
            init_image=init_image,
            strength=input.config.strength
        )

        result_image = self.sd_gen.img2img(
            init_image, input.prompt, internal_config)

        parent_dir = os.path.dirname(input.output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        result_image.to_pil().save(input.output_path)

        return ImageGenOutput(output_image_path=input.output_path)
