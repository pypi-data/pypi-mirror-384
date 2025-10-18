#!/usr/bin/env python3
"""
Adaptive Search Engine for Any JSON Data

This version automatically adapts to any JSON schema and data source,
making it suitable for diverse datasets beyond the original training data.

Key Features:
1. Auto-detects schema and important fields
2. Generic domain detection based on content
3. Configurable field boosting
4. Schema analysis and suggestions
5. Flexible for any JSON structure

Usage:
    python adaptive_search.py --query "search term" --data file.jsonl --analyze
"""

import argparse
import json
import numpy as np
import torch
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional, Set
from dataclasses import dataclass
from collections import defaultdict, Counter

# Import your model components
try:
    from embedding_model.config import load_config
    from embedding_model.tokenizer import CharVocab
    from embedding_model.model.charcnn import CharCNNEncoder
    from embedding_model.datasets.collate import make_char_collate
    from embedding_model.download import get_default_model_path
    from embedding_model.data.flatten import flatten_to_text
except ImportError:
    from src.embedding_model.config import load_config
    from src.embedding_model.tokenizer import CharVocab
    from src.embedding_model.model.charcnn import CharCNNEncoder
    from src.embedding_model.datasets.collate import make_char_collate
    from src.embedding_model.download import get_default_model_path
    from src.embedding_model.data.flatten import flatten_to_text

@dataclass
class SchemaInfo:
    """Information about the dataset schema"""
    field_names: Set[str]
    field_types: Dict[str, str]
    field_samples: Dict[str, List[str]]
    text_fields: List[str]
    id_fields: List[str]
    numeric_fields: List[str]
    categorical_fields: Dict[str, List[str]]
    record_count: int

@dataclass
class SearchConfig:
    """Adaptive search configuration"""
    important_fields: List[str]
    boost_factors: Dict[str, float]
    domain_keywords: Dict[str, List[str]]
    hybrid_weight: float = 0.7
    text_field_weight: float = 1.5
    id_field_weight: float = 3.0

@dataclass
class AdaptiveSearchResult:
    """Search result with adaptive metadata"""
    record: Dict[str, Any]
    score: float
    index: int
    field_matches: Dict[str, List[str]]
    boost_factors: Dict[str, float]
    explanation: str
    confidence: float

