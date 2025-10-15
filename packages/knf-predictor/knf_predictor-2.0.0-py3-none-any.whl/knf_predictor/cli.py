#!/usr/bin/env python3
"""Command-line interface for KNF predictor"""

import argparse
import sys
from pathlib import Path
from .predictor import predict_batch
from . import __version__, __citation__


def main():
    """Main entry point for CLI"""
    
    print("=" * 80)
    print(f"🧠 KNF PREDICTOR v{__version__} - Supramolecular Stability Prediction")
    print("=" * 80)
    
    parser = argparse.ArgumentParser(
        prog='knf-predict',
        description='🧠 AI-powered KNF prediction from XYZ files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  knf-predict -i ./molecules -o results.csv
  knf-predict -i ./data --device cuda
  knf-predict --version
  knf-predict --cite

{__citation__}

GitHub: https://github.com/prasanna-kulkarni/knf-predictor
        """
    )
    
    parser.add_argument('--input', '-i', 
                       help='Folder containing .xyz files')
    parser.add_argument('--output', '-o', 
                       default='knf_predictions.csv',
                       help='Output CSV file (default: knf_predictions.csv)')
    parser.add_argument('--device', '-d', 
                       default='cpu', 
                       choices=['cpu', 'cuda'],
                       help='Device to use (default: cpu)')
    parser.add_argument('--version', '-v', 
                       action='version',
                       version=f'KNF Predictor v{__version__}')
    parser.add_argument('--cite', 
                       action='store_true',
                       help='Show citation information')
    
    args = parser.parse_args()
    
    if args.cite:
        print(__citation__)
        sys.exit(0)
    
    if not args.input:
        parser.print_help()
        sys.exit(1)
    
    # Run prediction
    predict_batch(args.input, args.output, device=args.device)


if __name__ == "__main__":
    main()
