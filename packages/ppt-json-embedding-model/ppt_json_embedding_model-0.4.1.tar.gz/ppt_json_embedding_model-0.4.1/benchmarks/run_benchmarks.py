#!/usr/bin/env python3
"""
Unified benchmark runner for the JSON embedding model.

This script provides a simple interface to run various benchmarks
and generate comprehensive reports.
"""

import argparse
import sys
from pathlib import Path

def main():
    """Main benchmark runner."""
    parser = argparse.ArgumentParser(
        description="Run benchmarks for the JSON embedding model"
    )
    
    parser.add_argument(
        "--type", 
        choices=["quick", "comprehensive", "performance", "quality"],
        default="quick",
        help="Type of benchmark to run"
    )
    
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to model checkpoint"
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        help="Directory containing test data"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="benchmark_results",
        help="Output directory for results"
    )
    
    args = parser.parse_args()
    
    if args.type == "quick":
        print("Running quick benchmark...")
        from .quick_benchmark import main as quick_main
        quick_main()
        
    elif args.type == "comprehensive":
        print("Running comprehensive benchmark...")
        # Import and run comprehensive benchmark
        from .benchmark_embedding_model import main as comprehensive_main
        
        # Build arguments for comprehensive benchmark
        comp_args = []
        if args.model_path:
            comp_args.extend(["--model-path", args.model_path])
        if args.data_dir:
            comp_args.extend(["--data-dir", args.data_dir])
        comp_args.extend(["--output-dir", args.output_dir])
        
        # Mock sys.argv for the comprehensive benchmark
        original_argv = sys.argv
        sys.argv = ["benchmark_embedding_model.py"] + comp_args
        
        try:
            comprehensive_main()
        finally:
            sys.argv = original_argv
            
    else:
        print(f"Benchmark type '{args.type}' not yet implemented")
        return 1
    
    print(f"Benchmark completed. Results saved to {args.output_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
