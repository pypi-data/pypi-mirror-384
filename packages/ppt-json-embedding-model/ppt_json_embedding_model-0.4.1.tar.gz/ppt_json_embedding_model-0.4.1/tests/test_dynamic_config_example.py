"""
Example test file showing how dynamic configuration makes tests more robust.

This demonstrates how tests automatically adapt to different model configurations
without needing hardcoded values.
"""

import pytest
import numpy as np
import torch
from embedding_model.model.charcnn import CharCNNEncoder
from embedding_model.api import JSONEmbeddingModel


class TestDynamicConfiguration:
    """Test suite showing dynamic configuration benefits."""
    
    def test_model_adapts_to_any_config(self, sample_vocab, sample_config):
        """Test that model creation adapts to any configuration."""
        # Create model with current config
        model = CharCNNEncoder(
            vocab_size=len(sample_vocab.stoi),
            embedding_dim=sample_config.char_embed_dim,
            conv_channels=sample_config.conv_channels,
            kernel_sizes=sample_config.kernel_sizes,
            projection_dim=sample_config.projection_dim,
            layer_norm=sample_config.layer_norm
        )
        
        # Test that model dimensions match config
        batch_size = 2
        seq_len = 10
        ids = torch.randint(0, len(sample_vocab.stoi), (batch_size, seq_len))
        mask = torch.ones(batch_size, seq_len, dtype=torch.bool)
        
        output = model(ids, mask)
        
        # These assertions will work regardless of config values
        assert output.shape == (batch_size, sample_config.projection_dim)
        assert len(model.convs) == len(sample_config.kernel_sizes)
        assert model.convs[0].out_channels == sample_config.conv_channels
    
    def test_embedding_dimensions_match_config(self, mock_model_checkpoint, sample_config):
        """Test that embeddings always match the configured projection dimension."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        # Single embedding
        embedding = model.embed_text("test")
        assert embedding.shape == (sample_config.projection_dim,)
        
        # Batch embeddings
        embeddings = model.embed_texts(["test1", "test2", "test3"])
        assert embeddings.shape == (3, sample_config.projection_dim)
    
    def test_config_dependent_parameters(self, sample_config):
        """Test that we can validate config-dependent parameters."""
        # These tests work regardless of the actual config values
        assert sample_config.projection_dim > 0
        assert sample_config.char_embed_dim > 0
        assert sample_config.conv_channels > 0
        assert len(sample_config.kernel_sizes) > 0
        assert all(k > 0 for k in sample_config.kernel_sizes)
        assert sample_config.max_chars > 0
        
        # Test that kernel sizes are reasonable
        assert max(sample_config.kernel_sizes) < sample_config.max_chars
    
    def test_vocabulary_size_independence(self, sample_vocab, sample_config):
        """Test that model works with any vocabulary size."""
        # Create models with different vocab sizes
        small_vocab_size = 50
        large_vocab_size = 200
        
        small_model = CharCNNEncoder(
            vocab_size=small_vocab_size,
            embedding_dim=sample_config.char_embed_dim,
            conv_channels=sample_config.conv_channels,
            kernel_sizes=sample_config.kernel_sizes,
            projection_dim=sample_config.projection_dim,
            layer_norm=sample_config.layer_norm
        )
        
        large_model = CharCNNEncoder(
            vocab_size=large_vocab_size,
            embedding_dim=sample_config.char_embed_dim,
            conv_channels=sample_config.conv_channels,
            kernel_sizes=sample_config.kernel_sizes,
            projection_dim=sample_config.projection_dim,
            layer_norm=sample_config.layer_norm
        )
        
        # Both should produce same output dimensions
        batch_size = 2
        seq_len = 10
        
        small_ids = torch.randint(0, small_vocab_size, (batch_size, seq_len))
        large_ids = torch.randint(0, large_vocab_size, (batch_size, seq_len))
        mask = torch.ones(batch_size, seq_len, dtype=torch.bool)
        
        small_output = small_model(small_ids, mask)
        large_output = large_model(large_ids, mask)
        
        # Both outputs should have same shape (config-determined)
        assert small_output.shape == large_output.shape
        assert small_output.shape == (batch_size, sample_config.projection_dim)
    
    def test_helper_fixtures(self, dynamic_embedding_shape, dynamic_batch_embedding_shape):
        """Test that helper fixtures work correctly."""
        # Create some dummy embeddings
        single_embedding = np.random.randn(*dynamic_embedding_shape)
        batch_embeddings = np.random.randn(5, dynamic_embedding_shape[0])
        
        # These should pass regardless of actual dimensions
        assert single_embedding.shape == dynamic_embedding_shape
        assert dynamic_batch_embedding_shape(batch_embeddings, 5)


# Example of how you might test with different configurations
@pytest.mark.parametrize("projection_dim,conv_channels", [
    (128, 128),
    (256, 256), 
    (512, 512)
])
def test_with_different_dimensions(projection_dim, conv_channels, sample_vocab):
    """Example of testing with different configuration values."""
    # This would require creating custom configs, but shows the flexibility
    model = CharCNNEncoder(
        vocab_size=len(sample_vocab.stoi),
        embedding_dim=32,  # Keep small for test speed
        conv_channels=conv_channels,
        kernel_sizes=[3, 5],  # Keep simple for test speed
        projection_dim=projection_dim,
        layer_norm=True
    )
    
    batch_size = 2
    seq_len = 10
    ids = torch.randint(0, len(sample_vocab.stoi), (batch_size, seq_len))
    mask = torch.ones(batch_size, seq_len, dtype=torch.bool)
    
    output = model(ids, mask)
    
    # Test adapts to the parameterized dimensions
    assert output.shape == (batch_size, projection_dim)
    assert model.convs[0].out_channels == conv_channels
