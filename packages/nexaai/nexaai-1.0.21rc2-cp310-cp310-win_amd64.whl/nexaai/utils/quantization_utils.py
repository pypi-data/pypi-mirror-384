"""
Quantization utilities for extracting quantization types from model files and configurations.

This module provides utilities to extract quantization information from:
- GGUF model filenames
- MLX model repository IDs  
- MLX model config.json files
"""

import os
import json
import re
import logging
from enum import Enum
from typing import Optional

# Set up logger
logger = logging.getLogger(__name__)


class QuantizationType(str, Enum):
    """Enum for GGUF and MLX model quantization types."""
    # GGUF quantization types
    BF16 = "BF16"
    F16 = "F16"
    Q2_K = "Q2_K"
    Q2_K_L = "Q2_K_L"
    Q3_K = "Q3_K"
    Q3_K_M = "Q3_K_M"
    Q3_K_S = "Q3_K_S"
    Q4_0 = "Q4_0"
    Q4_1 = "Q4_1"
    Q4_K = "Q4_K"
    Q4_K_M = "Q4_K_M"
    Q4_K_S = "Q4_K_S"
    Q5_K = "Q5_K"
    Q5_K_M = "Q5_K_M"
    Q5_K_S = "Q5_K_S"
    Q6_K = "Q6_K"
    Q8_0 = "Q8_0"
    MXFP4 = "MXFP4"
    MXFP8 = "MXFP8"
    
    # MLX bit-based quantization types
    BIT_1 = "1BIT"
    BIT_2 = "2BIT"
    BIT_3 = "3BIT"
    BIT_4 = "4BIT"
    BIT_5 = "5BIT"
    BIT_6 = "6BIT"
    BIT_7 = "7BIT"
    BIT_8 = "8BIT"
    BIT_16 = "16BIT"


def extract_quantization_from_filename(filename: str) -> Optional[QuantizationType]:
    """
    Extract quantization type from filename.
    
    Args:
        filename: The filename to extract quantization from
        
    Returns:
        QuantizationType enum value or None if not found
    """
    # Define mapping from lowercase patterns to enum values
    # Include "." to ensure precise matching (e.g., "q4_0." not "q4_0_xl")
    pattern_to_enum = {
        'bf16.': QuantizationType.BF16,
        'f16.': QuantizationType.F16,  # Add F16 support
        'q2_k_l.': QuantizationType.Q2_K_L,  # Check Q2_K_L before Q2_K to avoid partial match
        'q2_k.': QuantizationType.Q2_K,
        'q3_k.': QuantizationType.Q3_K,
        'q3_k_m.': QuantizationType.Q3_K_M,
        'q3_k_s.': QuantizationType.Q3_K_S,
        'q4_k_m.': QuantizationType.Q4_K_M,
        'q4_k_s.': QuantizationType.Q4_K_S,
        'q4_0.': QuantizationType.Q4_0,
        'q4_1.': QuantizationType.Q4_1,
        'q4_k.': QuantizationType.Q4_K,
        'q5_k.': QuantizationType.Q5_K,
        'q5_k_m.': QuantizationType.Q5_K_M,
        'q5_k_s.': QuantizationType.Q5_K_S,
        'q6_k.': QuantizationType.Q6_K,
        'q8_0.': QuantizationType.Q8_0,
        'mxfp4.': QuantizationType.MXFP4,
        'mxfp8.': QuantizationType.MXFP8,
    }
    
    filename_lower = filename.lower()
    
    # Check longer patterns first to avoid partial matches
    # Sort by length descending to check q2_k_l before q2_k, q4_k_m before q4_0, etc.
    for pattern in sorted(pattern_to_enum.keys(), key=len, reverse=True):
        if pattern in filename_lower:
            return pattern_to_enum[pattern]
    
    return None


