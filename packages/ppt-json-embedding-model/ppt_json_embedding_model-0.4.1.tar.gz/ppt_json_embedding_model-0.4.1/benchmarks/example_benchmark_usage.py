#!/usr/bin/env python3
"""
Example Usage of JSON Embedding Model Benchmarking

This script demonstrates how to use the benchmarking tools
for different scenarios and use cases.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def example_1_quick_test():
    """Example 1: Quick functionality test"""
    print("=" * 60)
    print("Example 1: Quick Functionality Test")
    print("=" * 60)
    
    print("Use this for rapid development and debugging")
    print()
    
    # Command to run
    cmd = "python quick_benchmark.py"
    print(f"Command: {cmd}")
    print()
    
    print("Expected output:")
    print("- PASS Embedding generation test")
    print("- Performance metrics (embeddings/sec)")
    print("- Search functionality test")
    print("- Memory usage analysis")
    print()

def example_2_comprehensive_benchmark():
    """Example 2: Full benchmark suite"""
    print("=" * 60)
    print("Example 2: Comprehensive Benchmark Suite")
    print("=" * 60)
    
    print("Use this for thorough model evaluation")
    print()
    
    cmd = """python benchmark_embedding_model.py \\
    --data-dir data/ \\
    --output-dir benchmarks/ \\
    --batch-size 256"""
    
    print(f"Command:")
    print(cmd)
    print()
    
    print("Outputs:")
    print("- benchmarks/benchmark_results.json (detailed metrics)")
    print("- benchmarks/benchmark_report.md (human-readable)")
    print()
    
    print("Test Categories:")
    print("- Embedding Quality (reproducibility, diversity)")
    print("- Search Relevance (MRR, precision@K)")
    print("- Performance (speed, memory)")
    print("- Cross-Domain Analysis")
    print()

def example_3_performance_optimization():
    """Example 3: Performance optimization workflow"""
    print("=" * 60)
    print("Example 3: Performance Optimization")
    print("=" * 60)
    
    print("Use this to optimize batch sizes and settings")
    print()
    
    batch_sizes = [64, 128, 256, 512]
    
    print("Test different batch sizes:")
    for batch_size in batch_sizes:
        cmd = f"python benchmark_embedding_model.py --batch-size {batch_size} --quick"
        print(f"  {cmd}")
    
    print()
    print("Compare results to find optimal batch size")
    print("- Higher batch size = faster throughput")
    print("- Lower batch size = less memory usage")
    print()

def example_4_search_quality_analysis():
    """Example 4: Search quality analysis"""
    print("=" * 60)
    print("Example 4: Search Quality Analysis")
    print("=" * 60)
    
    print("Test search quality with real queries")
    print()
    
    # Example queries for different domains
    test_queries = {
        "Hardware Issues": [
            "server hardware failure",
            "network switch malfunction",
            "storage device error"
        ],
        "Software Problems": [
            "application crash",
            "database connection timeout",
            "authentication failure"
        ],
        "Network Issues": [
            "network connectivity problem",
            "DNS resolution failure",
            "bandwidth limitation"
        ]
    }
    
    print("Example test queries by domain:")
    for domain, queries in test_queries.items():
        print(f"\n{domain}:")
        for query in queries:
            print(f"  - {query}")
    
    print()
    print("Manual testing commands:")
    print("""
# Generate embeddings for all datasets
json-embed --input data/qa-tickets_from_xlsx.fixed.jsonl --output tickets.npy
json-embed --input data/qa-assets_from_xlsx.fixed.jsonl --output assets.npy
json-embed --input data/qa-customers_from_xlsx.fixed.jsonl --output customers.npy

# Test search with specific queries
json-embed-search \\
  --pairs data/qa-tickets_from_xlsx.fixed.jsonl=tickets.npy \\
  --query "server hardware failure" \\
  --topk 10

# Cross-domain search
json-embed-search \\
  --pairs data/qa-tickets_from_xlsx.fixed.jsonl=tickets.npy data/qa-assets_from_xlsx.fixed.jsonl=assets.npy \\
  --query "network device configuration" \\
  --topk 10
""")

def example_5_regression_testing():
    """Example 5: Regression testing workflow"""
    print("=" * 60)
    print("Example 5: Regression Testing")
    print("=" * 60)
    
    print("Use this to detect performance regressions")
    print()
    
    workflow = """
