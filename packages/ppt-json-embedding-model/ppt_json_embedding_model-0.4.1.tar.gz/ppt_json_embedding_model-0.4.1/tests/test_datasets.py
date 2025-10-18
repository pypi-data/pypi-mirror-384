"""
Tests for dataset classes.
"""

import pytest
from embedding_model.datasets.mixed import JsonDataset, MixedJsonConversationDataset


class TestJsonDataset:
    """Test the JsonDataset class."""
    
    def test_dataset_initialization(self, sample_documents):
        """Test dataset initialization."""
        dataset = JsonDataset(sample_documents)
        
        assert len(dataset) == len(sample_documents)
        assert dataset._texts is not None
        assert len(dataset._texts) == len(sample_documents)
    
    def test_dataset_getitem(self, sample_documents):
        """Test getting items from dataset."""
        dataset = JsonDataset(sample_documents)
        
        # Test getting individual items
        for i in range(len(dataset)):
            text = dataset[i]
            assert isinstance(text, str)
            assert len(text) > 0
    
    def test_custom_separators(self, sample_documents):
        """Test dataset with custom separators."""
        dataset = JsonDataset(
            sample_documents,
            text_separator=" || ",
            field_kv_sep=" = ",
            field_pair_sep=" && "
        )
        
        text = dataset[0]
        assert " = " in text  # Custom key-value separator
        assert " && " in text  # Custom field pair separator
    
    def test_empty_dataset(self):
        """Test dataset with empty records."""
        dataset = JsonDataset([])
        
        assert len(dataset) == 0
        assert dataset._texts == []
    
    def test_single_document(self, sample_documents):
        """Test dataset with single document."""
        dataset = JsonDataset([sample_documents[0]])
        
        assert len(dataset) == 1
        text = dataset[0]
        assert isinstance(text, str)
        assert "MacBook Pro" in text  # Should contain document content
    
    def test_backward_compatibility_alias(self, sample_documents):
        """Test that MixedJsonConversationDataset works with JsonDataset for JSON-only data."""
        dataset1 = JsonDataset(sample_documents)
        dataset2 = MixedJsonConversationDataset(
            sample_documents,
            text_separator=" \n ",
            field_kv_sep=": ",
            field_pair_sep=" | "
        )
        
        # Should have same length
        assert len(dataset1) == len(dataset2)
        
        # Should produce the same text outputs for JSON data
        for i in range(len(dataset1)):
            assert dataset1[i] == dataset2[i]
    
    def test_complex_nested_documents(self):
        """Test dataset with complex nested documents."""
        complex_docs = [
            {
                "product": {
                    "name": "Complex Product",
                    "features": ["feature1", "feature2"],
                    "specs": {
                        "weight": "2kg",
                        "dimensions": {"width": 30, "height": 20}
                    }
                },
                "reviews": [
                    {"rating": 5, "text": "Great!"},
                    {"rating": 4, "text": "Good"}
                ]
            }
        ]
        
        dataset = JsonDataset(complex_docs)
        
        assert len(dataset) == 1
        text = dataset[0]
        
        # Should contain flattened nested content
        assert "product.name: Complex Product" in text
        assert "product.features.0: feature1" in text
        assert "product.specs.dimensions.width: 30" in text
        assert "reviews.0.rating: 5" in text
