#!/usr/bin/env python3
"""
Command line interface for text-to-image generation using MLX backend.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

# Add the parent directory to the path to import the interface
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interface import ImageGen, ImageSamplerConfig
from ml import (
    ImageGenCreateInput, 
    ImageGenTxt2ImgInput, 
    ImageGenerationConfig, 
    ImageSamplerConfig as MLImageSamplerConfig,
    SchedulerConfig,
    ModelConfig
)


def create_default_config() -> ImageGenerationConfig:
    """Create a default image generation configuration."""
    sampler_config = MLImageSamplerConfig(
        method="ddim",
        steps=4,  # SDXL Turbo optimized
        guidance_scale=0.0,  # SDXL Turbo works well with no guidance
        eta=0.0,
        seed=-1
    )
    
    scheduler_config = SchedulerConfig(
        type="ddim",
        num_train_timesteps=1000,
        steps_offset=0,
        beta_start=0.00085,
        beta_end=0.012,
        beta_schedule="scaled_linear",
        prediction_type="epsilon",
        timestep_type="discrete",
        timestep_spacing="linspace",
        interpolation_type="linear"
    )
    
    return ImageGenerationConfig(
        prompts=[""],  # Will be set by user input
        sampler_config=sampler_config,
        scheduler_config=scheduler_config,
        strength=1.0,
        negative_prompts=None,
        height=512,
        width=512
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate images from text prompts using MLX backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "a beautiful sunset over mountains"
  python main.py "a cat sitting on a chair" --output output.png --width 1024 --height 1024
  python main.py "a futuristic city" --model-path ./models/sdxl-turbo --steps 8 --seed 42
        """
    )
    
    # Required arguments
    parser.add_argument(
        "prompt",
        help="Text prompt for image generation"
    )
    
    # Optional arguments
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output image path (default: generated_image.png)"
    )
    
    parser.add_argument(
        "--model-path", "-m",
        type=str,
        default="stabilityai/sdxl-turbo",
        help="Path to the model or HuggingFace model name (default: stabilityai/sdxl-turbo)"
    )
    
    parser.add_argument(
        "--width", "-w",
        type=int,
        default=512,
        help="Image width (must be divisible by 16, default: 512)"
    )
    
    parser.add_argument(
        "--height", "-h",
        type=int,
        default=512,
        help="Image height (must be divisible by 16, default: 512)"
    )
    
    parser.add_argument(
        "--steps", "-s",
        type=int,
        default=4,
        help="Number of denoising steps (default: 4 for SDXL Turbo)"
    )
    
    parser.add_argument(
        "--guidance-scale", "-g",
        type=float,
        default=0.0,
        help="Guidance scale (default: 0.0 for SDXL Turbo)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=-1,
        help="Random seed (-1 for random, default: -1)"
    )
    
    parser.add_argument(
        "--negative-prompt", "-n",
        type=str,
        help="Negative prompt to avoid certain elements"
    )
    
    parser.add_argument(
        "--device-id",
        type=str,
        help="Device ID to use (default: auto-detect)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """Validate command line arguments."""
    # Check dimensions are divisible by 16
    if args.width % 16 != 0:
        raise ValueError(f"Width must be divisible by 16, got {args.width}")
    if args.height % 16 != 0:
        raise ValueError(f"Height must be divisible by 16, got {args.height}")
    
    # Check steps is positive
    if args.steps <= 0:
        raise ValueError(f"Steps must be positive, got {args.steps}")
    
    # Check guidance scale is non-negative
    if args.guidance_scale < 0:
        raise ValueError(f"Guidance scale must be non-negative, got {args.guidance_scale}")


def main():
    """Main function for command line interface."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Validate arguments
        validate_arguments(args)
        
        # Set up output path
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = Path("generated_image.png")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if args.verbose:
            print(f"Initializing image generation...")
            print(f"Model: {args.model_path}")
            print(f"Prompt: {args.prompt}")
            print(f"Output: {output_path}")
            print(f"Dimensions: {args.width}x{args.height}")
            print(f"Steps: {args.steps}")
            print(f"Guidance scale: {args.guidance_scale}")
            print(f"Seed: {args.seed}")
            if args.negative_prompt:
                print(f"Negative prompt: {args.negative_prompt}")
        
        # Create model configuration
        model_config = ModelConfig(
            name="sdxl-turbo",
            version="1.0",
            description="SDXL Turbo model for fast image generation"
        )
        
        # Create image generator
        create_input = ImageGenCreateInput(
            model_name="sdxl-turbo",
            model_path=args.model_path,
            config=model_config,
            scheduler_config_path="",  # Not used for SDXL Turbo
            plugin_id="mlx",
            device_id=args.device_id
        )
        
        image_gen = ImageGen(create_input)
        
        # Create generation configuration
        sampler_config = MLImageSamplerConfig(
            method="ddim",
            steps=args.steps,
            guidance_scale=args.guidance_scale,
            eta=0.0,
            seed=args.seed
        )
        
        scheduler_config = SchedulerConfig(
            type="ddim",
            num_train_timesteps=1000,
            steps_offset=0,
            beta_start=0.00085,
            beta_end=0.012,
            beta_schedule="scaled_linear",
            prediction_type="epsilon",
            timestep_type="discrete",
            timestep_spacing="linspace",
            interpolation_type="linear"
        )
        
        generation_config = ImageGenerationConfig(
            prompts=[args.prompt],
            sampler_config=sampler_config,
            scheduler_config=scheduler_config,
            strength=1.0,
            negative_prompts=[args.negative_prompt] if args.negative_prompt else None,
            height=args.height,
            width=args.width
        )
        
        # Create text-to-image input
        txt2img_input = ImageGenTxt2ImgInput(
            prompt=args.prompt,
            config=generation_config,
            output_path=str(output_path)
        )
        
        if args.verbose:
            print("Generating image...")
        
        # Generate image
        result = image_gen.txt2img(txt2img_input)
        
        if args.verbose:
            print(f"Image generated successfully!")
            print(f"Saved to: {result.output_image_path}")
        else:
            print(f"Image saved to: {result.output_image_path}")
        
        # Clean up
        image_gen.close()
        
    except KeyboardInterrupt:
        print("\nGeneration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
