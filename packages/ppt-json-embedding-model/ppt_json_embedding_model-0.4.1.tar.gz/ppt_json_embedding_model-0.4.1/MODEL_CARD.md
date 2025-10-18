# Model Card: JSON Embedding Model

## Model Details

**Model Name**: JSON Embedding Model  
**Version**: 0.3.0 
**Model Type**: Character-level CNN Encoder with Contrastive Learning  
**Architecture**: CharCNN + Projection Head  
**Training Objective**: NT-Xent (InfoNCE) Contrastive Loss  
**Embedding Dimension**: 256  
**Model Size**: ~1.2MB (when trained)  
**License**: MIT License  
**Distribution**: **Open-Weight Architecture** - Training code provided, no pre-trained weights included  

## Intended Use

### **Training Required**
This is an **open-weight model architecture** - you must train it on your own data. No pre-trained weights are provided.

### Primary Use Cases
- **Vector Search**: Generate embeddings for JSON records for similarity search
- **Semantic Retrieval**: Find relevant records based on text queries
- **Data Clustering**: Group similar JSON records for analysis
- **Anomaly Detection**: Identify unusual patterns in structured data

### Intended Users
- Developers working with JSON data search and retrieval
- Data scientists building semantic search systems
- Researchers exploring embedding models for structured data
- Organizations with proprietary JSON datasets who need custom embeddings

## Model Architecture

```
Input: JSON Text (flattened) → Character Tokenizer → Character Embeddings (32-dim)
         ↓
Multi-Kernel 1D CNN (kernels: 3,5,7) → Global Max Pooling (256 channels each)
         ↓
Projection Head (Linear + LayerNorm) → 256-dim Embedding Vector (L2 normalized)
```

**Key Components**:
- **Character Vocabulary**: Dynamic vocabulary built from training data
- **Character Embedding Dimension**: 32 per character
- **CNN Channels**: 256 channels for kernels [3, 5, 7]
- **Max Sequence Length**: 2048 characters
- **Final Embedding Dimension**: 256 (L2 normalized)

## Training Data Requirements

### **You Must Provide Your Own Training Data**
This model architecture requires training on your specific JSON dataset. No training data or pre-trained weights are included.

### Recommended Data Format
Train the model on JSON records from your domain, such as:
- Service tickets with descriptions and solutions
- Product catalogs with specifications
- Customer records with metadata
- Device configurations and logs
- Any structured JSON data you want to search

### Data Preprocessing (Automatic)
The training pipeline automatically handles:
- JSON objects flattened to text using `key=value` format
- Field pairs separated by ` | ` delimiter
- Text truncated to 2048 characters maximum
- Character-level tokenization

### Built-in Data Augmentation
- **Field Dropping**: Randomly remove 10-30% of JSON fields
- **Field Shuffling**: Randomize order of key-value pairs
- **Digit Masking**: Replace digits with `[DIGIT]` token (configurable probability)

### Minimum Training Recommendations
- **Minimum Samples**: ~1,000 JSON records (more is better)
- **Recommended**: 5,000+ records for good performance
- **Optimal**: 10,000+ records for best results
- **Training Time**: 10-50 epochs depending on data size

## Performance

### Training Metrics
- **Final Loss**: Converged contrastive loss (NT-Xent)
- **Temperature**: 0.1
- **Learning Rate**: 1e-3 with linear warmup

### Evaluation
**Note**: Performance dependent on training data quality and domain. 

**Recommended Evaluation After Training**:
- Implement retrieval recall@k on labeled query-document pairs from your domain
- Manual inspection of nearest neighbors for semantic quality
- Compare against baseline search methods (BM25, TF-IDF) on your specific data
- A/B test search relevance with your users

## Limitations

### Technical Limitations
- **Character-level only**: No word or subword understanding
- **Limited context**: 2048 character maximum input length
- **No fine-tuning**: Trained from scratch, not based on pre-trained models
- **Domain-specific**: Optimized for JSON data with key-value structure

