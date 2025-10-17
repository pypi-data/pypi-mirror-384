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

import sys
import os
import json
import mlx.core as mx
import numpy as np

curr_dir = os.path.dirname(os.path.abspath(__file__))
from .modeling.nexa_jina_v2 import Model, ModelArgs
from tokenizers import Tokenizer
from huggingface_hub import snapshot_download

# Try to import mlx_embeddings for general embedding support
try:
    import mlx_embeddings
    MLX_EMBEDDINGS_AVAILABLE = True
except ImportError:
    MLX_EMBEDDINGS_AVAILABLE = False
    # Suppress warning during import to avoid interfering with C++ tests
    # The warning will be shown when actually trying to use mlx_embeddings functionality
    pass

def detect_model_type(model_path):
    """Detect if the model is Jina V2 or generic mlx_embeddings model."""
    config_path = os.path.join(model_path, "config.json") if os.path.isdir(model_path) else f"{model_path}/config.json"
    
    if not os.path.exists(config_path):
        # Try default modelfiles directory
        config_path = f"{curr_dir}/modelfiles/config.json"
        if not os.path.exists(config_path):
            return "generic"
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Check if it's a Jina V2 model
        architectures = config.get("architectures", [])
        if "JinaBertModel" in architectures:
            return "jina_v2"
        
        return "generic"
    except Exception:
        return "generic"

# ========== Jina V2 Direct Implementation ==========

def load_jina_model(model_id):
    """Initialize and load the Jina V2 model with FP16 weights."""
    # Load configuration from config.json
    if not os.path.exists(f"{curr_dir}/modelfiles/config.json"):
        print(f"📥 Downloading Jina V2 model {model_id}...")
        
        # Ensure modelfiles directory exists
        os.makedirs(f"{curr_dir}/modelfiles", exist_ok=True)
        
        try:
            # Download model with progress indication
            snapshot_download(
                repo_id=model_id, 
                local_dir=f"{curr_dir}/modelfiles",
                resume_download=True,  # Resume partial downloads
                local_dir_use_symlinks=False  # Use actual files instead of symlinks
            )
            print("✅ Model download completed!")
        except Exception as e:
            print(f"❌ Failed to download model: {e}")
            print("💡 Try: huggingface-cli login (if authentication required)")
            raise

    with open(f"{curr_dir}/modelfiles/config.json", "r") as f:
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
    
    # Initialize model
    model = Model(config)
    
    # Load FP16 weights
    model.load_weights(f"{curr_dir}/modelfiles/model.safetensors", strict=True)
    model.eval()
    
    return model

def load_jina_tokenizer():
    """Load and configure the tokenizer for Jina V2."""
    tokenizer = Tokenizer.from_file(f"{curr_dir}/modelfiles/tokenizer.json")
    tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
    tokenizer.enable_truncation(max_length=512)
    return tokenizer

def encode_jina_text(model, tokenizer, text):
    """Encode a single text using Jina V2 and return its embedding."""
    # Tokenize the text
    encoding = tokenizer.encode(text)
    
    # Prepare inputs
    input_ids = np.array([encoding.ids], dtype=np.int32)
    attention_mask = np.array([encoding.attention_mask], dtype=np.float32)
    token_type_ids = np.array([encoding.type_ids if encoding.type_ids else [0] * len(encoding.ids)], dtype=np.int32)
    
    # Convert to MLX arrays
    input_ids = mx.array(input_ids)
    attention_mask = mx.array(attention_mask)
    token_type_ids = mx.array(token_type_ids)
    
    # Get embeddings
    embeddings = model.encode(
        input_ids=input_ids,
        attention_mask=attention_mask,
        token_type_ids=token_type_ids,
    )
    
    return embeddings

# ========== MLX Embeddings Direct Implementation ==========

def load_mlx_embeddings_model(model_id):
    """Load model using mlx_embeddings package."""
    if not MLX_EMBEDDINGS_AVAILABLE:
        print("Warning: mlx_embeddings not available. Please install it to use general embedding models.")
        raise ImportError("mlx_embeddings package is not available. Please install it first.")
    
    # Download model if needed
    model_path = f"{curr_dir}/modelfiles"
    
    if not os.path.exists(f"{model_path}/config.json"):
        print(f"📥 Downloading model {model_id}...")
        os.makedirs(model_path, exist_ok=True)
        
        try:
            snapshot_download(
                repo_id=model_id,
                local_dir=model_path,
                resume_download=True,
                local_dir_use_symlinks=False
            )
            print("✅ Model download completed!")
        except Exception as e:
            print(f"❌ Failed to download model: {e}")
            raise
    
    # Load model and tokenizer using mlx_embeddings
    model, tokenizer = mlx_embeddings.load(model_path)
    return model, tokenizer

