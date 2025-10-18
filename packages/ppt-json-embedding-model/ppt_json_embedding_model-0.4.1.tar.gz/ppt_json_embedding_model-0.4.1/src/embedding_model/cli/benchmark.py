#!/usr/bin/env python3
"""
Comprehensive Benchmarking Suite for PPT JSON Embedding Model

This script evaluates the embedding model across multiple dimensions:
- Embedding Quality & Consistency
- Search Relevance & Ranking
- Performance & Speed
- Cross-Domain Retrieval
- Domain-Specific Tasks

Usage:
    python benchmark_embedding_model.py --data-dir data/ --output-dir benchmarks/
"""

import argparse
import json
import time
import os
import sys
import numpy as np
import torch
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import psutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import from installed package first, then from src
try:
    from embedding_model.config import load_config
    from embedding_model.tokenizer import CharVocab
    from embedding_model.model.charcnn import CharCNNEncoder
    from embedding_model.datasets.collate import make_char_collate
    from embedding_model.data.flatten import flatten_to_text
    from embedding_model.download import get_default_model_path
except ImportError:
    from src.embedding_model.config import load_config
    from src.embedding_model.tokenizer import CharVocab
    from src.embedding_model.model.charcnn import CharCNNEncoder
    from src.embedding_model.datasets.collate import make_char_collate
    from src.embedding_model.data.flatten import flatten_to_text
    from src.embedding_model.download import get_default_model_path

@dataclass
class BenchmarkResults:
    """Container for benchmark results"""
    embedding_quality: Dict[str, float]
    search_metrics: Dict[str, float]
    performance_metrics: Dict[str, float]
    cross_domain_metrics: Dict[str, float]
    domain_specific: Dict[str, Dict[str, float]]

