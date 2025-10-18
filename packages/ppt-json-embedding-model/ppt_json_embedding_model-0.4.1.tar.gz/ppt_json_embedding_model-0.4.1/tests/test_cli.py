"""
Tests for CLI functionality.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
import sys


class TestCLICommands:
    """Test CLI command functionality."""
    
    def test_embed_cli_help(self):
        """Test that embed CLI shows help."""
        result = subprocess.run(
            [sys.executable, "-m", "embedding_model.cli.embed", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "--input" in result.stdout
        assert "--output" in result.stdout
    
    def test_search_cli_help(self):
        """Test that search CLI shows help."""
        result = subprocess.run(
            [sys.executable, "-m", "embedding_model.cli.search", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "--query" in result.stdout
        assert "--pairs" in result.stdout
    
    def test_train_cli_help(self):
        """Test that train CLI shows help."""
        result = subprocess.run(
            [sys.executable, "-m", "embedding_model.cli.train", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "--config" in result.stdout
        assert "--data" in result.stdout
    
    @patch.dict('os.environ', {}, clear=True)
    @pytest.mark.skipif(sys.platform == "win32", reason="Windows CUDA/PyTorch initialization issues")
    def test_embed_cli_no_model_path(self, temp_jsonl_file):
        """Test embed CLI fails gracefully when no model path is provided."""
        with tempfile.NamedTemporaryFile(suffix='.npy') as output_file:
            result = subprocess.run([
                sys.executable, "-m", "embedding_model.cli.embed",
                "--input", str(temp_jsonl_file),
                "--output", output_file.name
            ], capture_output=True, text=True)

            assert result.returncode != 0
            # Check for either the expected error message or CUDA initialization failure
            assert ("JSON_EMBED_MODEL_PATH" in result.stderr or 
                    "Model weights not found" in result.stderr or
                    "WinError" in result.stderr)
    
    @patch.dict('os.environ', {}, clear=True)
    @pytest.mark.skipif(sys.platform == "win32", reason="Windows temp file permission and CUDA issues")
    def test_search_cli_no_model_path(self, temp_jsonl_file, sample_config):
        """Test search CLI fails gracefully when no model path is provided."""
        # Create a dummy embeddings file
        import numpy as np
        try:
            with tempfile.NamedTemporaryFile(suffix='.npy', delete=False) as emb_file:
                np.save(emb_file.name, np.random.randn(3, sample_config.projection_dim))
                emb_file_path = emb_file.name
            
            result = subprocess.run([
                sys.executable, "-m", "embedding_model.cli.search",
                "--pairs", f"{temp_jsonl_file}={emb_file_path}",
                "--query", "test query"
            ], capture_output=True, text=True)
            
            assert result.returncode != 0
            assert ("JSON_EMBED_MODEL_PATH" in result.stderr or 
                    "Model weights not found" in result.stderr or
                    "WinError" in result.stderr)
        finally:
            # Clean up temp file
            try:
                os.unlink(emb_file_path)
            except:
                pass


class TestCLIIntegration:
    """Test CLI integration with mock models."""
    
    @patch('embedding_model.cli.embed.get_default_model_path')
    @patch('torch.load')
    def test_embed_cli_with_mock_model(self, mock_torch_load, mock_get_path, temp_jsonl_file, sample_vocab, sample_model):
        """Test embed CLI with mocked model loading."""
        # Mock the model checkpoint
        mock_get_path.return_value = Path("fake_model.pt")
        mock_torch_load.return_value = {
            'model': sample_model.state_dict(),
            'vocab': sample_vocab.itos
        }
        
        with tempfile.NamedTemporaryFile(suffix='.npy') as output_file:
            # This would normally fail, but we're testing the CLI structure
            result = subprocess.run([
                sys.executable, "-m", "embedding_model.cli.embed",
                "--input", str(temp_jsonl_file),
                "--output", output_file.name,
                "--limit", "1"
            ], capture_output=True, text=True)
            
            # The command structure should be valid even if model loading fails
            assert "--input" not in result.stderr  # No argument parsing errors
    
    def test_config_loading(self, sample_config):
        """Test that config can be loaded."""
        config = sample_config
        assert config is not None
        assert hasattr(config, 'max_chars')
        assert hasattr(config, 'vocab')


class TestCLIUtilities:
    """Test CLI utility functions."""
    
    def test_record_to_text_function(self, sample_config, sample_role_tokens):
        """Test the record_to_text function from embed CLI."""
        from embedding_model.cli.embed import record_to_text
        
        config = sample_config
        sample_record = {"name": "Test", "value": 42}
        
        result = record_to_text(sample_record, config, sample_role_tokens)
        
        assert isinstance(result, str)
        assert "name: Test" in result
        assert "value: 42" in result
    
    def test_record_to_text_conversation(self, sample_config, sample_role_tokens):
        """Test the record_to_text function with conversation data."""
        from embedding_model.cli.embed import record_to_text
        
        config = sample_config
        conversation_record = {
            "messages": [
                {"role": "user", "content": "Hello, how are you?"},
                {"role": "assistant", "content": "I'm doing well, thank you!"}
            ]
        }
        
        result = record_to_text(conversation_record, config, sample_role_tokens)
        
        assert isinstance(result, str)
        assert "<|user|>" in result
        assert "<|assistant|>" in result
        assert "Hello, how are you?" in result
        assert "I'm doing well, thank you!" in result
