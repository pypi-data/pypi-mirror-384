# Benchmarking Guide for JSON Embedding Model

This guide provides comprehensive benchmarking tools and instructions for evaluating the JSON embedding model performance across multiple dimensions.

## Quick Start

### Basic Performance Test
```bash
# Quick functional test (5 minutes)
python quick_benchmark.py

# Comprehensive benchmark suite (15-30 minutes)
python benchmark_embedding_model.py --data-dir data/ --output-dir benchmarks/
```

## Benchmark Categories

### 1. Embedding Quality
- **Reproducibility**: Same input produces identical embeddings
- **Diversity**: Embeddings don't collapse to similar values
- **Distribution**: Healthy embedding space characteristics
- **Consistency**: Stable embedding norms and patterns

### 2. Search Relevance
- **Mean Reciprocal Rank (MRR)**: Quality of top-ranked results
- **Precision@K**: Accuracy of top-K retrieved items
- **Cross-domain retrieval**: Performance across different data types
- **Domain-specific matching**: Tickets, devices, customers, accounts

### 3. Performance Metrics
- **Embedding Speed**: Embeddings generated per second
- **Memory Usage**: RAM consumption during operation
- **Batch Efficiency**: Speedup from batch processing
- **Scalability**: Performance with different dataset sizes

### 4. Cross-Domain Analysis
- **Inter-domain similarity**: How similar are different data types
- **Domain separation**: Quality of domain-specific clustering
- **Transfer capability**: Cross-domain search effectiveness

## Usage Examples

### Comprehensive Benchmark
```bash
# Full benchmark with all datasets
python benchmark_embedding_model.py \
  --data-dir data/ \
  --output-dir benchmarks/ \
  --batch-size 256

# Quick benchmark with smaller samples
python benchmark_embedding_model.py \
  --data-dir data/ \
  --output-dir benchmarks/ \
  --quick

# Custom model and config
python benchmark_embedding_model.py \
  --data-dir data/ \
  --output-dir benchmarks/ \
  --model custom_model.pt \
  --config custom_config.yaml
```

### Individual Tests
```bash
# Quick functional verification
python quick_benchmark.py

# Test specific dataset
python -c "
from benchmark_embedding_model import EmbeddingBenchmark
bench = EmbeddingBenchmark()
results = bench.test_performance({'tickets': 'data/qa-tickets_from_xlsx.fixed.jsonl'})
print(results)
"
```

### Manual Testing with CLI Tools
```bash
# Generate embeddings for each dataset
json-embed --input data/qa-tickets_from_xlsx.fixed.jsonl --output tickets.npy --batch-size 256
json-embed --input data/qa-devices_from_xlsx.fixed.jsonl --output devices.npy --batch-size 256

# Test search quality
json-embed-search \
  --pairs data/qa-tickets_from_xlsx.fixed.jsonl=tickets.npy \
  --query "network connectivity issue" \
  --topk 10

# Cross-domain search
json-embed-search \
  --pairs data/qa-tickets_from_xlsx.fixed.jsonl=tickets.npy data/qa-devices_from_xlsx.fixed.jsonl=devices.npy \
  --query "server hardware problem" \
  --topk 10
```

## Understanding Results

### Embedding Quality Metrics

| Metric | Good Range | Description |
|--------|------------|-------------|
| Reproducibility | > 0.99 | Same input gives same output |
| Embedding Diversity (std) | > 0.1 | Embeddings use full space |
| Mean Cosine Similarity | 0.1-0.5 | Not too similar, not random |

### Search Relevance Metrics

| Metric | Good Range | Description |
|--------|------------|-------------|
| Mean Reciprocal Rank | > 0.5 | First relevant result in top 2 |
| Precision@5 | > 0.3 | At least 1-2 relevant in top 5 |

### Performance Metrics

| Metric | Good Performance | Description |
|--------|------------------|-------------|
| Embeddings/Second | > 100 | Processing speed |
| Memory Usage | < 500 MB | Resource efficiency |
| Batch Efficiency | > 5x | Batch vs single speedup |

## Optimization Guidelines

