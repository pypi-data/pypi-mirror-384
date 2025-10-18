# Training Guide: JSON Embedding Model

## **Important: Training Required**

This is an **open-weight model** - we provide the architecture and training code, but **no pre-trained weights**. You must train the model on your own JSON data.

## Why No Pre-trained Weights?

- **Privacy**: Pre-trained weights can leak information about training data
- **Domain Specificity**: Your JSON schema is unique to your use case
- **Security**: Prevents reverse-engineering of proprietary data structures
- **Customization**: Model learns your specific field names, values, and patterns

## Quick Start

### 1. Prepare Your Data

Create a JSONL file (one JSON object per line):

```jsonl
{"id": "1", "title": "Product A", "description": "High-quality widget", "category": "electronics"}
{"id": "2", "title": "Service B", "description": "Professional installation", "category": "services"}
{"id": "3", "title": "Product C", "description": "Budget-friendly option", "category": "electronics"}
```

**Minimum Requirements:**
- 1,000+ JSON records (more is better)
- Consistent JSON structure
- Text-rich fields for meaningful embeddings

### 2. Train Your Model

```bash
# Basic training
python -m embedding_model.cli.train your_data.jsonl --output my_model.pt

# Advanced training with custom config
python -m embedding_model.cli.train your_data.jsonl \
  --output my_model.pt \
  --epochs 15 \
  --batch-size 64 \
  --config config/default.yaml
```

### 3. Test Your Model

```bash
# Search your data
python -m embedding_model.cli.search \
  --model my_model.pt \
  --data your_data.jsonl \
  --query "high quality electronics" \
  --topk 5
```

## Training Tips

### Data Quality
- **More data = better performance**: 10,000+ records ideal
- **Diverse content**: Include variety of field values and structures
- **Clean data**: Remove duplicates and corrupted records
- **Representative**: Training data should match your search use cases

### Training Parameters
- **Epochs**: Start with 10, increase if loss is still decreasing
- **Batch size**: 32-128 depending on your GPU memory
- **Learning rate**: Default 3e-4 works well, try 1e-4 for fine-tuning

### Monitoring Training
```bash
# Training will output loss every 50 steps
# Look for decreasing contrastive loss
# Typical good final loss: 0.1-0.5
```

## Advanced Usage

### Custom Configuration

Create your own config file:

```yaml
# my_config.yaml
seed: 42
max_chars: 2048
epochs: 20
batch_size: 64
lr: 1e-4
temperature: 0.05  # Lower = more focused similarities
```

```bash
python -m embedding_model.cli.train your_data.jsonl \
  --config my_config.yaml \
  --output my_model.pt
```

### Data Augmentation

The model automatically applies augmentation during training:
- **Field dropping**: Randomly removes fields to improve robustness
- **Field shuffling**: Changes field order to prevent position bias
- **Digit masking**: Masks some digits to improve generalization

## Evaluation

### Manual Testing
```bash
# Test search quality
python -m embedding_model.cli.search \
  --model my_model.pt \
  --data your_data.jsonl \
  --query "test query" \
  --topk 10 \
  --explain  # Shows why results were selected
```

### Systematic Evaluation
1. **Hold out test set**: Keep 10-20% of data for testing
2. **Query relevance**: Create test queries with known relevant results
3. **Recall@K**: Measure how often relevant results appear in top K
4. **A/B testing**: Compare against baseline search (BM25, exact match)

## Troubleshooting

### Poor Search Quality
- **More training data**: Add more diverse examples
- **Longer training**: Increase epochs if loss still decreasing
- **Check data quality**: Remove duplicates, fix JSON formatting
- **Adjust temperature**: Lower values (0.05) for more focused similarities

### Training Issues
- **Out of memory**: Reduce batch size or max_chars
- **Slow training**: Use GPU if available, reduce data size for testing
- **Loss not decreasing**: Check data quality, try different learning rate

### Model Size
- **Too large**: Reduce conv_channels or projection_dim in config
- **Too small**: Increase parameters, but ensure you have enough training data

## Production Deployment

### Model Serving
```bash
# Generate embeddings for your entire dataset
python -m embedding_model.cli.embed \
  --model my_model.pt \
  --input production_data.jsonl \
  --output production_embeddings.npy

# Use embeddings with vector database (Pinecone, Weaviate, etc.)
```

### Retraining
- **Retrain periodically** as your data evolves
- **Incremental updates**: Add new data and retrain
- **A/B test** new model versions before deployment

## Security Considerations

### Data Privacy
- **Training data stays local**: Never uploaded anywhere
- **Model weights contain patterns**: Don't share trained models publicly
- **Embeddings are compressed**: But may still contain some information

### Best Practices
- **Separate environments**: Train on secure infrastructure
- **Access control**: Limit who can access trained models
- **Data governance**: Follow your organization's data handling policies

## Need Help?

- **Check issues**: Look for similar problems in GitHub issues
- **Documentation**: Read the full model card and API docs
- **Community**: Join discussions in GitHub Discussions

Remember: The model learns from YOUR data, so performance depends entirely on your training dataset quality and size!
