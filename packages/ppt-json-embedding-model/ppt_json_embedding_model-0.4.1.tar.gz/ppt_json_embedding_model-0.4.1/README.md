## Custom JSON Embedding Model (from scratch)

A from-scratch character-CNN encoder trained with a contrastive objective to embed JSON records (devices, tickets, customers) into dense vectors for vector stores.

### Features
- Char-level tokenizer (no external models)
- Multi-kernel 1D CNN + max-pooling
- Projection head to target dimension
- NT-Xent (InfoNCE) contrastive training with simple JSON augmentations
- JSON flattening utilities and CLI tools
- Conversation role tokens to structure prompts/responses

**[Model Card](https://github.com/ParkPlaceTech/json-embedding-model/blob/main/MODEL_CARD.md)** - Detailed model documentation, limitations, and usage guidelines

### Installation

```bash
# Install from PyPI (recommended)
pip install ppt-json-embedding-model

# Or install from GitHub
pip install git+https://github.com/ParkPlaceTech/json-embedding-model.git

# For development (editable install)
git clone https://github.com/ParkPlaceTech/json-embedding-model.git
cd json-embedding-model
pip install -e .
```

### Quick Start

**Note:** This package provides the model architecture and training framework. You'll need to train your own model or provide pre-trained weights.

```bash
# Train a model on your data
json-embed-train --config config/default.yaml --data your-data.jsonl --out my-model.pt

# Generate embeddings using your trained model
json-embed --model my-model.pt --input your-data.jsonl --output embeddings.npy

# Search with your model
json-embed-search --model my-model.pt --data your-data.jsonl --query "search query" --topk 5
```

### Local Development

```bash
# create venv (recommended)
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -r requirements.txt

# or install as package
pip install -e .

# Train your model
json-embed-train --config config/default.yaml --data your-data.jsonl --out my-model.pt

# Embed using your trained model
json-embed --model my-model.pt --input data/records.jsonl --output embeddings.npy --config config/default.yaml --batch-size 64

# Local search (cosine) across JSONL=NPY pairs
json-embed-search --model my-model.pt --data data/records.jsonl --query "find related records" --topk 5

# Prefilter exact fields before cosine (AND). Example: SerialNumber filter
json-embed-search --model my-model.pt --data data/records.jsonl \
  --where SerialNumber=APM00111003159 --query "Find tickets for this serial" --topk 5
```

### Python API for Applications

For integrating into applications and agents, use the high-level Python API:

```python
from embedding_model import JSONEmbeddingModel

# Initialize model with your trained model path
model = JSONEmbeddingModel("path/to/your/trained-model.pt")

# Embed documents
documents = [
    {"title": "Product A", "description": "High-quality widget", "price": 299},
    {"title": "Service B", "description": "Professional installation", "price": 199}
]
embeddings = model.embed_documents(documents)

# Search documents
results = model.search(
    query="affordable installation service", 
    documents=documents, 
    embeddings=embeddings,
    top_k=5
)

for similarity, idx, doc in results:
    print(f"Score: {similarity:.3f} | {doc['title']}")
```

**Convenience functions for quick usage:**
```python
from embedding_model import search_documents

results = search_documents(
    query="your search query",
    documents=your_json_documents,
    model_path="path/to/your/trained-model.pt",
    top_k=5
)
```

See `examples/python_api_example.py` for complete usage examples.

### Benchmarking

Evaluate model performance with the benchmarking suite:

```bash
# Install benchmark dependencies
pip install -e ".[benchmark]"

# Run quick benchmark
python benchmarks/run_benchmarks.py --type quick

# Run comprehensive benchmark
python benchmarks/run_benchmarks.py --type comprehensive --model-path path/to/model.pt --data-dir data/
```

See the [benchmarks documentation](https://github.com/ParkPlaceTech/json-embedding-model/blob/main/benchmarks/README.md) for detailed benchmarking information.

### Data Format
- JSONL files containing one record per line.
- Records can be any JSON structure; flattening will convert to text.
- Example: `{"title": "Product A", "description": "High-quality widget", "price": 299}`

### Notes
- Steps per epoch ≈ ceil(total_records / batch_size). Use `max_steps` in config to cap.
- CPU-only runs are slower; consider reducing `max_chars`, `batch_size`, or `conv_channels`.
- Use the cleaned `.fixed.jsonl` you trained on when embedding for consistency.

### License
This project is licensed under the MIT License - see the `LICENSE` file for details.
