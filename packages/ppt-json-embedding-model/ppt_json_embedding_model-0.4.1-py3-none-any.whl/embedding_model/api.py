"""
High-level Python API for JSON embedding and search.

This module provides a simple interface for developers to integrate 
JSON embedding and search capabilities into their applications.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import json

import torch
import numpy as np

from .config import load_config
from .tokenizer import CharVocab
from .model.charcnn import CharCNNEncoder
from .datasets.collate import make_char_collate
from .data.flatten import flatten_to_text
from .download import get_default_model_path


class JSONEmbeddingModel:
    """
    High-level interface for JSON embedding and search.
    
    Example usage:
        # Initialize model
        model = JSONEmbeddingModel("path/to/model.pt")
        
        # Embed documents
        docs = [{"title": "Doc 1", "content": "..."}, {"title": "Doc 2", "content": "..."}]
        embeddings = model.embed_documents(docs)
        
        # Search
        results = model.search("search query", docs, embeddings, top_k=5)
    """
    
    def __init__(
        self, 
        model_path: Optional[str] = None, 
        config_path: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Initialize the JSON embedding model.
        
        Args:
            model_path: Path to model checkpoint. If None, uses JSON_EMBED_MODEL_PATH env var or auto-download
            config_path: Path to config YAML. If None, uses default config
            device: Device to run model on ('cpu', 'cuda', 'auto'). If None, auto-detects
        """
        self.logger = logging.getLogger(__name__)
        
        # Set device
        if device is None or device == 'auto':
            try:
                # Try CUDA first if available
                if torch.cuda.is_available():
                    # Test CUDA initialization to catch Windows service errors
                    torch.zeros(1).cuda()
                    self.device = 'cuda'
                    self.logger.info("Using CUDA device")
                else:
                    self.device = 'cpu'
                    self.logger.info("CUDA not available, using CPU")
            except Exception as e:
                # Fallback to CPU if CUDA fails (e.g., Windows service errors)
                self.logger.warning(f"CUDA initialization failed ({e}), falling back to CPU")
                self.device = 'cpu'
        else:
            self.device = device
            
        # Load config
        if config_path is None:
            # Use default config from package
            config_path = Path(__file__).parent / "config" / "default.yaml"
        self.config = load_config(str(config_path))
        
        # Load model
        if model_path is None:
            model_path = str(get_default_model_path())
        
        self.model_path = model_path
        self.model = None
        self.vocab = None
        self.collate_fn = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the model, vocabulary, and collate function."""
        self.logger.info(f"Loading model from: {self.model_path}")
        
        # Load checkpoint
        checkpoint = torch.load(self.model_path, map_location=self.device)
        
        # Use vocabulary from checkpoint if available, otherwise build from config
        if 'vocab' in checkpoint:
            # Use the vocabulary that was used during training
            vocab_list = checkpoint['vocab']
            if isinstance(vocab_list, list):
                # Convert list back to CharVocab
                stoi = {char: i for i, char in enumerate(vocab_list)}
                self.vocab = CharVocab(
                    stoi=stoi,
                    itos=vocab_list,
                    unk_token=self.config.vocab.unk_token if self.config else "?"
                )
            else:
                # Assume it's already a CharVocab object
                self.vocab = vocab_list
            self.logger.info(f"Using vocabulary from checkpoint ({len(self.vocab.stoi)} characters)")
        else:
            # Fallback to building from config
            self.vocab = CharVocab.build(
                self.config.vocab.initial,
                self.config.vocab.unk_token
            )
            self.logger.info(f"Building vocabulary from config ({len(self.vocab.stoi)} characters)")
        
        # Create model with the correct vocabulary size
        self.model = CharCNNEncoder(
            vocab_size=len(self.vocab.stoi),
            embedding_dim=self.config.char_embed_dim if self.config else 32,
            conv_channels=self.config.conv_channels if self.config else 256,
            kernel_sizes=self.config.kernel_sizes if self.config else [3, 5, 7],
            projection_dim=self.config.projection_dim if self.config else 256,
            layer_norm=self.config.layer_norm if self.config else True
        )
        
        # Load weights
        self.model.load_state_dict(checkpoint['model'])
        self.model.to(self.device)
        self.model.eval()
        
        # Create collate function
        self.collate_fn = make_char_collate(
            vocab=self.vocab,
            max_len=self.config.max_chars if self.config else 2048
        )
        
        self.logger.info("Model loaded successfully")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            1D numpy array of embeddings
        """
        with torch.no_grad():
            ids, mask = self.collate_fn([text])
            embedding = self.model(ids, mask).cpu().numpy()[0]
            return embedding.astype(np.float32)
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Embed multiple text strings.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            2D numpy array of embeddings (num_texts, embedding_dim)
        """
        embeddings = []
        
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                ids, mask = self.collate_fn(batch_texts)
                batch_embeddings = self.model(ids, mask).cpu().numpy()
                embeddings.append(batch_embeddings)
        
        if not embeddings:
            # Return empty array with correct shape for empty input
            return np.empty((0, self.model.proj.out_features), dtype=np.float32)
        return np.vstack(embeddings).astype(np.float32)
    
    def embed_json_object(self, obj: Dict[str, Any]) -> np.ndarray:
        """
        Embed a single JSON object.
        
        Args:
            obj: JSON object (dictionary) to embed
            
        Returns:
            1D numpy array of embeddings
        """
        text = flatten_to_text(
            obj,
            text_separator=self.config.text_separator,
            field_kv_sep=self.config.field_kv_sep,
            field_pair_sep=self.config.field_pair_sep
        )
        return self.embed_text(text)
    
    def embed_documents(self, documents: List[Dict[str, Any]], batch_size: int = 32) -> np.ndarray:
        """
        Embed multiple JSON documents.
        
        Args:
            documents: List of JSON objects (dictionaries) to embed
            batch_size: Batch size for processing
            
        Returns:
            2D numpy array of embeddings (num_docs, embedding_dim)
        """
        texts = []
        for doc in documents:
            text = flatten_to_text(
                doc,
                text_separator=self.config.text_separator,
                field_kv_sep=self.config.field_kv_sep,
                field_pair_sep=self.config.field_pair_sep
            )
            texts.append(text)
        
        return self.embed_texts(texts, batch_size=batch_size)
    
    def search(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        embeddings: Optional[np.ndarray] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[float, int, Dict[str, Any]]]:
        """
        Search documents using semantic similarity.
        
        Args:
            query: Search query text
            documents: List of JSON documents to search
            embeddings: Pre-computed embeddings. If None, computes on-the-fly
            top_k: Number of top results to return
            filters: Optional filters to apply (key-value pairs)
            
        Returns:
            List of (similarity_score, document_index, document) tuples
        """
        # Embed query
        query_embedding = self.embed_text(query)
        
        # Get or compute document embeddings
        if embeddings is None:
            embeddings = self.embed_documents(documents)
        
        # Apply filters if provided
        valid_indices = list(range(len(documents)))
        if filters:
            valid_indices = []
            for i, doc in enumerate(documents):
                if self._matches_filters(doc, filters):
                    valid_indices.append(i)
        
        if not valid_indices:
            return []
        
        # Compute similarities for valid documents
        valid_embeddings = embeddings[valid_indices]
        similarities = np.dot(valid_embeddings, query_embedding)
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            doc_idx = valid_indices[idx]
            similarity = float(similarities[idx])
            document = documents[doc_idx]
            results.append((similarity, doc_idx, document))
        
        return results
    
    def _matches_filters(self, document: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if document matches all filters."""
        for key, expected_value in filters.items():
            if key not in document:
                return False
            
            doc_value = document[key]
            if isinstance(expected_value, str) and isinstance(doc_value, str):
                # Case-insensitive string comparison
                if expected_value.lower() != doc_value.lower():
                    return False
            else:
                if doc_value != expected_value:
                    return False
        
        return True


