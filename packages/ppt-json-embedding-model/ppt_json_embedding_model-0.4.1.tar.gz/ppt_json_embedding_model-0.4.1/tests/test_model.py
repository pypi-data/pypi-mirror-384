"""
Tests for the CharCNN model.
"""

import pytest
import torch
from embedding_model.model.charcnn import CharCNNEncoder


class TestCharCNNEncoder:
    """Test the CharCNNEncoder model."""
    
    def test_model_initialization(self):
        """Test model initialization with various parameters."""
        model = CharCNNEncoder(
            vocab_size=100,
            embedding_dim=32,
            conv_channels=64,
            kernel_sizes=[3, 5, 7],
            projection_dim=128,
            layer_norm=True
        )
        
        assert model.char_embed.num_embeddings == 100
        assert model.char_embed.embedding_dim == 32
        assert len(model.convs) == 3  # Three kernel sizes
        assert model.proj.out_features == 128
        assert model.ln is not None  # Layer norm enabled
    
    def test_model_without_layer_norm(self):
        """Test model initialization without layer normalization."""
        model = CharCNNEncoder(
            vocab_size=50,
            embedding_dim=16,
            conv_channels=32,
            kernel_sizes=[3],
            projection_dim=64,
            layer_norm=False
        )
        
        assert isinstance(model.ln, torch.nn.Identity)
    
    def test_forward_pass(self, sample_model, sample_vocab, sample_config):
        """Test forward pass through the model."""
        batch_size = 2
        seq_len = 10
        
        # Create sample input
        ids = torch.randint(0, len(sample_vocab.stoi), (batch_size, seq_len))
        mask = torch.ones(batch_size, seq_len, dtype=torch.bool)
        
        # Forward pass
        output = sample_model(ids, mask)
        
        assert output.shape == (batch_size, sample_config.projection_dim)
        assert output.dtype == torch.float32
    
    def test_forward_with_padding(self, sample_model, sample_vocab, sample_config):
        """Test forward pass with padded sequences."""
        batch_size = 2
        seq_len = 10
        
        # Create input with some padding
        ids = torch.randint(0, len(sample_vocab.stoi), (batch_size, seq_len))
        mask = torch.ones(batch_size, seq_len, dtype=torch.bool)
        mask[0, 7:] = False  # Pad the first sequence after position 7
        mask[1, 5:] = False  # Pad the second sequence after position 5
        
        output = sample_model(ids, mask)
        
        assert output.shape == (batch_size, sample_config.projection_dim)
        assert not torch.isnan(output).any()
        assert not torch.isinf(output).any()
    
    def test_model_parameters_count(self, sample_model):
        """Test that model has reasonable number of parameters."""
        total_params = sum(p.numel() for p in sample_model.parameters())
        
        # Should have parameters but not too many for test model
        assert total_params > 1000
        assert total_params < 1000000  # Reasonable upper bound for test model
    
    def test_model_gradients(self, sample_model, sample_vocab):
        """Test that gradients flow properly."""
        batch_size = 2
        seq_len = 10
        
        ids = torch.randint(0, len(sample_vocab.stoi), (batch_size, seq_len))
        mask = torch.ones(batch_size, seq_len, dtype=torch.bool)
        
        # Forward pass
        output = sample_model(ids, mask)
        
        # Backward pass
        loss = output.sum()
        loss.backward()
        
        # Check that gradients exist
        for name, param in sample_model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for {name}"
                assert not torch.isnan(param.grad).any(), f"NaN gradient for {name}"
    
    def test_model_eval_mode(self, sample_model, sample_vocab):
        """Test model in evaluation mode."""
        sample_model.eval()
        
        batch_size = 2
        seq_len = 10
        ids = torch.randint(0, len(sample_vocab.stoi), (batch_size, seq_len))
        mask = torch.ones(batch_size, seq_len, dtype=torch.bool)
        
        with torch.no_grad():
            output1 = sample_model(ids, mask)
            output2 = sample_model(ids, mask)
        
        # Outputs should be identical in eval mode
        assert torch.allclose(output1, output2)
    
    def test_different_sequence_lengths(self, sample_model, sample_vocab, sample_config):
        """Test model with different sequence lengths."""
        batch_size = 3
        
        # Different lengths
        lengths = [5, 10, 8]
        max_len = max(lengths)
        
        ids = torch.zeros(batch_size, max_len, dtype=torch.long)
        mask = torch.zeros(batch_size, max_len, dtype=torch.bool)
        
        for i, length in enumerate(lengths):
            ids[i, :length] = torch.randint(1, len(sample_vocab.stoi), (length,))
            mask[i, :length] = True
        
        output = sample_model(ids, mask)
        
        assert output.shape == (batch_size, sample_config.projection_dim)
        assert not torch.isnan(output).any()
    
    def test_empty_sequence_handling(self, sample_model, sample_config):
        """Test model with empty sequences (all padding)."""
        batch_size = 2
        seq_len = 10
        
        ids = torch.zeros(batch_size, seq_len, dtype=torch.long)  # All padding
        mask = torch.zeros(batch_size, seq_len, dtype=torch.bool)  # All False
        
        output = sample_model(ids, mask)
        
        assert output.shape == (batch_size, sample_config.projection_dim)
        # Output should be valid (not NaN/Inf) even for empty sequences
        assert torch.isfinite(output).all()