class EmbeddingBenchmark:
    def __init__(self, model_path: str = None, config_path: str = None, batch_size: int = 256):
        """Initialize the benchmark suite"""
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)
        
        # Load model
        if model_path:
            self.model_path = model_path
        else:
            self.model_path = str(get_default_model_path())
            
        self.config = load_config(config_path) if config_path else None
        self.model, self.collate, self.vocab = self._load_model()
        
        # Benchmark data storage
        self.embeddings_cache = {}
        self.records_cache = {}
        
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
    
    def load_dataset(self, jsonl_path: str, limit: int = None) -> Tuple[List[Dict], List[str]]:
        """Load records from JSONL file"""
        records = []
        texts = []
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                if line.strip():
                    record = json.loads(line)
                    records.append(record)
                    texts.append(flatten_to_text(record))
        
        return records, texts
    
    def generate_embeddings(self, texts: List[str], cache_key: str = None) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if cache_key and cache_key in self.embeddings_cache:
            return self.embeddings_cache[cache_key]
        
        embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i+self.batch_size]
            ids, mask = self.collate(batch_texts)
            
            with torch.no_grad():
                batch_embs = self.model(ids, mask).cpu().numpy()
            embeddings.append(batch_embs)
        
        result = np.concatenate(embeddings, axis=0) if embeddings else np.empty((0, self.model.projection_dim))
        
        if cache_key:
            self.embeddings_cache[cache_key] = result
            
        return result
    
    def test_embedding_quality(self, datasets: Dict[str, str]) -> Dict[str, float]:
        """Test embedding quality and consistency"""
        self.logger.info("Testing Embedding Quality...")
        
        results = {}
        
        # Test 1: Reproducibility (same input should give same embedding)
        test_texts = ["Sample device configuration", "Network error in system", "Customer account status"]
        emb1 = self.generate_embeddings(test_texts)
        emb2 = self.generate_embeddings(test_texts)
        
        reproducibility_score = np.mean([
            np.allclose(emb1[i], emb2[i], atol=1e-6) for i in range(len(test_texts))
        ])
        results['reproducibility'] = reproducibility_score
        
        # Test 2: Embedding distribution analysis
        all_embeddings = []
        for dataset_name, path in datasets.items():
            records, texts = self.load_dataset(path, limit=1000)  # Sample for efficiency
            embs = self.generate_embeddings(texts, cache_key=f"quality_{dataset_name}")
            all_embeddings.append(embs)
        
        combined_embs = np.concatenate(all_embeddings, axis=0)
        
        # Check for degenerate embeddings (all similar)
        pairwise_sims = np.dot(combined_embs, combined_embs.T)
        mean_similarity = np.mean(pairwise_sims)
        std_similarity = np.std(pairwise_sims)
        
        results['mean_cosine_similarity'] = float(mean_similarity)
        results['std_cosine_similarity'] = float(std_similarity)
        results['embedding_diversity'] = float(std_similarity)  # Higher is better
        
        # Test 3: Embedding magnitude consistency
        norms = np.linalg.norm(combined_embs, axis=1)
        results['mean_embedding_norm'] = float(np.mean(norms))
        results['std_embedding_norm'] = float(np.std(norms))
        
        self.logger.info(f"PASS Embedding Quality Results: {results}")
        return results
    
    def test_search_relevance(self, datasets: Dict[str, str]) -> Dict[str, float]:
        """Test search relevance and ranking quality"""
        self.logger.info("Testing Search Relevance...")
        
        results = {}
        
        # Load all datasets
        all_records = []
        all_texts = []
        dataset_labels = []
        
        for dataset_name, path in datasets.items():
            records, texts = self.load_dataset(path, limit=1000)
            all_records.extend(records)
            all_texts.extend(texts)
            dataset_labels.extend([dataset_name] * len(records))
        
        # Generate embeddings
        all_embeddings = self.generate_embeddings(all_texts, cache_key="search_test")
        
        # Test queries for different domains
        test_queries = {
            "devices": ["network device configuration", "server hardware", "storage system"],
            "tickets": ["system error", "network issue", "hardware failure"],
            "customers": ["account information", "customer data", "user profile"],
            "accounts": ["billing account", "company account", "account details"]
        }
        
        mrr_scores = []  # Mean Reciprocal Rank
        precision_at_k = []
        
        for domain, queries in test_queries.items():
            for query in queries:
                # Generate query embedding
                query_emb = self.generate_embeddings([query])[0]
                
                # Compute similarities
                similarities = np.dot(all_embeddings, query_emb)
                ranked_indices = np.argsort(similarities)[::-1]
                
                # Calculate metrics
                relevant_indices = [i for i, label in enumerate(dataset_labels) 
                                 if self._is_relevant(domain, label)]
                
                # MRR: position of first relevant result
                first_relevant_rank = None
                for rank, idx in enumerate(ranked_indices[:50], 1):
                    if idx in relevant_indices:
                        first_relevant_rank = rank
                        break
                
                if first_relevant_rank:
                    mrr_scores.append(1.0 / first_relevant_rank)
                else:
                    mrr_scores.append(0.0)
                
                # Precision@5
                top_5_relevant = sum(1 for idx in ranked_indices[:5] if idx in relevant_indices)
                precision_at_k.append(top_5_relevant / 5.0)
        
        results['mean_reciprocal_rank'] = float(np.mean(mrr_scores))
        results['precision_at_5'] = float(np.mean(precision_at_k))
        
        self.logger.info(f"PASS Search Relevance Results: {results}")
        return results
    
    def _is_relevant(self, query_domain: str, result_domain: str) -> bool:
        """Determine if a result is relevant to a query domain"""
        domain_mapping = {
            "devices": ["qa-assets"],
            "tickets": ["qa-tickets"], 
            "customers": ["qa-customers"],
            "accounts": ["qa-accounts"]
        }
        
        relevant_datasets = domain_mapping.get(query_domain, [])
        return any(dataset in result_domain for dataset in relevant_datasets)
    
    def test_performance(self, datasets: Dict[str, str]) -> Dict[str, float]:
        """Test embedding generation performance"""
        self.logger.info("Testing Performance...")
        
        results = {}
        
        # Test embedding speed
        test_texts = []
        for path in list(datasets.values())[:2]:  # Use 2 datasets
            _, texts = self.load_dataset(path, limit=500)
            test_texts.extend(texts)
        
        # Measure embedding time
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        embeddings = self.generate_embeddings(test_texts)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        total_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        results['embeddings_per_second'] = len(test_texts) / total_time
        results['seconds_per_1000_embeddings'] = (total_time / len(test_texts)) * 1000
        results['memory_usage_mb'] = memory_usage
        results['total_time_seconds'] = total_time
        
        # Test batch size efficiency
        single_text = test_texts[0]
        
        # Single embedding
        start = time.time()
        single_emb = self.generate_embeddings([single_text])
        single_time = time.time() - start
        
        # Batch embedding (100 copies)
        batch_texts = [single_text] * 100
        start = time.time()
        batch_embs = self.generate_embeddings(batch_texts)
        batch_time = time.time() - start
        
        results['single_embedding_time_ms'] = single_time * 1000
        results['batch_efficiency_ratio'] = (single_time * 100) / batch_time
        
        self.logger.info(f"PASS Performance Results: {results}")
        return results
    
    def test_cross_domain_retrieval(self, datasets: Dict[str, str]) -> Dict[str, float]:
        """Test cross-domain retrieval capabilities"""
        self.logger.info("Testing Cross-Domain Retrieval...")
        
        results = {}
        
        # Load datasets separately
        dataset_data = {}
        for name, path in datasets.items():
            records, texts = self.load_dataset(path, limit=500)
            embeddings = self.generate_embeddings(texts, cache_key=f"cross_domain_{name}")
            dataset_data[name] = {
                'records': records,
                'texts': texts,
                'embeddings': embeddings
            }
        
        # Test cross-domain similarity
        cross_similarities = {}
        
        for source_name, source_data in dataset_data.items():
            for target_name, target_data in dataset_data.items():
                if source_name != target_name:
                    # Sample some records from source
                    sample_size = min(50, len(source_data['embeddings']))
                    sample_indices = np.random.choice(len(source_data['embeddings']), sample_size, replace=False)
                    
                    avg_max_similarity = 0
                    for idx in sample_indices:
                        source_emb = source_data['embeddings'][idx]
                        similarities = np.dot(target_data['embeddings'], source_emb)
                        max_sim = np.max(similarities)
                        avg_max_similarity += max_sim
                    
                    avg_max_similarity /= sample_size
                    cross_similarities[f"{source_name}_to_{target_name}"] = avg_max_similarity
        
        # Calculate overall cross-domain metrics
        similarities_values = list(cross_similarities.values())
        results['mean_cross_domain_similarity'] = float(np.mean(similarities_values))
        results['std_cross_domain_similarity'] = float(np.std(similarities_values))
        
        # Add individual cross-domain scores
        results.update(cross_similarities)
        
        self.logger.info(f"PASS Cross-Domain Results: {results}")
        return results
    
    def test_domain_specific_tasks(self, datasets: Dict[str, str]) -> Dict[str, Dict[str, float]]:
        """Test domain-specific embedding quality"""
        self.logger.info("Testing Domain-Specific Tasks...")
        
        results = {}
        
        for dataset_name, path in datasets.items():
            self.logger.info(f"Testing {dataset_name}...")
            
            records, texts = self.load_dataset(path, limit=1000)
            embeddings = self.generate_embeddings(texts, cache_key=f"domain_{dataset_name}")
            
            domain_results = {}
            
            # Test 1: Clustering quality (silhouette-like metric)
            if len(embeddings) > 10:
                # Sample for efficiency
                sample_size = min(200, len(embeddings))
                sample_indices = np.random.choice(len(embeddings), sample_size, replace=False)
                sample_embs = embeddings[sample_indices]
                
                # Compute pairwise distances
                similarities = np.dot(sample_embs, sample_embs.T)
                
                # Intra-cluster (self) similarity vs inter-cluster similarity
                intra_similarities = np.diag(similarities)  # Self similarity (should be 1.0)
                inter_similarities = similarities[np.triu_indices_from(similarities, k=1)]
                
                domain_results['mean_inter_similarity'] = float(np.mean(inter_similarities))
                domain_results['std_inter_similarity'] = float(np.std(inter_similarities))
                
            # Test 2: Key field preservation (if available)
            if dataset_name == 'qa-tickets' and len(records) > 0:
                # Test if tickets with similar status/priority cluster together
                domain_results.update(self._test_ticket_clustering(records, embeddings))
            elif dataset_name == 'qa-assets' and len(records) > 0:
                # Test if similar devices cluster together
                domain_results.update(self._test_device_clustering(records, embeddings))
            
            results[dataset_name] = domain_results
        
        self.logger.info(f"PASS Domain-Specific Results: {results}")
        return results
    
    def _test_ticket_clustering(self, records: List[Dict], embeddings: np.ndarray) -> Dict[str, float]:
        """Test ticket-specific clustering quality"""
        results = {}
        
        # Group by status if available
        status_groups = defaultdict(list)
        for i, record in enumerate(records):
            status = record.get('InternalStatusCode', record.get('Status', 'Unknown'))
            status_groups[status].append(i)
        
        if len(status_groups) > 1:
            # Calculate within-group vs between-group similarity
            within_similarities = []
            between_similarities = []
            
            for status, indices in status_groups.items():
                if len(indices) > 1:
                    # Within-group similarities
                    group_embs = embeddings[indices]
                    group_sims = np.dot(group_embs, group_embs.T)
                    within_similarities.extend(group_sims[np.triu_indices_from(group_sims, k=1)])
                    
                    # Between-group similarities (sample)
                    other_indices = [i for other_status, other_indices in status_groups.items() 
                                   if other_status != status for i in other_indices[:10]]
                    if other_indices:
                        other_embs = embeddings[other_indices[:10]]
                        between_sims = np.dot(group_embs[:5], other_embs.T)
                        between_similarities.extend(between_sims.flatten())
            
            if within_similarities and between_similarities:
                results['within_status_similarity'] = float(np.mean(within_similarities))
                results['between_status_similarity'] = float(np.mean(between_similarities))
                results['status_separation_score'] = float(
                    np.mean(within_similarities) - np.mean(between_similarities)
                )
        
        return results
    
    def _test_device_clustering(self, records: List[Dict], embeddings: np.ndarray) -> Dict[str, float]:
        """Test device-specific clustering quality"""
        results = {}
        
        # Group by product line or manufacturer if available
        product_groups = defaultdict(list)
        for i, record in enumerate(records):
            product = record.get('ProductLine', record.get('Manufacturer', 'Unknown'))
            product_groups[product].append(i)
        
        if len(product_groups) > 1:
            # Similar logic to ticket clustering
            within_similarities = []
            between_similarities = []
            
            for product, indices in product_groups.items():
                if len(indices) > 1:
                    group_embs = embeddings[indices]
                    group_sims = np.dot(group_embs, group_embs.T)
                    within_similarities.extend(group_sims[np.triu_indices_from(group_sims, k=1)])
                    
                    other_indices = [i for other_product, other_indices in product_groups.items() 
                                   if other_product != product for i in other_indices[:10]]
                    if other_indices:
                        other_embs = embeddings[other_indices[:10]]
                        between_sims = np.dot(group_embs[:5], other_embs.T)
                        between_similarities.extend(between_sims.flatten())
            
            if within_similarities and between_similarities:
                results['within_product_similarity'] = float(np.mean(within_similarities))
                results['between_product_similarity'] = float(np.mean(between_similarities))
                results['product_separation_score'] = float(
                    np.mean(within_similarities) - np.mean(between_similarities)
                )
        
        return results
    
    def run_full_benchmark(self, datasets: Dict[str, str]) -> BenchmarkResults:
        """Run the complete benchmark suite"""
        self.logger.info("Starting Full Benchmark Suite...")
        
        # Run all benchmark categories
        embedding_quality = self.test_embedding_quality(datasets)
        search_metrics = self.test_search_relevance(datasets)
        performance_metrics = self.test_performance(datasets)
        cross_domain_metrics = self.test_cross_domain_retrieval(datasets)
        domain_specific = self.test_domain_specific_tasks(datasets)
        
        results = BenchmarkResults(
            embedding_quality=embedding_quality,
            search_metrics=search_metrics,
            performance_metrics=performance_metrics,
            cross_domain_metrics=cross_domain_metrics,
            domain_specific=domain_specific
        )
        
        self.logger.info("PASS Benchmark Suite Complete!")
        return results
    
    def save_results(self, results: BenchmarkResults, output_path: str):
        """Save benchmark results to JSON"""
        results_dict = {
            'embedding_quality': results.embedding_quality,
            'search_metrics': results.search_metrics,
            'performance_metrics': results.performance_metrics,
            'cross_domain_metrics': results.cross_domain_metrics,
            'domain_specific': results.domain_specific,
            'model_info': {
                'model_path': self.model_path,
                'vocab_size': len(self.vocab.itos),
                'projection_dim': getattr(self.model, 'projection_dim', 'Unknown'),
                'conv_channels': getattr(self.model, 'conv_channels', 'Unknown'),
                'kernel_sizes': getattr(self.model, 'kernel_sizes', 'Unknown')
            },
            'benchmark_config': {
                'batch_size': self.batch_size
            }
        }
        
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Results saved to: {output_path}")

