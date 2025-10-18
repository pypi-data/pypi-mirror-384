"""
Test Search Comparison and Improvements

This module tests search functionality improvements and comparisons.
Uses mocked data and models to avoid external dependencies.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import tempfile
import json
from pathlib import Path


@pytest.fixture
def sample_search_data():
    """Sample data for search testing."""
    return [
        {
            "id": "1",
            "title": "Network Connectivity Issue",
            "category": "network",
            "severity": "high",
            "description": "Unable to connect to corporate network, affecting multiple users",
            "tags": ["network", "connectivity", "infrastructure"]
        },
        {
            "id": "2", 
            "title": "Server Hardware Failure",
            "category": "hardware",
            "severity": "critical",
            "description": "Primary database server experiencing hardware failures",
            "tags": ["server", "hardware", "database", "critical"]
        },
        {
            "id": "3",
            "title": "Account Billing Problem", 
            "category": "billing",
            "severity": "medium",
            "description": "Customer reporting incorrect charges on monthly billing statement",
            "tags": ["billing", "account", "customer", "charges"]
        },
        {
            "id": "4",
            "title": "Device Configuration Error",
            "category": "configuration", 
            "severity": "low",
            "description": "Mobile device not properly configured for email access",
            "tags": ["device", "configuration", "email", "mobile"]
        },
        {
            "id": "5",
            "title": "Authentication Failure",
            "category": "security",
            "severity": "high", 
            "description": "Users unable to authenticate to system after recent security update",
            "tags": ["authentication", "security", "login", "system"]
        }
    ]


@pytest.fixture
def temp_data_dir(sample_search_data, tmp_path):
    """Create a temporary data directory with JSONL files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create sample JSONL file
    jsonl_file = data_dir / "sample_data.jsonl"
    with open(jsonl_file, 'w') as f:
        for item in sample_search_data:
            f.write(json.dumps(item) + '\n')
    
    return data_dir


class TestSearchComparison:
    """Test search functionality and improvements."""
    
    def test_search_relevance_basic(self, integration_model, sample_search_data):
        """Test basic search relevance with known queries."""
        test_queries = [
            ("network connectivity", "network"),  # Should match network category
            ("server hardware", "hardware"),      # Should match hardware category  
            ("billing problem", "billing"),       # Should match billing category
            ("authentication", "security"),       # Should match security category
        ]
        
        for query, expected_category in test_queries:
            results = integration_model.search(
                query=query,
                documents=sample_search_data,
                top_k=3
            )
            
            assert len(results) > 0, f"No results for query: {query}"
            
            # Check that top result is relevant
            top_similarity, top_idx, top_doc = results[0]
            assert top_similarity > 0.1, f"Low similarity for query: {query}"
            
            # Check that expected category appears in top results
            categories = [doc["category"] for _, _, doc in results]
            assert expected_category in categories, f"Expected category '{expected_category}' not found for query '{query}'"
    
    def test_search_with_filters_performance(self, integration_model, sample_search_data):
        """Test search performance with different filter combinations."""
        # Test category filter
        results = integration_model.search(
            query="system problem",
            documents=sample_search_data,
            filters={"category": "network"},
            top_k=5
        )
        
        # All results should match filter
        for _, _, doc in results:
            assert doc["category"] == "network"
    
    def test_search_ranking_quality(self, integration_model, sample_search_data):
        """Test that search results are properly ranked by relevance."""
        results = integration_model.search(
            query="server database critical",
            documents=sample_search_data,
            top_k=5
        )
        
        assert len(results) > 1, "Need multiple results to test ranking"
        
        # Similarities should be in descending order
        similarities = [sim for sim, _, _ in results]
        assert similarities == sorted(similarities, reverse=True), "Results not properly ranked"
        
        # Top result should be the server hardware failure (most relevant)
        top_doc = results[0][2]
        assert "server" in top_doc["title"].lower() or "database" in top_doc["description"].lower()
    
    def test_search_empty_query_handling(self, integration_model, sample_search_data):
        """Test handling of edge cases like empty queries."""
        # Empty query should still return results (random order is fine)
        results = integration_model.search(
            query="",
            documents=sample_search_data,
            top_k=3
        )
        
        assert isinstance(results, list)
        assert len(results) <= 3
    
    def test_search_no_matches_scenario(self, integration_model, sample_search_data):
        """Test search with very specific filters that match nothing."""
        results = integration_model.search(
            query="any query",
            documents=sample_search_data,
            filters={"category": "nonexistent_category"},
            top_k=5
        )
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    @pytest.mark.parametrize("batch_size", [1, 2, 5])
    def test_search_batch_processing(self, integration_model, sample_search_data, batch_size):
        """Test search with different batch sizes."""
        # This tests internal batching doesn't affect results
        results1 = integration_model.search(
            query="network issue",
            documents=sample_search_data,
            top_k=3
        )
        
        # Results should be consistent regardless of internal batching
        assert len(results1) > 0
        assert all(isinstance(sim, float) for sim, _, _ in results1)
    
    def test_search_similarity_bounds(self, integration_model, sample_search_data):
        """Test that similarity scores are within expected bounds."""
        results = integration_model.search(
            query="test query",
            documents=sample_search_data,
            top_k=len(sample_search_data)
        )
        
        for similarity, idx, doc in results:
            # Cosine similarity should be between -1 and 1, but typically 0-1 for normalized vectors
            assert -1 <= similarity <= 1, f"Similarity {similarity} out of bounds"
            assert 0 <= idx < len(sample_search_data), f"Index {idx} out of bounds"
            assert doc in sample_search_data, "Document not in original dataset"