# Convenience functions for quick usage
def embed_documents(
    documents: List[Dict[str, Any]], 
    model_path: Optional[str] = None,
    batch_size: int = 32,
    device: Optional[str] = None
) -> np.ndarray:
    """
    Quick function to embed documents without creating a model instance.
    
    Args:
        documents: List of JSON documents to embed
        model_path: Path to model checkpoint
        batch_size: Batch size for processing
        device: Device to use ('cpu', 'cuda', 'auto', or None for auto-detect)
        
    Returns:
        2D numpy array of embeddings
    """
    model = JSONEmbeddingModel(model_path, device=device)
    return model.embed_documents(documents, batch_size=batch_size)


def search_documents(
    query: str,
    documents: List[Dict[str, Any]],
    model_path: Optional[str] = None,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
    device: Optional[str] = None
) -> List[Tuple[float, int, Dict[str, Any]]]:
    """
    Quick function to search documents without creating a model instance.
    
    Args:
        query: Search query text
        documents: List of JSON documents to search
        model_path: Path to model checkpoint
        top_k: Number of top results to return
        filters: Optional filters to apply
        device: Device to use ('cpu', 'cuda', 'auto', or None for auto-detect)
        
    Returns:
        List of (similarity_score, document_index, document) tuples
    """
    model = JSONEmbeddingModel(model_path, device=device)
    return model.search(query, documents, top_k=top_k, filters=filters)