def generate_benchmark_report(results: BenchmarkResults, output_path: str):
    """Generate a human-readable benchmark report"""
    
    report = f"""
# JSON Embedding Model Benchmark Report

## Summary

### Embedding Quality
- **Reproducibility**: {results.embedding_quality.get('reproducibility', 0):.3f}
- **Embedding Diversity**: {results.embedding_quality.get('embedding_diversity', 0):.3f}
- **Mean Embedding Norm**: {results.embedding_quality.get('mean_embedding_norm', 0):.3f}

### Search Performance  
- **Mean Reciprocal Rank**: {results.search_metrics.get('mean_reciprocal_rank', 0):.3f}
- **Precision@5**: {results.search_metrics.get('precision_at_5', 0):.3f}

### Technical Performance
- **Embeddings/Second**: {results.performance_metrics.get('embeddings_per_second', 0):.1f}
- **Memory Usage**: {results.performance_metrics.get('memory_usage_mb', 0):.1f} MB
- **Batch Efficiency**: {results.performance_metrics.get('batch_efficiency_ratio', 0):.2f}x

### Cross-Domain Retrieval
- **Mean Cross-Domain Similarity**: {results.cross_domain_metrics.get('mean_cross_domain_similarity', 0):.3f}

## Detailed Results

### Embedding Quality Metrics
"""
    
    for metric, value in results.embedding_quality.items():
        report += f"- **{metric}**: {value:.4f}\n"
    
    report += "\n### Search Relevance Metrics\n"
    for metric, value in results.search_metrics.items():
        report += f"- **{metric}**: {value:.4f}\n"
    
    report += "\n### Performance Metrics\n"
    for metric, value in results.performance_metrics.items():
        if 'time' in metric.lower() or 'second' in metric.lower():
            report += f"- **{metric}**: {value:.3f}s\n"
        elif 'memory' in metric.lower():
            report += f"- **{metric}**: {value:.1f} MB\n"
        else:
            report += f"- **{metric}**: {value:.3f}\n"
    
    report += "\n### Cross-Domain Metrics\n"
    for metric, value in results.cross_domain_metrics.items():
        report += f"- **{metric}**: {value:.4f}\n"
    
    report += "\n### Domain-Specific Results\n"
    for domain, metrics in results.domain_specific.items():
        report += f"\n#### {domain}\n"
        for metric, value in metrics.items():
            report += f"- **{metric}**: {value:.4f}\n"
    
    report += f"""

## Recommendations

### Performance Optimization
{'- PASS Good performance' if results.performance_metrics.get('embeddings_per_second', 0) > 100 else '- WARNING Consider batch size optimization'}
{'- PASS Efficient memory usage' if results.performance_metrics.get('memory_usage_mb', 0) < 500 else '- WARNING High memory usage detected'}

### Search Quality
{'- PASS Good search relevance' if results.search_metrics.get('mean_reciprocal_rank', 0) > 0.5 else '- WARNING Search relevance could be improved'}
{'- PASS Good precision' if results.search_metrics.get('precision_at_5', 0) > 0.3 else '- WARNING Low precision, consider model retraining'}

### Embedding Quality
{'- PASS Good embedding diversity' if results.embedding_quality.get('embedding_diversity', 0) > 0.1 else '- WARNING Low embedding diversity, potential mode collapse'}
{'- PASS Reproducible embeddings' if results.embedding_quality.get('reproducibility', 0) > 0.9 else '- WARNING Embedding reproducibility issues'}
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

def main():
    parser = argparse.ArgumentParser(description="Benchmark JSON Embedding Model")
    parser.add_argument("--data-dir", default="data/", help="Directory containing JSONL files")
    parser.add_argument("--output-dir", default="benchmarks/", help="Output directory for results")
    parser.add_argument("--model", help="Path to model checkpoint (auto-downloads if not provided)")
    parser.add_argument("--config", help="Path to config YAML")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch size for embeddings")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmark with smaller samples")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Find JSONL files
    data_dir = Path(args.data_dir)
    datasets = {}
    for jsonl_file in data_dir.glob("*.jsonl"):
        dataset_name = jsonl_file.stem
        datasets[dataset_name] = str(jsonl_file)
    
    if not datasets:
        print(f"ERROR No JSONL files found in {data_dir}")
        return
    
    print(f"INFO Found datasets: {list(datasets.keys())}")
    
    # Initialize benchmark
    benchmark = EmbeddingBenchmark(
        model_path=args.model,
        config_path=args.config,
        batch_size=args.batch_size
    )
    
    # Run benchmarks
    results = benchmark.run_full_benchmark(datasets)
    
    # Save results
    os.makedirs(args.output_dir, exist_ok=True)
    
    # JSON results
    json_path = os.path.join(args.output_dir, "benchmark_results.json")
    benchmark.save_results(results, json_path)
    
    # Human-readable report
    report_path = os.path.join(args.output_dir, "benchmark_report.md")
    generate_benchmark_report(results, report_path)
    
    print(f"PASS Benchmark complete!")
    print(f"Results: {json_path}")
    print(f"Report: {report_path}")

if __name__ == "__main__":
    main()