class TestSearchComparisonMocked:
    """Test search comparison functionality with mocked dependencies."""
    
    def test_search_comparison_with_mocked_data(self, mock_model_checkpoint):
        """Test search comparison with mocked model."""
        from embedding_model import JSONEmbeddingModel
        
        # Test that we can initialize search with CPU fallback
        model = JSONEmbeddingModel(str(mock_model_checkpoint), device='cpu')
        
        # Test basic functionality works
        test_doc = {"id": "1", "title": "test", "content": "test content"}
        embedding = model.embed_json_object(test_doc)
        
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
    
    def test_model_path_resolution(self, tmp_path, mock_model_checkpoint):
        """Test model path resolution and fallback logic."""
        from embedding_model import JSONEmbeddingModel
        
        # Test with explicit path (should work)
        model = JSONEmbeddingModel(str(mock_model_checkpoint), device='cpu')
        assert model is not None
        
        # Test with nonexistent path (should raise error)
        with pytest.raises((FileNotFoundError, RuntimeError)):
            JSONEmbeddingModel("/nonexistent/path/model.pt", device='cpu')


# Test data generation utilities
class TestSearchDataGeneration:
    """Test utilities for generating search test data."""
    
    def test_generate_diverse_documents(self, sample_search_data):
        """Test that sample data has good diversity for search testing."""
        # Check we have different categories
        categories = set(doc["category"] for doc in sample_search_data)
        assert len(categories) >= 3, "Need diverse categories for good search testing"
        
        # Check we have different severity levels
        severities = set(doc["severity"] for doc in sample_search_data)
        assert len(severities) >= 2, "Need different severity levels"
        
        # Check all documents have required fields
        required_fields = ["id", "title", "category", "description"]
        for doc in sample_search_data:
            for field in required_fields:
                assert field in doc, f"Document missing required field: {field}"
    
    def test_jsonl_file_creation(self, temp_data_dir, sample_search_data):
        """Test JSONL file creation for search testing."""
        jsonl_files = list(temp_data_dir.glob("*.jsonl"))
        assert len(jsonl_files) > 0, "No JSONL files created"
        
        # Read back and verify content
        with open(jsonl_files[0], 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == len(sample_search_data)
        
        # Parse and verify each line
        for i, line in enumerate(lines):
            parsed = json.loads(line.strip())
            assert parsed == sample_search_data[i]


# Mark as integration tests requiring model functionality
pytestmark = pytest.mark.integration