class SchemaAnalyzer:
    """Analyzes JSON data to understand schema and content patterns"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_schema(self, records: List[Dict[str, Any]], sample_size: int = 1000) -> SchemaInfo:
        """Analyze dataset schema and content patterns"""
        self.logger.info(f"Analyzing schema from {len(records)} records...")
        
        # Sample for efficiency
        sample_records = records[:min(sample_size, len(records))]
        
        # Collect field information
        field_names = set()
        field_types = defaultdict(Counter)
        field_samples = defaultdict(list)
        
        for record in sample_records:
            for field, value in record.items():
                field_names.add(field)
                
                # Determine type
                if value is None:
                    field_types[field]['null'] += 1
                elif isinstance(value, bool):
                    field_types[field]['boolean'] += 1
                elif isinstance(value, int):
                    field_types[field]['integer'] += 1
                elif isinstance(value, float):
                    field_types[field]['float'] += 1
                elif isinstance(value, str):
                    field_types[field]['string'] += 1
                else:
                    field_types[field]['other'] += 1
                
                # Collect samples
                if value and len(field_samples[field]) < 10:
                    field_samples[field].append(str(value))
        
        # Determine dominant types
        dominant_types = {}
        for field, type_counts in field_types.items():
            dominant_types[field] = type_counts.most_common(1)[0][0]
        
        # Categorize fields
        text_fields = []
        id_fields = []
        numeric_fields = []
        categorical_fields = {}
        
        for field in field_names:
            field_lower = field.lower()
            samples = field_samples[field]
            
            # ID fields (contain 'id', unique values, etc.)
            if ('id' in field_lower or 'key' in field_lower or 'number' in field_lower or
                'serial' in field_lower or 'ref' in field_lower):
                id_fields.append(field)
            
            # Numeric fields
            elif dominant_types[field] in ['integer', 'float']:
                numeric_fields.append(field)
            
            # Text fields (long strings, descriptions, etc.)
            elif dominant_types[field] == 'string':
                # Check if text-like (longer strings)
                avg_length = np.mean([len(s) for s in samples if s]) if samples else 0
                
                if avg_length > 20 or any(word in field_lower for word in 
                    ['description', 'note', 'comment', 'text', 'message', 'detail']):
                    text_fields.append(field)
                else:
                    # Categorical (short strings, limited values)
                    unique_values = list(set(samples))
                    if len(unique_values) <= 20 and len(samples) > 0:
                        categorical_fields[field] = unique_values
        
        return SchemaInfo(
            field_names=field_names,
            field_types=dominant_types,
            field_samples=dict(field_samples),
            text_fields=text_fields,
            id_fields=id_fields,
            numeric_fields=numeric_fields,
            categorical_fields=categorical_fields,
            record_count=len(records)
        )
    
    def suggest_search_config(self, schema: SchemaInfo) -> SearchConfig:
        """Suggest search configuration based on schema analysis"""
        self.logger.info("Generating adaptive search configuration...")
        
        # Determine important fields
        important_fields = []
        boost_factors = {}
        
        # Prioritize fields by importance
        for field in schema.text_fields:
            important_fields.append(field)
            boost_factors[field] = 1.5  # Text fields get moderate boost
        
        for field in schema.id_fields:
            important_fields.append(field)
            boost_factors[field] = 3.0  # ID fields get high boost for exact matches
        
        # Add name-like fields
        for field in schema.field_names:
            if 'name' in field.lower() or 'title' in field.lower():
                important_fields.append(field)
                boost_factors[field] = 2.0
        
        # Generate domain keywords from categorical fields and samples
        domain_keywords = {}
        for field, values in schema.categorical_fields.items():
            # Use categorical values as potential domain indicators
            domain_keywords[field] = [str(v).lower() for v in values if v and len(str(v)) > 2]
        
        return SearchConfig(
            important_fields=important_fields,
            boost_factors=boost_factors,
            domain_keywords=domain_keywords,
            hybrid_weight=0.7,
            text_field_weight=1.5,
            id_field_weight=3.0
        )
    
    def print_schema_analysis(self, schema: SchemaInfo, config: SearchConfig):
        """Print detailed schema analysis"""
        print("\nDataset Schema Analysis")
        print("=" * 60)
        print(f"Total Records: {schema.record_count:,}")
        print(f"Total Fields: {len(schema.field_names)}")
        print()
        
        if schema.text_fields:
            print(f"Text Fields ({len(schema.text_fields)}): {', '.join(schema.text_fields)}")
        if schema.id_fields:
            print(f"ID Fields ({len(schema.id_fields)}): {', '.join(schema.id_fields)}")
        if schema.numeric_fields:
            print(f"Numeric Fields ({len(schema.numeric_fields)}): {', '.join(schema.numeric_fields)}")
        
        if schema.categorical_fields:
            print(f"\nCategorical Fields:")
            for field, values in list(schema.categorical_fields.items())[:5]:
                print(f"  {field}: {values[:5]}{'...' if len(values) > 5 else ''}")
        
        print(f"\nRecommended Search Configuration:")
        print(f"  Important Fields: {config.important_fields[:5]}{'...' if len(config.important_fields) > 5 else ''}")
        print(f"  Boost Factors: {dict(list(config.boost_factors.items())[:3])}{'...' if len(config.boost_factors) > 3 else ''}")
        print(f"  Hybrid Weight: {config.hybrid_weight}")
        print()

class AdaptiveSearchEngine:
    """Search engine that adapts to any JSON data structure"""
    
    def __init__(self, model_path: str = None, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Load model
        if model_path:
            self.model_path = model_path
        else:
            self.model_path = str(get_default_model_path())
            
        self.config = load_config(config_path) if config_path else None
        self.model, self.collate, self.vocab = self._load_model()
        
        # Schema and search configuration
        self.schema: Optional[SchemaInfo] = None
        self.search_config: Optional[SearchConfig] = None
        
        # Data storage
        self.records: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        
    def _load_model(self):
        """Load the embedding model"""
        self.logger.info(f"Loading model from: {self.model_path}")
        
        ckpt = torch.load(self.model_path, map_location="cpu")
        itos = ckpt["vocab"]
        vocab = CharVocab(stoi={ch: i for i, ch in enumerate(itos)}, itos=itos, unk_token="?")
        
        model = CharCNNEncoder(
            vocab_size=len(vocab.itos),
            embedding_dim=self.config.char_embed_dim if self.config else 32,
            conv_channels=self.config.conv_channels if self.config else 256,
            kernel_sizes=self.config.kernel_sizes if self.config else [3, 5, 7],
            projection_dim=self.config.projection_dim if self.config else 256,
            layer_norm=self.config.layer_norm if self.config else True,
        )
        model.load_state_dict(ckpt["model"])
        model.eval()
        
        collate = make_char_collate(vocab, self.config.max_chars if self.config else 2048)
        
        return model, collate, vocab
    
    def load_data(self, jsonl_path: str, analyze_schema: bool = True, custom_config: SearchConfig = None):
        """Load data and optionally analyze schema"""
        self.logger.info(f"Loading data from: {jsonl_path}")
        
        # Load records
        self.records = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.records.append(json.loads(line))
        
        self.logger.info(f"PASS Loaded {len(self.records)} records")
        
        if analyze_schema:
            # Analyze schema
            analyzer = SchemaAnalyzer()
            self.schema = analyzer.analyze_schema(self.records)
            
            # Generate or use custom search config
            if custom_config:
                self.search_config = custom_config
                self.logger.info("Using custom search configuration")
            else:
                self.search_config = analyzer.suggest_search_config(self.schema)
                self.logger.info("Generated adaptive search configuration")
        
        # Generate embeddings
        self.logger.info("Generating embeddings...")
        texts = [flatten_to_text(record) for record in self.records]
        self.embeddings = self._generate_embeddings(texts)
        
        self.logger.info(f"PASS Ready for search with {self.embeddings.shape[0]} embeddings")
    
    def _generate_embeddings(self, texts: List[str], batch_size: int = 256) -> np.ndarray:
        """Generate embeddings for texts"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            ids, mask = self.collate(batch_texts)
            
            with torch.no_grad():
                batch_embs = self.model(ids, mask).cpu().numpy()
            embeddings.append(batch_embs)
            
            if i % (batch_size * 4) == 0:
                progress = min(100, (i / len(texts)) * 100)
                self.logger.info(f"  Progress: {progress:.1f}%")
        
        return np.concatenate(embeddings, axis=0) if embeddings else np.empty((0, self.model.projection_dim))
    
    def _extract_field_matches(self, query: str, record: Dict[str, Any]) -> Dict[str, List[str]]:
        """Find which fields match query terms"""
        query_terms = re.findall(r'\b\w+\b', query.lower())
        field_matches = defaultdict(list)
        
        for field, value in record.items():
            if isinstance(value, (str, int, float)) and value:
                value_str = str(value).lower()
                for term in query_terms:
                    if term in value_str:
                        field_matches[field].append(term)
        
        return dict(field_matches)
    
    def _calculate_adaptive_boost(self, record: Dict[str, Any], field_matches: Dict[str, List[str]]) -> float:
        """Calculate boost factor based on field matches and schema"""
        if not self.search_config:
            return 1.0
        
        boost = 1.0
        
        for field, matches in field_matches.items():
            base_boost = len(matches) * 0.1  # Base boost per match
            
            # Apply configured boost factors
            if field in self.search_config.boost_factors:
                field_boost = self.search_config.boost_factors[field]
                boost += base_boost * field_boost
            else:
                # Default boost for unrecognized fields
                boost += base_boost
        
        return min(boost, 4.0)  # Cap boost at 4x
    
    def _calculate_confidence(self, score: float, field_matches: Dict[str, List[str]], query: str) -> float:
        """Calculate confidence score for the result"""
        base_confidence = min(score * 2, 1.0)  # Base confidence from embedding score
        
        # Boost confidence for field matches
        if field_matches:
            match_confidence = min(len(field_matches) * 0.2, 0.5)
            base_confidence += match_confidence
        
        # Boost confidence for exact term matches
        query_terms = set(re.findall(r'\b\w+\b', query.lower()))
        all_matches = set()
        for matches in field_matches.values():
            all_matches.update(matches)
        
        if query_terms and all_matches:
            term_overlap = len(query_terms & all_matches) / len(query_terms)
            base_confidence += term_overlap * 0.3
        
        return min(base_confidence, 1.0)
    
    def search(self, 
               query: str, 
               topk: int = 10,
               field_filters: Dict[str, str] = None,
               hybrid_weight: float = None,
               min_confidence: float = 0.0) -> List[AdaptiveSearchResult]:
        """Adaptive search that works with any data structure"""
        
        if self.embeddings is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        self.logger.info(f"Adaptive search: '{query}'")
        
        # Use provided hybrid weight or default from config
        if hybrid_weight is None:
            hybrid_weight = self.search_config.hybrid_weight if self.search_config else 0.7
        
        # Generate query embedding
        query_embedding = self._generate_embeddings([query])[0]
        
        # Semantic similarity scores
        semantic_scores = np.dot(self.embeddings, query_embedding)
        
        # Apply field filters if specified
        valid_indices = list(range(len(self.records)))
        if field_filters:
            valid_indices = []
            for i, record in enumerate(self.records):
                match = True
                for field, value in field_filters.items():
                    if str(record.get(field, '')).lower() != value.lower():
                        match = False
                        break
                if match:
                    valid_indices.append(i)
            
            self.logger.info(f"Field filters applied: {len(valid_indices)} records remaining")
        
        # Process each valid record
        results = []
        for idx in valid_indices:
            record = self.records[idx]
            semantic_score = semantic_scores[idx]
            
            # Find field matches
            field_matches = self._extract_field_matches(query, record)
            
            # Calculate keyword score
            keyword_score = 0.0
            if field_matches:
                total_matches = sum(len(matches) for matches in field_matches.values())
                keyword_score = min(total_matches / 10.0, 1.0)  # Normalize to 0-1
            
            # Hybrid score
            final_score = (hybrid_weight * semantic_score + 
                          (1 - hybrid_weight) * keyword_score)
            
            # Apply adaptive boosting
            boost_factor = self._calculate_adaptive_boost(record, field_matches)
            final_score *= boost_factor
            
            # Calculate confidence
            confidence = self._calculate_confidence(final_score, field_matches, query)
            
            # Skip low confidence results
            if confidence < min_confidence:
                continue
            
            # Create explanation
            explanation_parts = []
            if field_matches:
                explanation_parts.append(f"Field matches in {list(field_matches.keys())}")
            if semantic_score > 0.3:
                explanation_parts.append(f"Semantic similarity ({semantic_score:.3f})")
            if keyword_score > 0.2:
                explanation_parts.append(f"Keyword matches ({keyword_score:.3f})")
            
            explanation = " | ".join(explanation_parts) if explanation_parts else "Semantic similarity"
            
            result = AdaptiveSearchResult(
                record=record,
                score=final_score,
                index=idx,
                field_matches=field_matches,
                boost_factors={'total_boost': boost_factor},
                explanation=explanation,
                confidence=confidence
            )
            
            results.append(result)
        
        # Sort by score and return top-k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:topk]
    
    def explain_search(self, query: str, topk: int = 5) -> None:
        """Print detailed search explanation"""
        results = self.search(query, topk=topk)
        
        print(f"\nAdaptive Search Results for: '{query}'")
        print("=" * 80)
        
        if self.schema:
            print(f"Dataset: {self.schema.record_count} records, {len(self.schema.field_names)} fields")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result.score:.4f} | Confidence: {result.confidence:.3f}")
            
            # Show key fields (first few non-null fields)
            key_info = {}
            field_count = 0
            for field, value in result.record.items():
                if value and field_count < 3:
                    if isinstance(value, str) and len(value) > 50:
                        key_info[field] = value[:50] + "..."
                    else:
                        key_info[field] = str(value)
                    field_count += 1
            
            if key_info:
                print(f"   Fields: {key_info}")
            
            if result.field_matches:
                print(f"   Matches: {result.field_matches}")
            
            print(f"   Explanation: {result.explanation}")
            print()