### Poor Embedding Quality
```bash
# Symptoms: Low diversity, high similarity, unstable norms
# Solutions:
# 1. Check training data quality
# 2. Adjust contrastive loss parameters
# 3. Increase embedding dimension
# 4. Review augmentation strategies
```

### Poor Search Relevance
```bash
# Symptoms: Low MRR, poor precision
# Solutions:
# 1. Improve training data labeling
# 2. Add domain-specific augmentations
# 3. Tune model architecture (CNN filters, dims)
# 4. Collect more diverse training examples
```

### Poor Performance
```bash
# Symptoms: Slow embedding, high memory
# Solutions:
# 1. Optimize batch size
# 2. Reduce max sequence length
# 3. Quantize model weights
# 4. Use CPU optimizations
```

## Benchmark Automation

### CI/CD Integration
```yaml
# .github/workflows/benchmark.yml
name: Model Benchmarks
on: [push, pull_request]
jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.10
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run benchmarks
      run: python benchmark_embedding_model.py --quick --data-dir data/ --output-dir results/
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: benchmark-results
        path: results/
```

### Regression Testing
```bash
# Compare with previous results
python -c "
import json
import numpy as np

# Load current and previous results
with open('benchmarks/benchmark_results.json') as f:
    current = json.load(f)
with open('benchmarks/previous_results.json') as f:
    previous = json.load(f)

# Check for regressions
current_mrr = current['search_metrics']['mean_reciprocal_rank']
previous_mrr = previous['search_metrics']['mean_reciprocal_rank']

if current_mrr < previous_mrr * 0.95:  # 5% regression threshold
    print(f'ERROR MRR regression: {current_mrr:.3f} < {previous_mrr:.3f}')
else:
    print(f'PASS MRR maintained: {current_mrr:.3f} >= {previous_mrr:.3f}')
"
```

## Custom Benchmarks

### Adding New Metrics
```python
# Example: Add semantic consistency test
def test_semantic_consistency(self, datasets):
    \"\"\"Test if semantically similar inputs produce similar embeddings\"\"\"
    
    # Define semantic pairs
    semantic_pairs = [
        ("server hardware failure", "hardware server malfunction"),
        ("network connectivity issue", "network connection problem"),
        ("customer account suspended", "account suspension for client")
    ]
    
    results = {}
    similarities = []
    
    for text1, text2 in semantic_pairs:
        emb1 = self.generate_embeddings([text1])[0]
        emb2 = self.generate_embeddings([text2])[0]
        similarity = np.dot(emb1, emb2)
        similarities.append(similarity)
    
    results['mean_semantic_similarity'] = float(np.mean(similarities))
    results['min_semantic_similarity'] = float(np.min(similarities))
    
    return results
```

### Domain-Specific Tests
```python
# Example: Test ticket priority clustering
def test_priority_clustering(self, ticket_records, ticket_embeddings):
    \"\"\"Test if tickets with same priority cluster together\"\"\"
    
    priority_groups = defaultdict(list)
    for i, record in enumerate(ticket_records):
        priority = record.get('Priority', 'Unknown')
        priority_groups[priority].append(i)
    
    # Calculate silhouette-like score for priority clustering
    # ... implementation details ...
    
    return {'priority_clustering_score': score}
```

## References

- **Embedding Quality**: [Embedding Evaluation Best Practices](https://arxiv.org/abs/1802.05365)
- **Search Metrics**: [Information Retrieval Evaluation](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html)
- **Contrastive Learning**: [SimCLR Paper](https://arxiv.org/abs/2002.05709)

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Make sure you're in the project root
cd path/to/embedding-model/
python benchmark_embedding_model.py

# Or install the package
pip install -e .
```

**Memory Errors**
```bash
# Reduce batch size
python benchmark_embedding_model.py --batch-size 64

# Or limit dataset size
python benchmark_embedding_model.py --quick
```

**Model Download Issues**
```bash
# Set GitHub token for private repos
export GITHUB_TOKEN=your_token
python benchmark_embedding_model.py
```

For more help, check the main [README.md](README.md) or open an issue in the repository.