def extract_quantization_from_repo_id(repo_id: str) -> Optional[QuantizationType]:
    """
    Extract quantization type from repo_id for MLX models by looking for bit patterns.
    
    Args:
        repo_id: The repository ID to extract quantization from
        
    Returns:
        QuantizationType enum value or None if not found
    """
    # Define mapping from bit numbers to enum values
    bit_to_enum = {
        1: QuantizationType.BIT_1,
        2: QuantizationType.BIT_2,
        3: QuantizationType.BIT_3,
        4: QuantizationType.BIT_4,
        5: QuantizationType.BIT_5,
        6: QuantizationType.BIT_6,
        7: QuantizationType.BIT_7,
        8: QuantizationType.BIT_8,
        16: QuantizationType.BIT_16,
    }
    
    # First check for patterns like "4bit", "8bit" etc. (case insensitive)
    pattern = r'(\d+)bit'
    matches = re.findall(pattern, repo_id.lower())
    
    for match in matches:
        try:
            bit_number = int(match)
            if bit_number in bit_to_enum:
                logger.debug(f"Found {bit_number}bit quantization in repo_id: {repo_id}")
                return bit_to_enum[bit_number]
        except ValueError:
            continue
    
    # Also check for patterns like "-q8", "_Q4" etc.
    q_pattern = r'[-_]q(\d+)'
    q_matches = re.findall(q_pattern, repo_id.lower())
    
    for match in q_matches:
        try:
            bit_number = int(match)
            if bit_number in bit_to_enum:
                logger.debug(f"Found Q{bit_number} quantization in repo_id: {repo_id}")
                return bit_to_enum[bit_number]
        except ValueError:
            continue
    
    return None


def extract_quantization_from_mlx_config(mlx_folder_path: str) -> Optional[QuantizationType]:
    """
    Extract quantization type from MLX model's config.json file.
    
    Args:
        mlx_folder_path: Path to the MLX model folder
        
    Returns:
        QuantizationType enum value or None if not found
    """
    config_path = os.path.join(mlx_folder_path, "config.json")
    
    if not os.path.exists(config_path):
        logger.debug(f"Config file not found: {config_path}")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Look for quantization.bits field
        quantization_config = config.get("quantization", {})
        if isinstance(quantization_config, dict):
            bits = quantization_config.get("bits")
            if isinstance(bits, int):
                # Define mapping from bit numbers to enum values
                bit_to_enum = {
                    1: QuantizationType.BIT_1,
                    2: QuantizationType.BIT_2,
                    3: QuantizationType.BIT_3,
                    4: QuantizationType.BIT_4,
                    5: QuantizationType.BIT_5,
                    6: QuantizationType.BIT_6,
                    7: QuantizationType.BIT_7,
                    8: QuantizationType.BIT_8,
                    16: QuantizationType.BIT_16,
                }
                
                if bits in bit_to_enum:
                    logger.debug(f"Found {bits}bit quantization in config.json: {config_path}")
                    return bit_to_enum[bits]
                else:
                    logger.debug(f"Unsupported quantization bits value: {bits}")
        
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error reading config.json from {config_path}: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error reading config.json from {config_path}: {e}")
    
    return None


def extract_gguf_quantization(filename: str) -> str:
    """
    Extract quantization level from GGUF filename using the enum-based approach.
    
    This function provides backward compatibility by returning a string representation
    of the quantization type.
    
    Args:
        filename: The GGUF filename
        
    Returns:
        String representation of the quantization type or "UNKNOWN" if not found
    """
    quantization_type = extract_quantization_from_filename(filename)
    if quantization_type:
        return quantization_type.value
    return "UNKNOWN"


def detect_quantization_for_mlx(repo_id: str, directory_path: str) -> Optional[QuantizationType]:
    """
    Detect quantization for MLX models using multiple methods in priority order.
    
    Args:
        repo_id: The repository ID
        directory_path: Path to the model directory
        
    Returns:
        QuantizationType enum value or None if not found
    """
    # Method 1: Extract from repo_id
    quantization_type = extract_quantization_from_repo_id(repo_id)
    if quantization_type:
        return quantization_type
    
    # Method 2: Extract from config.json if available
    quantization_type = extract_quantization_from_mlx_config(directory_path)
    if quantization_type:
        return quantization_type
    
    return None
