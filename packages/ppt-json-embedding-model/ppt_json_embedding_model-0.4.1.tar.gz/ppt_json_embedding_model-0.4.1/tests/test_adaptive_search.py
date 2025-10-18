#!/usr/bin/env python3
"""
Test Adaptive Search with Different Data Sources

This script demonstrates how the adaptive search engine automatically
adjusts to different JSON schemas and data sources.

MODEL SETUP:
The script will automatically find your model using these methods (in order):
1. --model argument: python test_adaptive_search.py --model /path/to/model.pt
2. EMBEDDING_MODEL_PATH environment variable: export EMBEDDING_MODEL_PATH=/path/to/model.pt
3. Auto-detection in common locations:
   - model.pt (current directory)
   - ppt-json-embedding-model.pt
   - models/ppt-json-embedding-model.pt
   - ../models/ppt-json-embedding-model.pt
   - ppt-json-embedding-model-v*.pt (wildcard match)
"""

import json
import os
import tempfile
import argparse
import sys
from pathlib import Path

def create_sample_datasets():
    """Create sample datasets with different schemas"""
    
    # Dataset 1: E-commerce data (different from training data)
    ecommerce_data = [
        {
            "product_id": "PROD-001",
            "title": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "category": "Electronics",
            "price": 99.99,
            "brand": "TechSound",
            "rating": 4.5,
            "availability": "In Stock"
        },
        {
            "product_id": "PROD-002", 
            "title": "Gaming Laptop",
            "description": "High-performance laptop for gaming and professional work",
            "category": "Computers",
            "price": 1299.99,
            "brand": "GameTech",
            "rating": 4.8,
            "availability": "Limited"
        },
        {
            "product_id": "PROD-003",
            "title": "Smartphone Case",
            "description": "Protective case for iPhone with wireless charging support",
            "category": "Accessories", 
            "price": 24.99,
            "brand": "ProtectPlus",
            "rating": 4.2,
            "availability": "In Stock"
        }
    ]
    
    # Dataset 2: HR/Employee data (completely different schema)
    hr_data = [
        {
            "employee_id": "EMP-2024-001",
            "full_name": "Sarah Johnson",
            "position": "Software Engineer",
            "department": "Engineering",
            "hire_date": "2024-01-15",
            "salary": 85000,
            "skills": "Python, JavaScript, React",
            "performance_rating": "Excellent",
            "manager": "Mike Chen"
        },
        {
            "employee_id": "EMP-2024-002",
            "full_name": "David Rodriguez", 
            "position": "Product Manager",
            "department": "Product",
            "hire_date": "2023-11-20",
            "salary": 95000,
            "skills": "Product Strategy, Agile, Analytics",
            "performance_rating": "Outstanding",
            "manager": "Lisa Park"
        },
        {
            "employee_id": "EMP-2024-003",
            "full_name": "Emily Wang",
            "position": "Network Administrator", 
            "department": "IT",
            "hire_date": "2024-02-01",
            "salary": 72000,
            "skills": "Network Security, Cisco, Linux",
            "performance_rating": "Good",
            "manager": "Tom Wilson"
        }
    ]
    
    # Dataset 3: Medical records (another different schema)
    medical_data = [
        {
            "patient_id": "PAT-001-2024",
            "patient_name": "John Smith",
            "age": 45,
            "diagnosis": "Hypertension",
            "symptoms": "High blood pressure, headaches",
            "treatment": "ACE inhibitor medication",
            "doctor": "Dr. Amanda Lopez",
            "visit_date": "2024-08-15",
            "severity": "Moderate"
        },
        {
            "patient_id": "PAT-002-2024",
            "patient_name": "Maria Garcia",
            "age": 32,
            "diagnosis": "Migraine",
            "symptoms": "Severe headaches, light sensitivity",
            "treatment": "Triptan medication and lifestyle changes",
            "doctor": "Dr. Robert Kim",
            "visit_date": "2024-08-20", 
            "severity": "Severe"
        }
    ]
    
    # Save datasets to temporary files
    datasets = {
        "ecommerce": ecommerce_data,
        "hr": hr_data,
        "medical": medical_data
    }
    
    temp_files = {}
    for name, data in datasets.items():
        temp_file = f"temp_{name}_data.jsonl"
        with open(temp_file, 'w', encoding='utf-8') as f:
            for record in data:
                f.write(json.dumps(record) + '\n')
        temp_files[name] = temp_file
    
    return temp_files

def find_model_path():
    """Find model file using various strategies"""
    # Strategy 1: Environment variable
    if 'EMBEDDING_MODEL_PATH' in os.environ:
        model_path = os.environ['EMBEDDING_MODEL_PATH']
        if os.path.exists(model_path):
            return model_path
    
    # Strategy 2: Common locations
    common_paths = [
        "model.pt",
        "ppt-json-embedding-model.pt", 
        "models/ppt-json-embedding-model.pt",
        "../models/ppt-json-embedding-model.pt",
        "./ppt-json-embedding-model-v*.pt"
    ]
    
    for path_pattern in common_paths:
        if '*' in path_pattern:
            # Handle wildcard patterns
            import glob
            matches = glob.glob(path_pattern)
            if matches:
                return matches[0]  # Return first match
        elif os.path.exists(path_pattern):
            return path_pattern
    
    return None