def encode_mlx_embeddings_text(model, tokenizer, texts, model_path=None):
    """Generate embeddings using mlx_embeddings."""
    if isinstance(texts, str):
        texts = [texts]
    
    # Check if this is a Gemma3TextModel by checking config
    # WORKAROUND: Gemma3TextModel has a bug where it expects 'inputs' as positional arg
    # but mlx_embeddings.generate passes 'input_ids' as keyword arg
    # See: https://github.com/ml-explore/mlx-examples/issues/... (bug report pending)
    is_gemma = False
    if model_path:
        config_path = os.path.join(model_path, "config.json") if os.path.isdir(model_path) else f"{model_path}/config.json"
    else:
        config_path = f"{curr_dir}/modelfiles/config.json"
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                architectures = config.get("architectures", [])
                is_gemma = "Gemma3TextModel" in architectures
        except Exception:
            pass
    
    if is_gemma:
        # HARDCODED WORKAROUND for Gemma3TextModel bug
        # Use direct tokenization and model call instead of mlx_embeddings.generate
        # This avoids the bug where generate passes 'input_ids' as keyword arg
        # but Gemma3TextModel.__call__ expects 'inputs' as positional arg
        
        # Tokenize using batch_encode_plus for Gemma models
        encoded_input = tokenizer.batch_encode_plus(
            texts,
            padding=True,
            truncation=True,
            return_tensors='mlx',
            max_length=512
        )
        
        # Get input tensors
        input_ids = encoded_input['input_ids']
        attention_mask = encoded_input.get('attention_mask', None)
        
        # Call model with positional input_ids and keyword attention_mask
        # This matches Gemma3TextModel's expected signature:
        # def __call__(self, inputs: mx.array, attention_mask: Optional[mx.array] = None)
        output = model(input_ids, attention_mask=attention_mask)
        
        # Get the normalized embeddings
        return output.text_embeds
    else:
        # Normal path for non-Gemma models
        # Use standard mlx_embeddings.generate approach
        output = mlx_embeddings.generate(
            model,
            tokenizer,
            texts=texts,
            max_length=512,
            padding=True,
            truncation=True
        )
        
        return output.text_embeds

def main(model_id):
    """Main function to handle user input and generate embeddings."""
    
    print(f"🔍 Loading model: {model_id}")
    
    # Detect model type
    model_type = detect_model_type(f"{curr_dir}/modelfiles")
    
    # First try to download/check if model exists
    if not os.path.exists(f"{curr_dir}/modelfiles/config.json"):
        # Download the model first to detect its type
        print(f"Model not found locally. Downloading...")
        os.makedirs(f"{curr_dir}/modelfiles", exist_ok=True)
        try:
            snapshot_download(
                repo_id=model_id, 
                local_dir=f"{curr_dir}/modelfiles",
                resume_download=True,
                local_dir_use_symlinks=False
            )
            print("✅ Model download completed!")
            # Re-detect model type after download
            model_type = detect_model_type(f"{curr_dir}/modelfiles")
        except Exception as e:
            print(f"❌ Failed to download model: {e}")
            raise
    
    print(f"📦 Detected model type: {model_type}")
    
    # Test texts
    test_texts = [
        "Hello, how are you?",
        "What is machine learning?",
        "The weather is nice today."
    ]
    
    if model_type == "jina_v2":
        print("Using Jina V2 direct implementation")
        
        # Load Jina V2 model
        model = load_jina_model(model_id)
        tokenizer = load_jina_tokenizer()
        
        print("\nGenerating embeddings for test texts:")
        for text in test_texts:
            embedding = encode_jina_text(model, tokenizer, text)
            print(f"\nText: '{text}'")
            print(f"  Embedding shape: {embedding.shape}")
            print(f"  Sample values (first 5): {embedding.flatten()[:5].tolist()}")
            print(f"  Stats - Min: {embedding.min():.4f}, Max: {embedding.max():.4f}, Mean: {embedding.mean():.4f}")
    
    else:
        print("Using mlx_embeddings direct implementation")
        
        if not MLX_EMBEDDINGS_AVAILABLE:
            print("❌ mlx_embeddings is not installed. Please install it to use generic models.")
            return
        
        # Load generic model using mlx_embeddings
        model, tokenizer = load_mlx_embeddings_model(model_id)
        
        print("\nGenerating embeddings for test texts:")
        # Pass model_path to handle Gemma workaround if needed
        embeddings = encode_mlx_embeddings_text(model, tokenizer, test_texts, model_path=f"{curr_dir}/modelfiles")
        
        for i, text in enumerate(test_texts):
            embedding = embeddings[i]
            print(f"\nText: '{text}'")
            print(f"  Embedding shape: {embedding.shape}")
            print(f"  Sample values (first 5): {embedding[:5].tolist()}")
            
            # Calculate stats
            emb_array = mx.array(embedding) if not isinstance(embedding, mx.array) else embedding
            print(f"  Stats - Min: {emb_array.min():.4f}, Max: {emb_array.max():.4f}, Mean: {emb_array.mean():.4f}")
    
    print("\n✅ Direct embedding generation completed!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate embeddings using direct implementation")
    parser.add_argument(
        "--model_id", 
        type=str, 
        default="nexaml/jina-v2-fp16-mlx",
        help="Model ID from Hugging Face Hub (e.g., 'nexaml/jina-v2-fp16-mlx' or 'mlx-community/embeddinggemma-300m-bf16')"
    )
    args = parser.parse_args()
    main(args.model_id)