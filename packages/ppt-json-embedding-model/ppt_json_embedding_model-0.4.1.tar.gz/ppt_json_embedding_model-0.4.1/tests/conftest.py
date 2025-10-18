"""
Pytest configuration and fixtures for embedding model tests.
"""

import pytest
import tempfile
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import torch
import numpy as np

# Add src to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from embedding_model.tokenizer import CharVocab
from embedding_model.model.charcnn import CharCNNEncoder
from embedding_model.config import load_config
from embedding_model.conversation import RoleTokenMap


@pytest.fixture
def sample_documents() -> List[Dict[str, Any]]:
    """Sample JSON documents for testing."""
    return [
        {
            "id": "1",
            "title": "MacBook Pro 16-inch",
            "category": "laptops",
            "brand": "Apple",
            "price": 2399,
            "description": "Powerful laptop with M2 Pro chip, great for development and creative work"
        },
        {
            "id": "2", 
            "title": "Dell XPS 13",
            "category": "laptops",
            "brand": "Dell",
            "price": 1299,
            "description": "Compact ultrabook with excellent build quality and long battery life"
        },
        {
            "id": "3",
            "title": "iPad Pro 12.9",
            "category": "tablets",
            "brand": "Apple", 
            "price": 1099,
            "description": "Professional tablet with Apple Pencil support, perfect for digital art"
        }
    ]


@pytest.fixture
def sample_vocab() -> CharVocab:
    """Sample character vocabulary for testing."""
    charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./,:;!?@#%&*()[]{}<>\"'`~+=|\\ \t"
    return CharVocab.build(charset, "?")


@pytest.fixture
def sample_model(sample_vocab, sample_config) -> CharCNNEncoder:
    """Sample model for testing - matches real config dimensions."""
    return CharCNNEncoder(
        vocab_size=len(sample_vocab.stoi),
        embedding_dim=sample_config.char_embed_dim,
        conv_channels=sample_config.conv_channels,
        kernel_sizes=sample_config.kernel_sizes,
        projection_dim=sample_config.projection_dim,
        layer_norm=sample_config.layer_norm
    )


@pytest.fixture
def temp_jsonl_file(sample_documents) -> Path:
    """Temporary JSONL file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for doc in sample_documents:
            f.write(json.dumps(doc) + '\n')
        return Path(f.name)


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    config_path = project_root / "src" / "embedding_model" / "config" / "default.yaml"
    return load_config(config_path)


@pytest.fixture
def sample_role_tokens(sample_config) -> RoleTokenMap:
    """Sample role tokens for testing conversation functionality."""
    return RoleTokenMap(
        sample_config.role_tokens.system,
        sample_config.role_tokens.user,
        sample_config.role_tokens.assistant
    )


@pytest.fixture
def mock_model_checkpoint(sample_vocab, sample_model, sample_config, tmp_path) -> Path:
    """Mock model checkpoint for testing."""
    checkpoint_path = tmp_path / "test_model.pt"
    
    # Create a checkpoint compatible with the actual API
    checkpoint = {
        'model': sample_model.state_dict(),
        'vocab': sample_vocab.itos,  # Save as list for reconstruction
        'config': sample_config.to_dict() if hasattr(sample_config, 'to_dict') else {
            'char_embed_dim': 32,
            'conv_channels': 64,
            'kernel_sizes': [3, 5],
            'projection_dim': 128,
            'layer_norm': True,
            'max_chars': 512
        }
    }
    
    torch.save(checkpoint, checkpoint_path)
    return checkpoint_path


@pytest.fixture
def sample_embeddings(sample_documents, sample_config) -> np.ndarray:
    """Sample embeddings for testing search functionality."""
    # Create deterministic embeddings for consistent testing
    np.random.seed(42)
    return np.random.randn(len(sample_documents), sample_config.projection_dim).astype(np.float32)


@pytest.fixture
def dynamic_embedding_shape(sample_config) -> tuple:
    """Helper fixture to get expected embedding shape dynamically."""
    return (sample_config.projection_dim,)


@pytest.fixture
def dynamic_batch_embedding_shape(sample_config):
    """Helper fixture to create dynamic batch embedding shape checker."""
    def check_shape(embeddings: np.ndarray, batch_size: int):
        expected_shape = (batch_size, sample_config.projection_dim)
        assert embeddings.shape == expected_shape, f"Expected {expected_shape}, got {embeddings.shape}"
        return True
    return check_shape


@pytest.fixture
def integration_model(mock_model_checkpoint):
    """Create a JSONEmbeddingModel instance for integration testing with CPU fallback."""
    from embedding_model import JSONEmbeddingModel
    
    # Force CPU to avoid CUDA/Windows issues in CI/testing environments
    return JSONEmbeddingModel(str(mock_model_checkpoint), device='cpu')
