#!/usr/bin/env python3
"""
Example: Using the JSON Embedding Model Python API

This example shows how to use the high-level Python API for embedding
and searching JSON documents in your applications.
"""

import os
from embedding_model import JSONEmbeddingModel, search_documents

# Sample documents
documents = [
    {
        "id": "1",
        "title": "MacBook Pro 16-inch",
        "category": "laptops",
        "brand": "Apple",
        "price": 2399,
        "description": "Powerful laptop with M2 Pro chip, great for development and creative work"
    },
    {
        "id": "2", 
        "title": "Dell XPS 13",
        "category": "laptops",
        "brand": "Dell",
        "price": 1299,
        "description": "Compact ultrabook with excellent build quality and long battery life"
    },
    {
        "id": "3",
        "title": "iPad Pro 12.9",
        "category": "tablets",
        "brand": "Apple", 
        "price": 1099,
        "description": "Professional tablet with Apple Pencil support, perfect for digital art"
    },
    {
        "id": "4",
        "title": "Gaming Desktop PC",
        "category": "desktops",
        "brand": "Custom",
        "price": 1899,
        "description": "High-performance gaming computer with RTX 4070 and 32GB RAM"
    }
]


def example_with_model_instance():
    """Example using a model instance (recommended for multiple operations)"""
    print("=== Example 1: Using Model Instance ===")
    
    # Initialize model (set your model path)
    model_path = os.environ.get("JSON_EMBED_MODEL_PATH", "path/to/your/model.pt")
    model = JSONEmbeddingModel(model_path)
    
    # Generate embeddings for all documents
    print("Generating embeddings...")
    embeddings = model.embed_documents(documents)
    print(f"Generated embeddings shape: {embeddings.shape}")
    
    # Search for laptops
    print("\nSearching for 'powerful laptop for development'...")
    results = model.search(
        query="powerful laptop for development",
        documents=documents,
        embeddings=embeddings,  # Reuse pre-computed embeddings
        top_k=3
    )
    
    for similarity, idx, doc in results:
        print(f"  Score: {similarity:.3f} | {doc['title']} - {doc['description'][:50]}...")
    
    # Search with filters
    print("\nSearching for Apple products...")
    results = model.search(
        query="creative work device",
        documents=documents,
        embeddings=embeddings,
        top_k=3,
        filters={"brand": "Apple"}  # Only Apple products
    )
    
    for similarity, idx, doc in results:
        print(f"  Score: {similarity:.3f} | {doc['title']} ({doc['brand']})")


def example_with_convenience_functions():
    """Example using convenience functions (good for one-off operations)"""
    print("\n=== Example 2: Using Convenience Functions ===")
    
    # Quick search without managing model instance
    model_path = os.environ.get("JSON_EMBED_MODEL_PATH", "path/to/your/model.pt")
    
    print("Searching for 'gaming computer'...")
    results = search_documents(
        query="gaming computer",
        documents=documents,
        model_path=model_path,
        top_k=2
    )
    
    for similarity, idx, doc in results:
        print(f"  Score: {similarity:.3f} | {doc['title']} - ${doc['price']}")


def example_embed_single_document():
    """Example of embedding individual documents"""
    print("\n=== Example 3: Embedding Individual Documents ===")
    
    model_path = os.environ.get("JSON_EMBED_MODEL_PATH", "path/to/your/model.pt")
    model = JSONEmbeddingModel(model_path)
    
    # Embed a single document
    new_doc = {
        "title": "Surface Laptop Studio",
        "category": "laptops", 
        "brand": "Microsoft",
        "description": "Innovative laptop with flexible screen for creative professionals"
    }
    
    embedding = model.embed_json_object(new_doc)
    print(f"Single document embedding shape: {embedding.shape}")
    
    # You can also embed raw text
    text_embedding = model.embed_text("high-performance laptop for gaming")
    print(f"Text embedding shape: {text_embedding.shape}")


if __name__ == "__main__":
    # Set your model path as environment variable:
    # export JSON_EMBED_MODEL_PATH="/path/to/your/model.pt"
    
    try:
        example_with_model_instance()
        example_with_convenience_functions()
        example_embed_single_document()
        
        print("\nAll examples completed successfully!")
        print("\nTips:")
        print("- Use model instances for multiple operations (more efficient)")
        print("- Pre-compute embeddings when searching the same documents repeatedly")
        print("- Use filters to narrow search results before semantic matching")
        print("- Batch processing is automatically handled for better performance")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Set JSON_EMBED_MODEL_PATH environment variable")
        print("2. Have a trained model checkpoint (.pt file)")
        print("3. Install the package: pip install ppt-json-embedding-model")
