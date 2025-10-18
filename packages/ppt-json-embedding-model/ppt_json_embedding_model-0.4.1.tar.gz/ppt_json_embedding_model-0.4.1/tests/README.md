# Tests for PPT JSON Embedding Model

This directory contains comprehensive tests for the JSON embedding model package.

## Test Structure

- `conftest.py` - Pytest fixtures and configuration
- `test_api.py` - Tests for the high-level Python API
- `test_tokenizer.py` - Tests for character tokenization
- `test_data_flatten.py` - Tests for JSON flattening functionality
- `test_model.py` - Tests for the CharCNN model
- `test_datasets.py` - Tests for dataset classes
- `test_cli.py` - Tests for CLI functionality
- `test_api_integration.py` - Integration tests for the API (moved from root)
- `test_adaptive_search.py` - Tests for adaptive search (moved from root)
- `test_search_improvements.py` - Tests for search improvements (moved from root)

## Running Tests

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only  
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

### Run with Coverage

```bash
pytest --cov=src/embedding_model --cov-report=html
```

### Run Specific Test Files

```bash
# Test API functionality
pytest tests/test_api.py

# Test tokenizer
pytest tests/test_tokenizer.py

# Test CLI
pytest tests/test_cli.py
```

## Test Coverage Goals

- **API**: Complete coverage of JSONEmbeddingModel class and convenience functions
- **Core Components**: Tokenizer, model, data flattening
- **CLI**: Command-line interface functionality
- **Error Handling**: Edge cases and error conditions
- **Integration**: End-to-end functionality with mock models

Target: **80%+ code coverage**
