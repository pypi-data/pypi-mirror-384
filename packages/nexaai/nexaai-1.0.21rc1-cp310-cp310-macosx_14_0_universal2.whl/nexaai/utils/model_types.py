"""
Model type mappings for HuggingFace pipeline tags to our internal model types.

This module provides centralized model type mapping functionality to avoid
circular imports between other utility modules.
"""

from enum import Enum
from typing import Dict


class ModelTypeMapping(Enum):
    """Enum for mapping HuggingFace pipeline_tag to our ModelType."""
    TEXT_GENERATION = ("text-generation", "llm")
    IMAGE_TEXT_TO_TEXT = ("image-text-to-text", "vlm")
    ANY_TO_ANY = ("any-to-any", "ata")
    AUTOMATIC_SPEECH_RECOGNITION = ("automatic-speech-recognition", "asr")
    
    def __init__(self, pipeline_tag: str, model_type: str):
        self.pipeline_tag = pipeline_tag
        self.model_type = model_type


# Create mapping dictionaries from the enum
PIPELINE_TO_MODEL_TYPE: Dict[str, str] = {
    mapping.pipeline_tag: mapping.model_type 
    for mapping in ModelTypeMapping
}

MODEL_TYPE_TO_PIPELINE: Dict[str, str] = {
    mapping.model_type: mapping.pipeline_tag 
    for mapping in ModelTypeMapping
}


def map_pipeline_tag_to_model_type(pipeline_tag: str) -> str:
    """Map HuggingFace pipeline_tag to our ModelType."""
    if not pipeline_tag:
        return "other"
    
    return PIPELINE_TO_MODEL_TYPE.get(pipeline_tag, "other")


def map_model_type_to_pipeline_tag(model_type: str) -> str:
    """Reverse map ModelType back to HuggingFace pipeline_tag."""
    if not model_type:
        return None
    
    return MODEL_TYPE_TO_PIPELINE.get(model_type)
