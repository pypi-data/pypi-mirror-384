# Copyright © Nexa AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import os
import json
import mlx.core as mx
import numpy as np
from pathlib import Path
from typing import Any, List, Optional, Sequence
from abc import ABC, abstractmethod

# Import necessary modules 
from tokenizers import Tokenizer

# Import from ml.py for API alignment
import sys
from pathlib import Path as PathLib
sys.path.insert(0, str(PathLib(__file__).parent.parent))

from ml import (
    Embedder as BaseEmbedder,
    EmbeddingConfig,
    Path as PathType,
)

# Import profiling module
from profiling import ProfilingMixin, StopReason

# Import the model implementation for Jina
try:
    from .modeling.nexa_jina_v2 import Model, ModelArgs
except ImportError:
    # Fallback for when module is run directly
    from modeling.nexa_jina_v2 import Model, ModelArgs

# Import mlx_embeddings for general embedding support
try:
    import mlx_embeddings
    MLX_EMBEDDINGS_AVAILABLE = True
except ImportError:
    MLX_EMBEDDINGS_AVAILABLE = False


class BaseMLXEmbedder(BaseEmbedder, ProfilingMixin, ABC):
    """
    Abstract base embedder interface for MLX embedding models.
    API aligned with ml.py Embedder abstract base class.
    """

    def __init__(
        self,
        model_path: PathType,
        tokenizer_path: PathType,
        device: Optional[str] = None,
    ) -> None:
        """Initialize the Embedder model."""
        # Initialize profiling mixin
        ProfilingMixin.__init__(self)

        # Store paths
        if (os.path.isfile(model_path)):
            model_path = os.path.dirname(model_path)

        # Call parent constructor
        # MLX manages device automatically, so we pass None for device
        super().__init__(model_path, tokenizer_path, device)
        
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path
        self.device = device if device is not None else "cpu"
        
        # Initialize model and tokenizer as None
        self.model = None
        self.tokenizer = None
        self.config = None

    def destroy(self) -> None:
        """Destroy the model and free resources."""
        self.model = None
        self.tokenizer = None
        self.config = None
        self.reset_profiling()

    @abstractmethod
    def load_model(self, model_path: PathType) -> bool:
        """Load model from path."""
        pass

    def close(self) -> None:
        """Close the model."""
        self.destroy()

    @abstractmethod
    def embed(
        self,
        texts: Sequence[str],
        config: Optional[EmbeddingConfig] = None,
        clear_cache: bool = True,
    ) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass

    @abstractmethod
    def embedding_dim(self) -> int:
        """Get embedding dimension."""
        pass

    def set_lora(self, lora_id: int) -> None:
        """Set active LoRA adapter. (Disabled for embedding models)"""
        raise NotImplementedError("LoRA is not supported for embedding models")

    def add_lora(self, lora_path: PathType) -> int:
        """Add LoRA adapter and return its ID. (Disabled for embedding models)"""
        raise NotImplementedError("LoRA is not supported for embedding models")

    def remove_lora(self, lora_id: int) -> None:
        """Remove LoRA adapter. (Disabled for embedding models)"""
        raise NotImplementedError("LoRA is not supported for embedding models")

    def list_loras(self) -> List[int]:
        """List available LoRA adapters. (Disabled for embedding models)"""
        raise NotImplementedError("LoRA is not supported for embedding models")

    def _normalize_embedding(self, embedding: List[float], method: str) -> List[float]:
        """Normalize embedding using specified method."""
        if method == "none":
            return embedding
        
        embedding_array = np.array(embedding)
        
        if method == "l2":
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm
        elif method == "mean":
            mean_val = np.mean(embedding_array)
            embedding_array = embedding_array - mean_val
        
        return embedding_array.tolist()