# 1. Run baseline benchmark
python benchmark_embedding_model.py --output-dir benchmarks/baseline/

# 2. Make model changes (training, architecture, etc.)

# 3. Run new benchmark  
python benchmark_embedding_model.py --output-dir benchmarks/current/

# 4. Compare results
python -c "
import json

# Load results
with open('benchmarks/baseline/benchmark_results.json') as f:
    baseline = json.load(f)
with open('benchmarks/current/benchmark_results.json') as f:
    current = json.load(f)

# Compare key metrics
metrics = [
    ('search_metrics', 'mean_reciprocal_rank'),
    ('search_metrics', 'precision_at_5'),
    ('performance_metrics', 'embeddings_per_second'),
    ('embedding_quality', 'embedding_diversity')
]

print('Regression Analysis:')
for category, metric in metrics:
    baseline_val = baseline[category][metric]
    current_val = current[category][metric]
    change = (current_val - baseline_val) / baseline_val * 100
    
    status = 'PASS' if change >= -5 else 'FAIL'  # 5% regression threshold
    print(f'{status} {metric}: {baseline_val:.3f} -> {current_val:.3f} ({change:+.1f}%)')
"
"""
    
    print("Workflow:")
    print(workflow)

def example_6_custom_evaluation():
    """Example 6: Custom evaluation scenarios"""
    print("=" * 60)
    print("Example 6: Custom Evaluation")
    print("=" * 60)
    
    print("Create domain-specific evaluation tests")
    print()
    
    custom_code = '''
from benchmark_embedding_model import EmbeddingBenchmark
import numpy as np

# Initialize benchmark
benchmark = EmbeddingBenchmark()

# Load your specific dataset
records, texts = benchmark.load_dataset("data/qa-tickets_from_xlsx.fixed.jsonl", limit=500)
embeddings = benchmark.generate_embeddings(texts)

# Custom test: Ticket severity clustering
severity_groups = {}
for i, record in enumerate(records):
    severity = record.get('Priority', 'Unknown')
    if severity not in severity_groups:
        severity_groups[severity] = []
    severity_groups[severity].append(i)

# Analyze clustering quality
print("Severity Clustering Analysis:")
for severity, indices in severity_groups.items():
    if len(indices) > 1:
        group_embeddings = embeddings[indices]
        # Calculate intra-group similarity
        similarities = np.dot(group_embeddings, group_embeddings.T)
        avg_similarity = np.mean(similarities[np.triu_indices_from(similarities, k=1)])
        print(f"  {severity}: {avg_similarity:.3f} avg similarity")

# Custom test: Find similar tickets
def find_similar_tickets(query_text, top_k=5):
    query_emb = benchmark.generate_embeddings([query_text])[0]
    similarities = np.dot(embeddings, query_emb)
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    print(f"\\nSimilar tickets to: '{query_text}'")
    for i, idx in enumerate(top_indices, 1):
        score = similarities[idx]
        ticket_id = records[idx].get('Id', 'Unknown')
        print(f"  {i}. {score:.3f} - Ticket {ticket_id}")

# Example usage
find_similar_tickets("network connectivity issue")
find_similar_tickets("server hardware failure")
'''
    
    print("Example custom evaluation:")
    print(custom_code)

def main():
    """Main function to run all examples"""
    print("JSON Embedding Model - Benchmark Examples")
    print("=" * 80)
    print()
    
    examples = [
        example_1_quick_test,
        example_2_comprehensive_benchmark,
        example_3_performance_optimization,
        example_4_search_quality_analysis,
        example_5_regression_testing,
        example_6_custom_evaluation
    ]
    
    for i, example_func in enumerate(examples, 1):
        example_func()
        if i < len(examples):
            print("\n" + "=" * 60 + "\n")
    
    print("=" * 80)
    print("PASS All examples shown!")
    print()
    print("Next steps:")
    print("1. Run: python quick_benchmark.py")
    print("2. Run: python benchmark_embedding_model.py --data-dir data/ --output-dir benchmarks/")
    print("3. Review: benchmarks/benchmark_report.md")
    print("4. Check: BENCHMARKING.md for detailed guidance")

if __name__ == "__main__":
    main()
