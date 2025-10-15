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

import os
import sys
import numpy as np
from pathlib import Path

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from interface (uses the factory pattern with routing)
from .interface import create_embedder
from .interface import EmbeddingConfig
from huggingface_hub import snapshot_download


def download_model_if_needed(model_id, local_dir):
    """Download model from Hugging Face Hub if not present locally."""
    if not os.path.exists(os.path.join(local_dir, "config.json")):
        print(f"📥 Model not found locally. Downloading {model_id}...")
        os.makedirs(local_dir, exist_ok=True)
        try:
            snapshot_download(
                repo_id=model_id,
                local_dir=local_dir,
                resume_download=True,
                local_dir_use_symlinks=False
            )
            print("✅ Model download completed!")
        except Exception as e:
            print(f"❌ Failed to download model: {e}")
            raise


def test_embedding_interface(model_path, is_local=False):
    """Test embedding model functionality using the interface."""
    
    print("=" * 70)
    print("TESTING EMBEDDING MODEL VIA INTERFACE")
    print("=" * 70)
    
    # Handle model path - download if it's a HF model ID
    if not is_local and "/" in model_path:
        # It's a HuggingFace model ID
        local_dir = f"./modelfiles/{model_path.replace('/', '_')}"
        download_model_if_needed(model_path, local_dir)
        model_path = local_dir
    
    # Create embedder using factory function (will auto-detect model type)
    print(f"\n🔍 Creating embedder for: {model_path}")
    embedder = create_embedder(model_path=model_path)
    print(f"✅ Created embedder type: {type(embedder).__name__}")
    
    # Load the model
    print("\n📚 Loading embedding model...")
    success = embedder.load_model(model_path)
    
    if not success:
        print("❌ Failed to load model!")
        return
    
    print("✅ Model loaded successfully!")
    print(f"📏 Embedding dimension: {embedder.embedding_dim()}")
    
    # Test texts
    test_texts = [
        "Hello, how are you?",
        "What is machine learning?",
        "The weather is nice today.",
        "Python is a programming language.",
        "Artificial intelligence is changing the world."
    ]
    
    # Configure embedding with different settings
    configs = [
        EmbeddingConfig(batch_size=2, normalize=True, normalize_method="l2"),
        EmbeddingConfig(batch_size=3, normalize=False),
    ]
    
    for config_idx, config in enumerate(configs):
        print(f"\n{'='*50}")
        print(f"TEST {config_idx + 1}: Config - Batch: {config.batch_size}, "
              f"Normalize: {config.normalize}, Method: {config.normalize_method}")
        print('='*50)
        
        # Generate embeddings
        embeddings = embedder.embed(test_texts, config)
        
        # Display results
        print(f"\n📊 Generated {len(embeddings)} embeddings")
        
        for i, (text, embedding) in enumerate(zip(test_texts[:3], embeddings[:3])):
            print(f"\n  Text {i+1}: '{text}'")
            print(f"    Dimension: {len(embedding)}")
            print(f"    First 5 values: {[f'{v:.4f}' for v in embedding[:5]]}")
            
            # Calculate magnitude
            magnitude = np.linalg.norm(embedding)
            print(f"    Magnitude: {magnitude:.6f}")
    
    # Compute similarity matrix for normalized embeddings
    print("\n" + "="*50)
    print("SIMILARITY MATRIX (L2 Normalized)")
    print("="*50)
    
    config = EmbeddingConfig(batch_size=len(test_texts), normalize=True, normalize_method="l2")
    embeddings = embedder.embed(test_texts, config)
    
    # Convert to numpy for easier computation
    embeddings_np = np.array(embeddings)
    similarity_matrix = np.dot(embeddings_np, embeddings_np.T)
    
    print("\nTexts:")
    for i, text in enumerate(test_texts):
        print(f"  [{i}] {text[:30]}...")
    
    print("\nSimilarity Matrix:")
    print("     ", end="")
    for i in range(len(test_texts)):
        print(f"  [{i}] ", end="")
    print()
    
    for i in range(len(test_texts)):
        print(f"  [{i}]", end="")
        for j in range(len(test_texts)):
            print(f" {similarity_matrix[i, j]:5.2f}", end="")
        print()
    
    # Find most similar pairs
    print("\n🔍 Most Similar Pairs (excluding self-similarity):")
    similarities = []
    for i in range(len(test_texts)):
        for j in range(i+1, len(test_texts)):
            similarities.append((similarity_matrix[i, j], i, j))
    
    similarities.sort(reverse=True)
    for sim, i, j in similarities[:3]:
        print(f"  • Texts [{i}] and [{j}]: {sim:.4f}")
    
    # Cleanup
    embedder.close()
    print("\n✅ Interface test completed successfully!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test embedding models via interface")
    parser.add_argument(
        "--model_path", 
        type=str, 
        default="nexaml/jina-v2-fp16-mlx",
        help="Model path (local) or HuggingFace model ID"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Indicate if model_path is a local directory"
    )
    args = parser.parse_args()
    
    test_embedding_interface(args.model_path, args.local)