class JinaV2Embedder(BaseMLXEmbedder):
    """
    Embedder implementation specifically for Jina V2 models.
    """

    def load_model(self, model_path: PathType) -> bool:
        """Load model from path."""
        try:
            # Use the provided model_path or fall back to instance path
            if model_path:
                # Apply same file-to-directory conversion as in __init__
                if os.path.isfile(model_path):
                    model_path = os.path.dirname(model_path)
                self.model_path = model_path
            
            # Load the model using internal implementation
            self.model = self._load_jina_model(self.model_path)
            self.tokenizer = self._load_tokenizer()
            
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

    def embed(
        self,
        texts: Sequence[str],
        config: Optional[EmbeddingConfig] = None,
        clear_cache: bool = True,
    ) -> List[List[float]]:
        """Generate embeddings for texts."""
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        if config is None:
            config = EmbeddingConfig()
        
        # Start profiling
        self._start_profiling()
        
        # Calculate total tokens for all texts
        total_tokens = sum(len(self.tokenizer.encode(text).ids) for text in texts)
        self._update_prompt_tokens(total_tokens)
        
        # End prompt processing, start decode
        self._prompt_end()
        self._decode_start()
        
        try:
            embeddings = []
            
            # Process texts in batches
            batch_size = config.batch_size
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self._encode_batch(batch_texts, config)
                embeddings.extend(batch_embeddings)
            
            if clear_cache:
                mx.clear_cache()
            
            # End timing and finalize profiling data
            self._update_generated_tokens(0)  # No generation in embedding
            self._set_stop_reason(StopReason.ML_STOP_REASON_COMPLETED)
            self._decode_end()
            self._end_profiling()
            
            return embeddings
            
        except Exception as e:
            self._set_stop_reason(StopReason.ML_STOP_REASON_UNKNOWN)
            self._decode_end()
            self._end_profiling()
            raise RuntimeError(f"Error generating embeddings: {str(e)}")

    def embedding_dim(self) -> int:
        """Get embedding dimension."""
        if self.config is None:
            return 768  # Default dimension for Jina v2
        return self.config.hidden_size

    def _load_jina_model(self, model_dir: str) -> Model:
        """Initialize and load the Jina V2 model with FP16 weights."""
        
        # Validate that model path exists
        if not os.path.exists(model_dir):
            raise ValueError(f"Model path does not exist: {model_dir}")
            
        print(f"Using local model path: {model_dir}")
        config_path = os.path.join(model_dir, "config.json")
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            config_dict = json.load(f)
        
        # Create ModelArgs from loaded config
        config = ModelArgs(
            model_type=config_dict["model_type"],
            vocab_size=config_dict["vocab_size"],
            hidden_size=config_dict["hidden_size"],
            num_hidden_layers=config_dict["num_hidden_layers"],
            num_attention_heads=config_dict["num_attention_heads"],
            intermediate_size=config_dict["intermediate_size"],
            hidden_act=config_dict["hidden_act"],
            hidden_dropout_prob=config_dict["hidden_dropout_prob"],
            attention_probs_dropout_prob=config_dict["attention_probs_dropout_prob"],
            max_position_embeddings=config_dict["max_position_embeddings"],
            type_vocab_size=config_dict["type_vocab_size"],
            initializer_range=config_dict["initializer_range"],
            layer_norm_eps=config_dict["layer_norm_eps"],
            pad_token_id=config_dict["pad_token_id"],
            position_embedding_type=config_dict["position_embedding_type"],
            use_cache=config_dict["use_cache"],
            classifier_dropout=config_dict["classifier_dropout"],
            feed_forward_type=config_dict["feed_forward_type"],
            emb_pooler=config_dict["emb_pooler"],
            attn_implementation=config_dict["attn_implementation"],
        )
        
        # Store config for embedding_dim()
        self.config = config
        
        # Initialize model
        model = Model(config)
        
        # Load FP16 weights from model path
        weights_path = os.path.join(model_dir, "model.safetensors")
        self._model_dir = model_dir
        
        # Validate that weights file exists
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"Model weights file not found: {weights_path}")
            
        model.load_weights(weights_path, strict=True)
        model.eval()
        
        return model

    def _load_tokenizer(self) -> Tokenizer:
        """Load and configure the tokenizer."""
        tokenizer_path = os.path.join(self._model_dir, "tokenizer.json")
        tokenizer = Tokenizer.from_file(tokenizer_path)
        tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        tokenizer.enable_truncation(max_length=512)
        return tokenizer

    def _encode_batch(self, texts: List[str], config: EmbeddingConfig) -> List[List[float]]:
        """Encode a batch of texts and return their embeddings."""
        embeddings = []
        
        for text in texts:
            embedding = self._encode_single_text(text, config)
            embeddings.append(embedding)
        
        return embeddings

    def _encode_single_text(self, text: str, config: EmbeddingConfig) -> List[float]:
        """Encode a single text and return its embedding."""
        # Tokenize the text
        encoding = self.tokenizer.encode(text)
        
        # Prepare inputs
        input_ids = np.array([encoding.ids], dtype=np.int32)
        attention_mask = np.array([encoding.attention_mask], dtype=np.float32)
        token_type_ids = np.array([encoding.type_ids if encoding.type_ids else [0] * len(encoding.ids)], dtype=np.int32)
        
        # Convert to MLX arrays
        input_ids = mx.array(input_ids)
        attention_mask = mx.array(attention_mask)
        token_type_ids = mx.array(token_type_ids)
        
        # Get embeddings
        embeddings = self.model.encode(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        
        # Convert to list and apply normalization if requested
        embedding_list = embeddings.flatten().tolist()
        
        if config.normalize:
            embedding_list = self._normalize_embedding(embedding_list, config.normalize_method)
        
        return embedding_list


class MlxEmbeddingEmbedder(BaseMLXEmbedder):
    """
    Embedder implementation using mlx_embeddings package for general embedding models.
    """

    def load_model(self, model_path: PathType) -> bool:
        """Load model from path using mlx_embeddings."""
        if not MLX_EMBEDDINGS_AVAILABLE:
            print("Warning: mlx_embeddings not available. Please install it to use general embedding models.")
            raise ImportError("mlx_embeddings package is not available. Please install it first.")
        
        try:
            # Use the provided model_path or fall back to instance path
            if model_path:
                if os.path.isfile(model_path):
                    model_path = os.path.dirname(model_path)
                self.model_path = model_path
            
            # Load model and tokenizer using mlx_embeddings
            self.model, self.tokenizer = mlx_embeddings.load(self.model_path)
            
            # Load config to get dimensions
            config_path = os.path.join(self.model_path, "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    self.config = json.load(f)
            
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

    def embed(
        self,
        texts: Sequence[str],
        config: Optional[EmbeddingConfig] = None,
        clear_cache: bool = True,
    ) -> List[List[float]]:
        """Generate embeddings for texts using mlx_embeddings."""
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        if config is None:
            config = EmbeddingConfig()
        
        # Start profiling
        self._start_profiling()
        
        try:
            # Calculate total tokens for profiling
            if hasattr(self.tokenizer, 'encode'):
                total_tokens = sum(len(self.tokenizer.encode(text)) for text in texts)
            else:
                # For tokenizers that don't have simple encode method
                total_tokens = len(texts) * 50  # Rough estimate
            
            self._update_prompt_tokens(total_tokens)
            
            # End prompt processing, start decode
            self._prompt_end()
            self._decode_start()
            
            # Check if this is a Gemma3TextModel
            # WORKAROUND: Gemma3TextModel has a bug where it expects 'inputs' as positional arg
            # but mlx_embeddings.generate passes 'input_ids' as keyword arg
            # See: https://github.com/ml-explore/mlx-examples/issues/... (bug report pending)
            is_gemma = False
            if self.config and "architectures" in self.config:
                architectures = self.config.get("architectures", [])
                is_gemma = "Gemma3TextModel" in architectures
            
            if is_gemma:
                # HARDCODED WORKAROUND for Gemma3TextModel bug
                # Use direct tokenization and model call instead of mlx_embeddings.generate
                max_length = config.max_length if hasattr(config, 'max_length') else 512
                
                # Tokenize using batch_encode_plus
                encoded_input = self.tokenizer.batch_encode_plus(
                    list(texts),
                    padding=True,
                    truncation=True,
                    return_tensors='mlx',
                    max_length=max_length
                )
                
                # Get input tensors
                input_ids = encoded_input['input_ids']
                attention_mask = encoded_input.get('attention_mask', None)
                
                # Call model with positional input_ids and keyword attention_mask
                # This matches Gemma3TextModel's expected signature
                output = self.model(input_ids, attention_mask=attention_mask)
                
                # Extract embeddings
                embeddings_tensor = output.text_embeds
            else:
                # Normal path for non-Gemma models
                # Generate embeddings using mlx_embeddings standard approach
                output = mlx_embeddings.generate(
                    self.model,
                    self.tokenizer,
                    texts=list(texts),
                    max_length=config.max_length if hasattr(config, 'max_length') else 512,
                    padding=True,
                    truncation=True
                )
                
                # Extract embeddings
                embeddings_tensor = output.text_embeds
            
            # Convert to list format
            embeddings = []
            for i in range(embeddings_tensor.shape[0]):
                embedding = embeddings_tensor[i].tolist()
                
                # Apply normalization if requested
                if config.normalize:
                    embedding = self._normalize_embedding(embedding, config.normalize_method)
                
                embeddings.append(embedding)
            
            if clear_cache:
                mx.clear_cache()
            
            # End timing and finalize profiling data
            self._update_generated_tokens(0)  # No generation in embedding
            self._set_stop_reason(StopReason.ML_STOP_REASON_COMPLETED)
            self._decode_end()
            self._end_profiling()
            
            return embeddings
            
        except Exception as e:
            self._set_stop_reason(StopReason.ML_STOP_REASON_UNKNOWN)
            self._decode_end()
            self._end_profiling()
            raise RuntimeError(f"Error generating embeddings: {str(e)}")

    def embedding_dim(self) -> int:
        """Get embedding dimension."""
        if self.config is None:
            return 768  # Default dimension
        
        # Try different config keys that might contain the dimension
        if "hidden_size" in self.config:
            return self.config["hidden_size"]
        elif "d_model" in self.config:
            return self.config["d_model"]
        elif "dim" in self.config:
            return self.config["dim"]
        else:
            return 768  # Fallback default


class MLXEmbedder(BaseMLXEmbedder):
    """
    Concrete embedder class that routes to the appropriate implementation.
    This class can be instantiated directly (for C++ compatibility) and will
    automatically delegate to JinaV2Embedder or MlxEmbeddingEmbedder based on model type.
    """
    
    def __init__(
        self,
        model_path: PathType,
        tokenizer_path: PathType,
        device: Optional[str] = None,
    ) -> None:
        """Initialize the Embedder model."""
        super().__init__(model_path, tokenizer_path, device)
        self._impl = None  # Will hold the actual implementation
    
    def _get_implementation(self) -> BaseMLXEmbedder:
        """Get or create the appropriate implementation based on model type."""
        if self._impl is None:
            # Detect model type and create appropriate implementation
            model_type = _detect_model_type(self.model_path)
            
            if model_type == "jina_v2":
                self._impl = JinaV2Embedder(self.model_path, self.tokenizer_path, self.device)
            else:
                self._impl = MlxEmbeddingEmbedder(self.model_path, self.tokenizer_path, self.device)
            
            # Copy over any existing state
            if self.model is not None:
                self._impl.model = self.model
            if self.tokenizer is not None:
                self._impl.tokenizer = self.tokenizer
            if self.config is not None:
                self._impl.config = self.config
        
        return self._impl
    
    def load_model(self, model_path: PathType) -> bool:
        """Load model from path."""
        # Get the appropriate implementation and delegate
        impl = self._get_implementation()
        result = impl.load_model(model_path)
        
        # Sync state back
        self.model = impl.model
        self.tokenizer = impl.tokenizer
        self.config = impl.config
        
        return result
    
    def embed(
        self,
        texts: Sequence[str],
        config: Optional[EmbeddingConfig] = None,
        clear_cache: bool = True,
    ) -> List[List[float]]:
        """Generate embeddings for texts."""
        # Get the appropriate implementation and delegate
        impl = self._get_implementation()
        return impl.embed(texts, config, clear_cache)
    
    def embedding_dim(self) -> int:
        """Get embedding dimension."""
        # Get the appropriate implementation and delegate
        impl = self._get_implementation()
        return impl.embedding_dim()
    
    def destroy(self) -> None:
        """Destroy the model and free resources."""
        super().destroy()
        if self._impl is not None:
            self._impl.destroy()
            self._impl = None


# Backward compatibility alias
Embedder = MLXEmbedder


def _detect_model_type(model_path: PathType) -> str:
    """Detect the model type from config.json."""
    if os.path.isfile(model_path):
        model_path = os.path.dirname(model_path)
    
    config_path = os.path.join(model_path, "config.json")
    
    if not os.path.exists(config_path):
        # If no config.json, assume it's a generic model
        return "generic"
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Check architectures field for JinaBertModel
        architectures = config.get("architectures", [])
        if "JinaBertModel" in architectures:
            return "jina_v2"
        
        # Default to generic mlx_embeddings for other models
        return "generic"
    
    except Exception as e:
        print(f"Warning: Could not parse config.json: {e}")
        return "generic"


# Factory function for creating embedder instances
def create_embedder(
    model_path: PathType,
    tokenizer_path: Optional[PathType] = None,
    device: Optional[str] = None,
) -> MLXEmbedder:
    """Create and return an MLXEmbedder instance that automatically routes to the appropriate implementation."""
    if tokenizer_path is None:
        tokenizer_path = model_path
    
    # Return the concrete MLXEmbedder which will handle routing internally
    return MLXEmbedder(model_path, tokenizer_path, device)