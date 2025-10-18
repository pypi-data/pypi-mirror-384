#!/usr/bin/env python3
"""
Quick test of the new Python API
"""

import os

# Test documents
test_docs = [
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
    }
]

def test_imports():
    """Test that we can import the new API"""
    print("=== Testing Imports ===")
    
    try:
        from embedding_model import JSONEmbeddingModel, search_documents, embed_documents
        print("Successfully imported JSONEmbeddingModel and convenience functions")
        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False

def test_model_initialization():
    """Test model initialization"""
    print("\n=== Testing Model Initialization ===")
    
    try:
        from embedding_model import JSONEmbeddingModel
        
        # Use environment variable or your model path
        model_path = os.environ.get("JSON_EMBED_MODEL_PATH", 
                                   r"C:\Users\vmoberg\source\repos\embedding-model\runs\exp1\last.pt")
        
        print(f"Attempting to load model from: {model_path}")
        model = JSONEmbeddingModel(model_path)
        print("Model initialized successfully")
        return model
        
    except Exception as e:
        print(f"Model initialization failed: {e}")
        return None

def test_embedding_single_document(integration_model):
    """Test embedding a single document"""
    print("\n=== Testing Single Document Embedding ===")
    
    try:
        doc = test_docs[0]
        embedding = integration_model.embed_json_object(doc)
        print(f"Single document embedded successfully")
        print(f"   Embedding shape: {embedding.shape}")
        print(f"   Embedding type: {type(embedding)}")
        return True
    except Exception as e:
        print(f"Single document embedding failed: {e}")
        return False

def test_embedding_multiple_documents(integration_model):
    """Test embedding multiple documents"""
    print("\n=== Testing Multiple Document Embedding ===")
    
    try:
        embeddings = integration_model.embed_documents(test_docs)
        print(f"Multiple documents embedded successfully")
        print(f"   Embeddings shape: {embeddings.shape}")
        print(f"   Expected shape: ({len(test_docs)}, embedding_dim)")
        return embeddings
    except Exception as e:
        print(f"Multiple document embedding failed: {e}")
        return None

def test_search_functionality(integration_model, sample_embeddings):
    """Test search functionality"""
    print("\n=== Testing Search Functionality ===")
    
    try:
        # Test basic search
        results = integration_model.search(
            query="powerful laptop for development",
            documents=test_docs,
            embeddings=sample_embeddings,
            top_k=3
        )
        
        print(f"Search completed successfully")
        print(f"   Found {len(results)} results")
        
        for i, (similarity, idx, doc) in enumerate(results):
            print(f"   {i+1}. Score: {similarity:.3f} | {doc['title']} ({doc['brand']})")
        
        return True
    except Exception as e:
        print(f"Search failed: {e}")
        return False

def test_search_with_filters(integration_model, sample_embeddings):
    """Test search with filters"""
    print("\n=== Testing Search with Filters ===")
    
    try:
        # Search only Apple products
        results = integration_model.search(
            query="creative work device",
            documents=test_docs,
            embeddings=sample_embeddings,
            top_k=3,
            filters={"brand": "Apple"}
        )
        
        print(f"Filtered search completed successfully")
        print(f"   Found {len(results)} Apple products")
        
        for i, (similarity, idx, doc) in enumerate(results):
            print(f"   {i+1}. Score: {similarity:.3f} | {doc['title']} ({doc['brand']})")
        
        return True
    except Exception as e:
        print(f"Filtered search failed: {e}")
        return False

def test_convenience_functions():
    """Test convenience functions"""
    print("\n=== Testing Convenience Functions ===")
    
    try:
        from embedding_model import search_documents
        
        model_path = os.environ.get("JSON_EMBED_MODEL_PATH", 
                                   r"C:\Users\vmoberg\source\repos\embedding-model\runs\exp1\last.pt")
        
        results = search_documents(
            query="affordable laptop",
            documents=test_docs,
            model_path=model_path,
            top_k=2
        )
        
        print(f"Convenience function search completed successfully")
        print(f"   Found {len(results)} results")
        
        for i, (similarity, idx, doc) in enumerate(results):
            print(f"   {i+1}. Score: {similarity:.3f} | {doc['title']} - ${doc['price']}")
        
        return True
    except Exception as e:
        print(f"Convenience function failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing the new Python API\n")
    
    # Test imports
    if not test_imports():
        print("\nCannot proceed without successful imports")
        return
    
    # Test model initialization
    model = test_model_initialization()
    if model is None:
        print("\nCannot proceed without model")
        return
    
    # Test single document embedding
    if not test_embedding_single_document(model):
        print("\nSingle document embedding failed")
        return
    
    # Test multiple document embedding
    embeddings = test_embedding_multiple_documents(model)
    if embeddings is None:
        print("\nMultiple document embedding failed")
        return
    
    # Test search
    if not test_search_functionality(model, embeddings):
        print("\nSearch functionality failed")
        return
    
    # Test filtered search
    if not test_search_with_filters(model, embeddings):
        print("\nFiltered search failed")
        return
    
    # Test convenience functions
    if not test_convenience_functions():
        print("\nConvenience functions failed")
        return
    
    print("\nAll tests passed! The Python API is working correctly!")
    print("\nYou can now use the API in your applications:")
    print("   from embedding_model import JSONEmbeddingModel")
    print("   model = JSONEmbeddingModel('path/to/model.pt')")
    print("   results = model.search('query', documents)")

if __name__ == "__main__":
    main()
