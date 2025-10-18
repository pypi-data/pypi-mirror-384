"""
Proper integration tests for the JSON Embedding Model API.

These tests use real model functionality with proper pytest fixtures
and include CPU fallback for environments with CUDA issues.
"""

import pytest
import numpy as np
import sys
import os
from pathlib import Path

# Test documents
TEST_DOCS = [
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
def integration_model(mock_model_checkpoint):
    """Create a JSONEmbeddingModel instance for integration testing with CPU fallback."""
    from embedding_model import JSONEmbeddingModel
    
    # Force CPU to avoid CUDA/Windows issues in CI/testing environments
    return JSONEmbeddingModel(str(mock_model_checkpoint), device='cpu')


class TestAPIIntegration:
    """Integration tests for the JSON Embedding Model API."""
    
    def test_imports(self):
        """Test that we can import the new API components."""
        from embedding_model import JSONEmbeddingModel, search_documents, embed_documents
        
        # Check that classes/functions exist and are callable
        assert JSONEmbeddingModel is not None
        assert callable(JSONEmbeddingModel)
        assert callable(search_documents)
        assert callable(embed_documents)
    
    def test_model_initialization(self, mock_model_checkpoint, sample_config):
        """Test model initialization with CPU fallback."""
        from embedding_model import JSONEmbeddingModel
        
        # Test with explicit CPU device
        model = JSONEmbeddingModel(str(mock_model_checkpoint), device='cpu')
        
        assert model is not None
        assert model.device == 'cpu'
        assert model.model is not None
        assert model.vocab is not None
        assert model.collate_fn is not None
        
        # Test that model has expected dimensions
        assert hasattr(model.model, 'proj')
        assert model.model.proj.out_features == sample_config.projection_dim
    
    def test_embedding_single_document(self, integration_model, sample_config):
        """Test embedding a single JSON document."""
        doc = TEST_DOCS[0]
        
        embedding = integration_model.embed_json_object(doc)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (sample_config.projection_dim,)
        assert embedding.dtype == np.float32
        assert not np.all(embedding == 0)  # Should not be all zeros
    
    def test_embedding_multiple_documents(self, integration_model, sample_config):
        """Test embedding multiple JSON documents."""
        embeddings = integration_model.embed_documents(TEST_DOCS)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (len(TEST_DOCS), sample_config.projection_dim)
        assert embeddings.dtype == np.float32
        assert not np.all(embeddings == 0)  # Should not be all zeros
        
        # Each document should have different embeddings
        for i in range(len(TEST_DOCS)):
            for j in range(i + 1, len(TEST_DOCS)):
                assert not np.array_equal(embeddings[i], embeddings[j])
    
    def test_search_functionality(self, integration_model):
        """Test search functionality with precomputed embeddings."""
        # Embed documents first
        embeddings = integration_model.embed_documents(TEST_DOCS)
        
        # Test search
        results = integration_model.search(
            query="laptop computer",
            documents=TEST_DOCS,
            embeddings=embeddings,
            top_k=2
        )
        
        assert isinstance(results, list)
        assert len(results) <= 2  # Should respect top_k
        assert len(results) > 0   # Should find some results
        
        # Check result format
        for similarity, idx, doc in results:
            assert isinstance(similarity, float)
            assert isinstance(idx, int)
            assert isinstance(doc, dict)
            assert 0 <= idx < len(TEST_DOCS)
            assert doc == TEST_DOCS[idx]
            assert 0 <= similarity <= 1  # Cosine similarity should be normalized
    
    def test_search_with_filters(self, integration_model):
        """Test search functionality with filters."""
        results = integration_model.search(
            query="Apple device",
            documents=TEST_DOCS,
            top_k=5,
            filters={"brand": "Apple"}
        )
        
        assert isinstance(results, list)
        assert len(results) > 0  # Should find Apple devices
        
        # All results should match filter
        for similarity, idx, doc in results:
            assert doc["brand"] == "Apple"
    
    def test_search_without_precomputed_embeddings(self, integration_model):
        """Test search functionality without precomputed embeddings."""
        results = integration_model.search(
            query="professional tablet",
            documents=TEST_DOCS,
            top_k=3
        )
        
        assert isinstance(results, list)
        assert len(results) <= 3
        assert len(results) > 0
        
        # Should find the iPad Pro as most relevant
        best_match = results[0]
        similarity, idx, doc = best_match
        assert "iPad" in doc["title"] or "tablet" in doc["description"].lower()
    
    def test_empty_documents_handling(self, integration_model):
        """Test handling of empty document lists."""
        results = integration_model.search(
            query="test query",
            documents=[],
            top_k=5
        )
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_device_fallback(self, mock_model_checkpoint):
        """Test that device fallback works correctly."""
        from embedding_model import JSONEmbeddingModel
        
        # Test auto device selection (should work on any system)
        model_auto = JSONEmbeddingModel(str(mock_model_checkpoint), device='auto')
        assert model_auto.device in ['cpu', 'cuda']
        
        # Test explicit CPU (should always work)
        model_cpu = JSONEmbeddingModel(str(mock_model_checkpoint), device='cpu')
        assert model_cpu.device == 'cpu'
        
        # Both should produce same results
        doc = TEST_DOCS[0]
        embedding_auto = model_auto.embed_json_object(doc)
        embedding_cpu = model_cpu.embed_json_object(doc)
        
        # Results should be very similar (allowing for minor floating point differences)
        assert embedding_auto.shape == embedding_cpu.shape
        assert np.allclose(embedding_auto, embedding_cpu, rtol=1e-5)


class TestConvenienceFunctions:
    """Test the high-level convenience functions."""
    
    def test_embed_documents_function(self, mock_model_checkpoint, sample_config):
        """Test the embed_documents convenience function with CPU fallback."""
        from embedding_model import embed_documents
        
        embeddings = embed_documents(
            documents=TEST_DOCS,
            model_path=str(mock_model_checkpoint),
            device='cpu',  # Force CPU for testing
            batch_size=2
        )
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (len(TEST_DOCS), sample_config.projection_dim)
        assert embeddings.dtype == np.float32
    
    def test_search_documents_function(self, mock_model_checkpoint):
        """Test the search_documents convenience function with CPU fallback."""
        from embedding_model import search_documents
        
        results = search_documents(
            query="laptop computer",
            documents=TEST_DOCS,
            model_path=str(mock_model_checkpoint),
            device='cpu',  # Force CPU for testing
            top_k=2
        )
        
        assert isinstance(results, list)
        assert len(results) <= 2
        assert len(results) > 0
        
        for similarity, idx, doc in results:
            assert isinstance(similarity, float)
            assert isinstance(idx, int)
            assert isinstance(doc, dict)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_nonexistent_model_path(self):
        """Test handling of nonexistent model path."""
        from embedding_model import JSONEmbeddingModel
        
        with pytest.raises((FileNotFoundError, RuntimeError)):
            JSONEmbeddingModel("nonexistent_model.pt", device='cpu')
    
    def test_malformed_documents(self, integration_model):
        """Test handling of malformed documents."""
        malformed_docs = [
            {"missing_required_fields": True},
            {},  # Empty document
            {"single_field": "value"}
        ]
        
        # Should not crash, even with malformed documents
        embeddings = integration_model.embed_documents(malformed_docs)
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == len(malformed_docs)
    
    def test_search_with_no_matching_filters(self, integration_model):
        """Test search with filters that match no documents."""
        results = integration_model.search(
            query="any query",
            documents=TEST_DOCS,
            top_k=5,
            filters={"nonexistent_field": "impossible_value"}
        )
        
        assert isinstance(results, list)
        assert len(results) == 0


# Mark these as integration tests
pytestmark = pytest.mark.integration
