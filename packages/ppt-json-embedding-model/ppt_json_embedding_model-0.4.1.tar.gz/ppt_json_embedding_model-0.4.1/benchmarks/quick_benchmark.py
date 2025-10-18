#!/usr/bin/env python3
"""
Quick Benchmark Script for JSON Embedding Model

A simplified version for rapid testing and development.
"""

import sys
import os
import time
import json
import numpy as np
from pathlib import Path

# Add the project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def quick_embedding_test():
    """Quick test of embedding generation"""
    print("Quick Embedding Test")
    
    try:
        # Check if package is installed, otherwise use direct path
        try:
            from embedding_model.cli.embed import main as embed_main
            from embedding_model.cli.search import main as search_main
        except ImportError:
            # Try direct import from src
            from src.embedding_model.cli.embed import main as embed_main
            from src.embedding_model.cli.search import main as search_main
        
        # Test data
        test_records = [
            {"id": 1, "type": "device", "name": "Server ABC-123", "status": "active"},
            {"id": 2, "type": "ticket", "description": "Network connectivity issue", "priority": "high"},
            {"id": 3, "type": "customer", "name": "Acme Corp", "industry": "technology"}
        ]
        
        # Create test file
        test_file = "test_data.jsonl"
        with open(test_file, 'w') as f:
            for record in test_records:
                f.write(json.dumps(record) + '\n')
        
        print(f"Created test file: {test_file}")
        
        # Test embedding generation
        print("Testing embedding generation...")
        start_time = time.time()
        
        # Simulate CLI call
        import sys
        original_argv = sys.argv.copy()
        sys.argv = ['embed', '--input', test_file, '--output', 'test_embeddings.npy', '--batch-size', '32']
        
        try:
            embed_main()
            embed_time = time.time() - start_time
            print(f"PASS Embeddings generated in {embed_time:.2f}s")
            
            # Check output
            embeddings = np.load('test_embeddings.npy')
            print(f"Embedding shape: {embeddings.shape}")
            print(f"Mean embedding norm: {np.mean(np.linalg.norm(embeddings, axis=1)):.3f}")
            
        except Exception as e:
            print(f"ERROR Embedding generation failed: {e}")
        finally:
            sys.argv = original_argv
        
        # Test search
        if os.path.exists('test_embeddings.npy'):
            print("Testing search...")
            sys.argv = ['search', '--pairs', f'{test_file}=test_embeddings.npy', '--query', 'network problem', '--topk', '2']
            
            try:
                search_main()
                print("PASS Search completed successfully")
            except Exception as e:
                print(f"ERROR Search failed: {e}")
            finally:
                sys.argv = original_argv
        
        # Cleanup
        for temp_file in [test_file, 'test_embeddings.npy']:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        print("Cleaned up test files")
        
    except ImportError as e:
        print(f"ERROR Import error: {e}")
        print("Make sure you're running from the project root directory")

def performance_test():
    """Test embedding performance with actual data"""
    print("\nPerformance Test")
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("ERROR Data directory not found")
        return
    
    jsonl_files = list(data_dir.glob("*.jsonl"))
    if not jsonl_files:
        print("ERROR No JSONL files found in data/")
        return
    
    # Test with first available file
    test_file = jsonl_files[0]
    print(f"Testing with: {test_file}")
    
    # Count records
    with open(test_file, 'r', encoding='utf-8') as f:
        record_count = sum(1 for line in f if line.strip())
    
    print(f"Records: {record_count}")
    
    # Test different batch sizes
    batch_sizes = [32, 128, 256]
    
    for batch_size in batch_sizes:
        print(f"\nTesting batch size: {batch_size}")
        
        output_file = f"perf_test_{batch_size}.npy"
        
        try:
            import sys
            original_argv = sys.argv.copy()
            sys.argv = ['embed', '--input', str(test_file), '--output', output_file, 
                       '--batch-size', str(batch_size), '--limit', '1000']
            
            start_time = time.time()
            
            from src.embedding_model.cli.embed import main as embed_main
            embed_main()
            
            elapsed = time.time() - start_time
            embeddings_per_sec = min(1000, record_count) / elapsed
            
            print(f"Time: {elapsed:.2f}s")
            print(f"Speed: {embeddings_per_sec:.1f} embeddings/sec")
            
            # Cleanup
            if os.path.exists(output_file):
                os.remove(output_file)
                
        except Exception as e:
            print(f"ERROR Failed: {e}")
        finally:
            sys.argv = original_argv

def memory_test():
    """Test memory usage"""
    print("\nMemory Usage Test")
    
    try:
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"Initial memory: {initial_memory:.1f} MB")
        
        # Load model
        try:
            from embedding_model.download import get_default_model_path
            from embedding_model.config import load_config
            from embedding_model.tokenizer import CharVocab
            from embedding_model.model.charcnn import CharCNNEncoder
        except ImportError:
            from src.embedding_model.download import get_default_model_path
            from src.embedding_model.config import load_config
            from src.embedding_model.tokenizer import CharVocab
            from src.embedding_model.model.charcnn import CharCNNEncoder
        import torch
        
        model_path = str(get_default_model_path())
        ckpt = torch.load(model_path, map_location="cpu")
        
        after_load_memory = process.memory_info().rss / 1024 / 1024
        print(f"After model load: {after_load_memory:.1f} MB (+{after_load_memory - initial_memory:.1f} MB)")
        
        # Test embedding generation
        itos = ckpt["vocab"]
        vocab = CharVocab(stoi={ch: i for i, ch in enumerate(itos)}, itos=itos, unk_token="?")
        
        model = CharCNNEncoder(
            vocab_size=len(vocab.itos),
            embedding_dim=32,
            conv_channels=256,
            kernel_sizes=[3, 5, 7],
            projection_dim=256,
            layer_norm=True,
        )
        model.load_state_dict(ckpt["model"])
        model.eval()
        
        after_init_memory = process.memory_info().rss / 1024 / 1024
        print(f"After model init: {after_init_memory:.1f} MB (+{after_init_memory - after_load_memory:.1f} MB)")
        
        # Generate test embeddings
        try:
            from embedding_model.datasets.collate import make_char_collate
        except ImportError:
            from src.embedding_model.datasets.collate import make_char_collate
        collate = make_char_collate(vocab, 2048)
        
        test_texts = ["Sample text for memory testing"] * 1000
        
        with torch.no_grad():
            ids, mask = collate(test_texts)
            embeddings = model(ids, mask)
        
        after_embedding_memory = process.memory_info().rss / 1024 / 1024
        print(f"After embeddings: {after_embedding_memory:.1f} MB (+{after_embedding_memory - after_init_memory:.1f} MB)")
        
        print(f"\nTotal memory usage: {after_embedding_memory - initial_memory:.1f} MB")
        
    except ImportError:
        print("ERROR psutil not available for memory testing")
    except Exception as e:
        print(f"ERROR Memory test failed: {e}")

def main():
    print("JSON Embedding Model - Quick Benchmark")
    print("=" * 50)
    
    # Run quick tests
    quick_embedding_test()
    performance_test()
    memory_test()
    
    print("\nPASS Quick benchmark complete!")
    print("\nFor comprehensive benchmarking, run:")
    print("   python benchmark_embedding_model.py --data-dir data/ --output-dir benchmarks/")

if __name__ == "__main__":
    main()
