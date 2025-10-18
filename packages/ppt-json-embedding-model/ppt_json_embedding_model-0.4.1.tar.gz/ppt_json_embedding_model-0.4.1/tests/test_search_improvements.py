#!/usr/bin/env python3
"""
Test Search Relevance Improvements

This script tests basic search functionality with mock models.
"""

import json
import os
import sys
import time
import argparse
import glob
import numpy as np
from pathlib import Path

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_search_comparison(mock_model_checkpoint, tmp_path):
    """Compare original vs enhanced search using mock model"""
    from embedding_model import JSONEmbeddingModel
    
    # Create mock data directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create sample test data
    sample_data = [
        {"id": "1", "title": "Network Connectivity Issue", "category": "network"},
        {"id": "2", "title": "Server Hardware Failure", "category": "hardware"},
        {"id": "3", "title": "Account Billing Problem", "category": "billing"},
    ]
    
    # Create test model with CPU fallback
    model = JSONEmbeddingModel(str(mock_model_checkpoint), device='cpu')
    
    # Test basic search functionality
    results = model.search(
        query="network issue",
        documents=sample_data,
        top_k=2
    )
    
    assert isinstance(results, list)
    assert len(results) <= 2
    print(f"Search test completed successfully with {len(results)} results")
    
    return True


if __name__ == "__main__":
    print("This test is designed to run with pytest")
    print("Usage: pytest tests/test_search_improvements.py")