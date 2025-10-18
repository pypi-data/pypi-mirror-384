"""
Tests for the character tokenizer.
"""

import pytest
from embedding_model.tokenizer import CharVocab, PAD_TOKEN


class TestCharVocab:
    """Test the CharVocab class."""
    
    def test_build_vocab(self):
        """Test building vocabulary from character set."""
        charset = "abc123"
        unk_token = "?"
        
        vocab = CharVocab.build(charset, unk_token)
        
        assert len(vocab.stoi) == len(charset) + 2  # +2 for pad and unk
        assert PAD_TOKEN in vocab.stoi
        assert unk_token in vocab.stoi
        assert vocab.stoi[PAD_TOKEN] == 0  # Pad should be first
        
        # Check all characters are included
        for char in charset:
            assert char in vocab.stoi
            assert char in vocab.itos
    
    def test_vocab_encoding(self, sample_vocab):
        """Test text encoding."""
        text = "hello"
        max_len = 10
        
        encoded = sample_vocab.encode(text, max_len)
        
        assert len(encoded) == max_len
        assert all(isinstance(x, int) for x in encoded)
        
        # Check padding
        assert encoded[len(text):] == [0] * (max_len - len(text))
    
    def test_vocab_encoding_truncation(self, sample_vocab):
        """Test text encoding with truncation."""
        long_text = "a" * 100
        max_len = 5
        
        encoded = sample_vocab.encode(long_text, max_len)
        
        assert len(encoded) == max_len
        assert all(x != 0 for x in encoded)  # No padding since truncated
    
    def test_unknown_character_handling(self, sample_vocab):
        """Test handling of unknown characters."""
        # Character not in vocabulary
        unknown_char = "🚀"
        text = f"hello{unknown_char}world"
        
        encoded = sample_vocab.encode(text, 20)
        
        # Should contain the unknown token ID
        unk_id = sample_vocab.stoi[sample_vocab.unk_token]
        assert unk_id in encoded
    
    def test_pad_id_property(self, sample_vocab):
        """Test the pad_id property."""
        assert sample_vocab.pad_id == 0
        assert sample_vocab.pad_id == sample_vocab.stoi[PAD_TOKEN]
    
    def test_empty_text_encoding(self, sample_vocab):
        """Test encoding empty text."""
        encoded = sample_vocab.encode("", 5)
        
        assert len(encoded) == 5
        assert all(x == 0 for x in encoded)  # All padding
    
    def test_vocab_consistency(self):
        """Test that stoi and itos are consistent."""
        charset = "abcdef123"
        vocab = CharVocab.build(charset, "?")
        
        # Check that stoi and itos are inverses
        for char, idx in vocab.stoi.items():
            assert vocab.itos[idx] == char
        
        for idx, char in enumerate(vocab.itos):
            assert vocab.stoi[char] == idx