def main():
    parser = argparse.ArgumentParser(description="Adaptive Search for Any JSON Data")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--data", required=True, help="JSONL file to search")
    parser.add_argument("--model", help="Path to model checkpoint")
    parser.add_argument("--config", help="Path to config YAML")
    parser.add_argument("--topk", type=int, default=10, help="Number of results")
    parser.add_argument("--analyze", action="store_true", help="Show schema analysis")
    parser.add_argument("--where", nargs='*', default=[], help="Field filters (field=value)")
    parser.add_argument("--hybrid-weight", type=float, default=0.7, help="Semantic vs keyword balance")
    parser.add_argument("--min-confidence", type=float, default=0.0, help="Minimum confidence threshold")
    parser.add_argument("--explain", action="store_true", help="Show detailed explanations")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Parse field filters
    field_filters = {}
    for filter_expr in args.where:
        if '=' in filter_expr:
            key, value = filter_expr.split('=', 1)
            field_filters[key.strip()] = value.strip()
    
    # Initialize search engine
    search_engine = AdaptiveSearchEngine(model_path=args.model, config_path=args.config)
    
    # Load data with schema analysis
    search_engine.load_data(args.data, analyze_schema=True)
    
    # Show schema analysis if requested
    if args.analyze:
        analyzer = SchemaAnalyzer()
        if search_engine.schema and search_engine.search_config:
            analyzer.print_schema_analysis(search_engine.schema, search_engine.search_config)
    
    # Perform search if query provided
    if args.query:
        if args.explain:
            search_engine.explain_search(args.query, topk=args.topk)
        else:
            results = search_engine.search(
                query=args.query,
                topk=args.topk,
                field_filters=field_filters if field_filters else None,
                hybrid_weight=args.hybrid_weight,
                min_confidence=args.min_confidence
            )
            
            print(f"\nResults for: '{args.query}'")
            print("-" * 60)
            
            for i, result in enumerate(results, 1):
                # Show first few key fields
                key_fields = {}
                field_count = 0
                for field, value in result.record.items():
                    if value and field_count < 2:
                        if isinstance(value, str) and len(value) > 40:
                            key_fields[field] = value[:40] + "..."
                        else:
                            key_fields[field] = str(value)
                        field_count += 1
                
                print(f"{i}. {result.score:.4f} (conf: {result.confidence:.2f}) | {key_fields}")
                if result.field_matches:
                    print(f"   Matches: {result.field_matches}")
    
    else:
        print("\nSchema analysis complete. Use --query to search, or --analyze to see details.")

if __name__ == "__main__":
    main()