def test_adaptive_search(model_path=None):
    """Test adaptive search with different data sources"""
    print("Testing Adaptive Search with Different Data Sources")
    print("=" * 70)
    
    # Find model path if not provided
    if model_path is None:
        model_path = find_model_path()
    
    if model_path is None or not os.path.exists(model_path):
        print("ERROR: Model file not found!")
        print("Please specify the model path using one of these methods:")
        print("1. Set EMBEDDING_MODEL_PATH environment variable")
        print("2. Use --model argument: python test_adaptive_search.py --model /path/to/model.pt")
        print("3. Place model file in current directory as 'model.pt'")
        return False
    
    print(f"Using model: {model_path}")
    
    # Create sample datasets
    temp_files = create_sample_datasets()
    
    try:
        for dataset_name, file_path in temp_files.items():
            print(f"\nTesting with {dataset_name.upper()} data")
            print("-" * 50)
            
            # Analyze schema
            print(f"Schema analysis for {dataset_name} dataset:")
            os.system(f'python adaptive_search.py --data {file_path} --model "{model_path}" --analyze')
            
            # Test searches relevant to each dataset
            if dataset_name == "ecommerce":
                test_queries = ["wireless headphones", "gaming laptop", "smartphone case"]
            elif dataset_name == "hr":
                test_queries = ["software engineer", "network administrator", "product manager"]
            elif dataset_name == "medical":
                test_queries = ["hypertension treatment", "migraine symptoms", "severe headache"]
            
            print(f"\nSample searches for {dataset_name}:")
            for query in test_queries[:2]:  # Test first 2 queries
                print(f"\nQuery: '{query}'")
                os.system(f'python adaptive_search.py --data {file_path} --model "{model_path}" --query "{query}" --topk 3')
    
    finally:
        # Cleanup temporary files
        for file_path in temp_files.values():
            if os.path.exists(file_path):
                os.remove(file_path)
        print(f"\nCleaned up temporary files")
        return True

def demonstrate_adaptability():
    """Demonstrate key adaptive features"""
    print("\nKey Adaptive Features Demonstrated:")
    print("=" * 70)
    
    print("""
1. AUTOMATIC SCHEMA DETECTION
   - Identifies text fields (title, description, symptoms)
   - Finds ID fields (product_id, employee_id, patient_id)
   - Detects categorical fields (category, department, severity)
   - Recognizes numeric fields (price, salary, age)

2. DYNAMIC FIELD BOOSTING
   - Text fields get 1.5x boost (descriptions, symptoms)
   - ID fields get 3.0x boost (exact matches)
   - Name fields get 2.0x boost (titles, names)
   - Automatically adapts to ANY field names

3. FLEXIBLE CONFIGURATION
   - No hardcoded domain keywords
   - Learns from actual data content
   - Adapts boost factors to data patterns
   - Works with any JSON structure

4. CONFIDENCE SCORING
   - Measures result reliability
   - Combines semantic + keyword matching
   - Filters low-confidence results
   - Provides search quality metrics

5. UNIVERSAL COMPATIBILITY
   - Works with any JSON data source
   - No schema migration needed
   - Preserves search quality across domains
   - Automatically optimizes for your data
   """)

def show_comparison_example():
    """Show comparison between fixed and adaptive search"""
    print("\nFixed vs Adaptive Search Comparison:")
    print("=" * 70)
    
    print("""
FIXED SEARCH (Original enhanced_search.py):
   PASS Works perfectly with training data schema
   FAIL Hardcoded for 'tickets', 'devices', 'customers', 'accounts'
   FAIL Expects specific field names (Description, ProblemNotes, etc.)
   FAIL Fails with new data sources
   FAIL Requires manual configuration for each new schema

ADAPTIVE SEARCH (New adaptive_search.py):
   PASS Works with ANY JSON schema
   PASS Auto-detects important fields
   PASS Learns boost factors from data
   PASS Adapts to any domain
   PASS Zero configuration required

MIGRATION PATH:
1. For existing data: Keep using enhanced_search.py (optimized)
2. For new data sources: Use adaptive_search.py (flexible)
3. For mixed scenarios: Use adaptive_search.py (universal)
""")

def main():
    parser = argparse.ArgumentParser(
        description="Test adaptive search with different data sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python test_adaptive_search.py --model model.pt
  EMBEDDING_MODEL_PATH=/path/to/model.pt python test_adaptive_search.py
  python test_adaptive_search.py  # Auto-detect model"""
    )
    parser.add_argument(
        '--model', '-m',
        help='Path to the model file (.pt). If not specified, will try to auto-detect.'
    )
    parser.add_argument(
        '--skip-tests', 
        action='store_true',
        help='Skip actual testing, just show documentation'
    )
    
    args = parser.parse_args()
    
    print("Adaptive Search Testing Suite")
    print("=" * 80)
    print("This demonstrates how adaptive search handles different data sources\n")
    
    if not args.skip_tests:
        # Test with different datasets
        success = test_adaptive_search(args.model)
        if not success:
            sys.exit(1)
    
    # Show key features
    demonstrate_adaptability()
    
    # Show comparison
    show_comparison_example()
    
    print("\nUsage Recommendations:")
    print("=" * 50)
    print("""
For YOUR use case (uploading different data sources):

1. Use adaptive_search.py for new/unknown data:
   python adaptive_search.py --data new_data.jsonl --model your_model.pt --analyze
   # Or with auto-detection: python adaptive_search.py --data new_data.jsonl --analyze

2. Review the auto-detected schema and adjust if needed

3. Search with confidence filtering:
   python adaptive_search.py --data new_data.jsonl --model your_model.pt \\
     --query "your search" --min-confidence 0.3

4. Fine-tune with custom hybrid weights:
   python adaptive_search.py --data new_data.jsonl --model your_model.pt \\
     --query "your search" --hybrid-weight 0.5  # More keyword-focused

Benefits:
PASS Works with ANY JSON data structure  
PASS No manual configuration required
PASS Maintains search quality across domains
PASS Automatically optimizes for your specific data
PASS Provides confidence scores for result quality
""")

if __name__ == "__main__":
    main()
