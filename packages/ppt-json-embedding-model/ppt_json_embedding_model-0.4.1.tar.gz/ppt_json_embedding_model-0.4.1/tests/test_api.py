"""
Tests for the high-level Python API.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import os
from pathlib import Path

from embedding_model import JSONEmbeddingModel, search_documents, embed_documents
from embedding_model.api import JSONEmbeddingModel


class TestJSONEmbeddingModel:
    """Test the JSONEmbeddingModel class."""
    
    def test_init_with_mock_checkpoint(self, mock_model_checkpoint):
        """Test model initialization with a mock checkpoint."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        assert model.model is not None
        assert model.vocab is not None
        assert model.collate_fn is not None
        assert len(model.vocab.stoi) > 0
    
    def test_embed_text(self, mock_model_checkpoint, sample_config):
        """Test embedding a single text string."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        text = "This is a test string"
        embedding = model.embed_text(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (sample_config.projection_dim,)
        assert embedding.dtype == np.float32
    
    def test_embed_texts_batch(self, mock_model_checkpoint, sample_config):
        """Test embedding multiple text strings."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        texts = ["First text", "Second text", "Third text"]
        embeddings = model.embed_texts(texts, batch_size=2)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (3, sample_config.projection_dim)
        assert embeddings.dtype == np.float32
    
    def test_embed_json_object(self, mock_model_checkpoint, sample_documents, sample_config):
        """Test embedding a JSON object."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        doc = sample_documents[0]
        embedding = model.embed_json_object(doc)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (sample_config.projection_dim,)
        assert embedding.dtype == np.float32
    
    def test_embed_documents(self, mock_model_checkpoint, sample_documents, sample_config):
        """Test embedding multiple JSON documents."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        embeddings = model.embed_documents(sample_documents)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (len(sample_documents), sample_config.projection_dim)
        assert embeddings.dtype == np.float32
    
    def test_search_functionality(self, mock_model_checkpoint, sample_documents):
        """Test search functionality."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        # Pre-compute embeddings
        embeddings = model.embed_documents(sample_documents)
        
        # Search
        results = model.search(
            query="powerful laptop",
            documents=sample_documents,
            embeddings=embeddings,
            top_k=2
        )
        
        assert len(results) == 2
        for similarity, idx, doc in results:
            assert isinstance(similarity, float)
            assert isinstance(idx, int)
            assert isinstance(doc, dict)
            assert 0 <= idx < len(sample_documents)
    
    def test_search_with_filters(self, mock_model_checkpoint, sample_documents):
        """Test search with filters."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        embeddings = model.embed_documents(sample_documents)
        
        # Search only Apple products
        results = model.search(
            query="device",
            documents=sample_documents,
            embeddings=embeddings,
            top_k=5,
            filters={"brand": "Apple"}
        )
        
        # Should only return Apple products
        for similarity, idx, doc in results:
            assert doc["brand"] == "Apple"
    
    def test_search_without_precomputed_embeddings(self, mock_model_checkpoint, sample_documents):
        """Test search without pre-computed embeddings."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        results = model.search(
            query="laptop",
            documents=sample_documents,
            top_k=1
        )
        
        assert len(results) == 1
        similarity, idx, doc = results[0]
        assert isinstance(similarity, float)
    
    def test_matches_filters(self, mock_model_checkpoint):
        """Test the _matches_filters method."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        document = {"brand": "Apple", "category": "laptops", "price": 1000}
        
        # Test matching filters
        assert model._matches_filters(document, {"brand": "Apple"})
        assert model._matches_filters(document, {"brand": "Apple", "category": "laptops"})
        
        # Test non-matching filters
        assert not model._matches_filters(document, {"brand": "Dell"})
        assert not model._matches_filters(document, {"nonexistent": "value"})
    
    def test_device_selection(self, mock_model_checkpoint):
        """Test device selection logic."""
        # Test auto device selection
        model = JSONEmbeddingModel(str(mock_model_checkpoint), device="auto")
        assert model.device in ["cpu", "cuda"]
        
        # Test explicit CPU
        model = JSONEmbeddingModel(str(mock_model_checkpoint), device="cpu")
        assert model.device == "cpu"
    
    def test_vocabulary_from_checkpoint(self, mock_model_checkpoint):
        """Test that vocabulary is loaded from checkpoint."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        # The vocab should be loaded from the checkpoint, not built from config
        assert model.vocab is not None
        assert len(model.vocab.stoi) > 0
        assert len(model.vocab.itos) > 0


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_embed_documents_function(self, mock_model_checkpoint, sample_documents, sample_config):
        """Test the embed_documents convenience function."""
        embeddings = embed_documents(
            documents=sample_documents,
            model_path=str(mock_model_checkpoint),
            batch_size=2
        )
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (len(sample_documents), sample_config.projection_dim)
    
    def test_search_documents_function(self, mock_model_checkpoint, sample_documents):
        """Test the search_documents convenience function."""
        results = search_documents(
            query="laptop computer",
            documents=sample_documents,
            model_path=str(mock_model_checkpoint),
            top_k=2
        )
        
        assert len(results) == 2
        for similarity, idx, doc in results:
            assert isinstance(similarity, float)
            assert isinstance(idx, int)
            assert isinstance(doc, dict)


class TestErrorHandling:
    """Test error handling in the API."""
    
    def test_nonexistent_model_path(self):
        """Test error when model path doesn't exist."""
        with pytest.raises(FileNotFoundError):
            JSONEmbeddingModel("nonexistent/path.pt")
    
    def test_empty_documents_search(self, mock_model_checkpoint):
        """Test search with empty documents list."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        results = model.search(
            query="test",
            documents=[],
            top_k=5
        )
        
        assert results == []
    
    def test_no_matching_filters(self, mock_model_checkpoint, sample_documents):
        """Test search with filters that match no documents."""
        model = JSONEmbeddingModel(str(mock_model_checkpoint))
        
        embeddings = model.embed_documents(sample_documents)
        
        results = model.search(
            query="test",
            documents=sample_documents,
            embeddings=embeddings,
            filters={"nonexistent_field": "nonexistent_value"}
        )
        
        assert results == []