### Data Limitations
- **Training data dependent**: Performance entirely dependent on your training data quality
- **Domain-specific**: Model may be biased toward your specific JSON schema and content
- **No pre-training**: Starts from scratch, no general knowledge transfer
- **Cold start problem**: Requires sufficient training data to be effective

### Use Case Limitations
- **Not suitable for**: General-purpose text understanding, long documents, non-JSON data
- **Requires JSON structure**: Designed for structured key-value data
- **Research/experimental**: Not validated for production-critical applications

## Ethical Considerations

### Bias
- **Representation bias**: May reflect patterns in training data domains
- **Domain bias**: May perform better on certain types of JSON structures
- **Language bias**: Optimized for English text content

### Responsible Use
- **Human oversight**: Recommendations should be reviewed by domain experts
- **Monitoring**: Track model performance and potential degradation over time
- **Validation**: Test thoroughly on your specific use case before deployment

## Technical Specifications

### Input Format
```json
{
  "key1": "value1",
  "key2": "value2", 
  "nested": {"subkey": "subvalue"}
}
```
*Flattened to*: `key1=value1 | key2=value2 | nested_subkey=subvalue`

### Output Format
- **Shape**: (batch_size, 256)
- **Type**: float32 NumPy array or PyTorch tensor
- **Range**: Normalized embeddings (typically [-1, 1])

## Usage Examples

### 1. Train Your Model (Required First Step)
```bash
# Train on your JSON data
python -m embedding_model.cli.train your_data.jsonl \
  --epochs 10 \
  --output my_model.pt \
  --config config/default.yaml

# Monitor training progress
# Model will be saved to my_model.pt when complete
```

### 2. Generate Embeddings (After Training)
```bash
# Generate embeddings using your trained model
python -m embedding_model.cli.embed \
  --model my_model.pt \
  --input new_data.jsonl \
  --output embeddings.npy
```

### 3. Search Your Data (After Training)
```bash
# Search using your trained model
python -m embedding_model.cli.search \
  --model my_model.pt \
  --data your_data.jsonl \
  --query "your search query" \
  --topk 10
```

### 4. Adaptive Search (Works with Any JSON Schema)
```bash
# Automatically adapts to your JSON structure
python -m embedding_model.cli.adaptive_search \
  --model my_model.pt \
  --data your_data.jsonl \
  --query "search query" \
  --analyze  # Shows detected schema
```

## Installation & Getting Started

### Install the Package
```bash
pip install ppt-json-embedding-model
```

Or from source:
```bash
git clone https://github.com/ParkPlaceTech/json-embedding-model
cd json-embedding-model
pip install -e .
```

### Quick Start Training Guide

1. **Prepare Your Data**: Create a JSONL file with your JSON records
   ```bash
   # your_data.jsonl - one JSON object per line
   {"id": "1", "title": "Example", "description": "Sample record"}
   {"id": "2", "title": "Another", "description": "Another sample"}
   ```

2. **Train Your Model**: 
   ```bash
   python -m embedding_model.cli.train your_data.jsonl --output my_model.pt
   ```

3. **Test Your Model**:
   ```bash
   python -m embedding_model.cli.search --model my_model.pt --data your_data.jsonl --query "sample"
   ```

### ⚠️ **Important**: No Pre-trained Weights
This is an open-weight architecture. You **must train** the model on your data before use.

## Version History

### v0.3.0
- **Open-weight release**: Training architecture and code provided
- Character-level CNN with contrastive learning
- 256-dimensional embeddings
- Support for custom JSON data training and search
- **No pre-trained weights included** - train on your own data

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## References

- **NT-Xent Loss**: [A Simple Framework for Contrastive Learning of Visual Representations](https://arxiv.org/abs/2002.05709)
- **Character-level CNNs**: [Character-level Convolutional Networks for Text Classification](https://arxiv.org/abs/1509.01626)
- **Model Cards**: [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
