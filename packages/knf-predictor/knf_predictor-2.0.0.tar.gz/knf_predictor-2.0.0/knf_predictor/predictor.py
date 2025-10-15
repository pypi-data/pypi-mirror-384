"""
Core prediction logic for KNF
==============================
Handles batch and single-molecule predictions.
"""

import torch
import numpy as np
import pandas as pd
import os
import glob
import sys
import time
from pathlib import Path
from tqdm import tqdm  # Add this import

from .models import KNF_Ensemble
from .graph_builder import build_graph, read_xyz


def get_bundled_model_path():
    """Get path to bundled model file"""
    return Path(__file__).parent / "data" / "KNF_Ensemble_v1.0.pth"


def predict_single(xyz_path, device='cpu'):
    """
    Predict KNF for a single molecule
    
    Args:
        xyz_path (str): Path to XYZ file
        device (str): 'cpu' or 'cuda'
    
    Returns:
        dict: Feature names and predicted values
    
    Example:
        >>> result = predict_single("molecule.xyz")
        >>> print(result['nci_attractive_strength'])
        -123.45
    """
    model_path = get_bundled_model_path()
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"❌ Bundled model not found at {model_path}\n"
            f"Please reinstall: pip install --force-reinstall knf-predictor"
        )
    
    # Load model
    pkg = torch.load(model_path, map_location=device, weights_only=False)
    
    model = KNF_Ensemble()
    model.load_state_dict(pkg['model_state_dict'])
    model.to(device)
    model.eval()
    
    # Build graph and predict
    atoms, coords = read_xyz(xyz_path)
    graph = build_graph(atoms, coords).to(device)
    
    with torch.no_grad():
        pred_scaled = model(graph).cpu().numpy().flatten()
    
    # Inverse transform
    pred = pkg['scaler'].inverse_transform(pred_scaled.reshape(1, -1)).flatten()
    
    return {f: float(v) for f, v in zip(pkg['feature_names'], pred)}


def predict_batch(input_folder, output_csv, device='cpu'):
    """
    Predict KNF for all XYZ files in a folder
    
    Args:
        input_folder (str): Path to folder containing .xyz files
        output_csv (str): Output CSV file path
        device (str): 'cpu' or 'cuda'
    
    Example:
        >>> predict_batch("./molecules", "results.csv", device='cuda')
    """
    
    print("\n" + "=" * 80)
    print("🧠 KNF PREDICTOR - Batch Prediction")
    print("=" * 80)
    print(f"\n📂 Input:  {input_folder}")
    print(f"💾 Output: {output_csv}")
    print(f"🖥️  Device: {device.upper()}\n")
    
    # Load bundled model
    model_path = get_bundled_model_path()
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"❌ Bundled model not found at {model_path}\n"
            f"Please reinstall: pip install --force-reinstall knf-predictor"
        )
    
    print(f"Loading 5-model ensemble from {model_path.name}...")
    pkg = torch.load(model_path, map_location=device, weights_only=False)
    
    model = KNF_Ensemble()
    model.load_state_dict(pkg['model_state_dict'])
    model.to(device)
    model.eval()
    
    scaler = pkg['scaler']
    features = pkg['feature_names']
    
    print(f"  Version: {pkg['metadata']['version']}")
    print(f"  R² = {pkg['metadata']['overall_r2']:.4f}")
    print(f"  Models: GAT (20%) + Transformer (35%) + Hybrid (35%) + SAGE (10%)\n")
    
    # Find XYZ files
    files = sorted(glob.glob(os.path.join(input_folder, '*.xyz')))
    
    if not files:
        raise ValueError(f"❌ No .xyz files found in {input_folder}")
    
    print(f"🔬 Processing {len(files):,} molecules...\n")
    
    # Progress tracking with tqdm
    results = []
    start_time = time.time()
    
    # Use tqdm progress bar
    with tqdm(total=len(files), ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:
        for fpath in files:
            try:
                # Read and build graph
                atoms, coords = read_xyz(fpath)
                graph = build_graph(atoms, coords).to(device)
                
                # Predict
                with torch.no_grad():
                    pred_scaled = model(graph).cpu().numpy().flatten()
                
                # Inverse transform
                pred = scaler.inverse_transform(pred_scaled.reshape(1, -1)).flatten()
                
                # Store result
                result = {'filename': os.path.basename(fpath)}
                result.update({f: float(v) for f, v in zip(features, pred)})
                results.append(result)
                
            except Exception as e:
                pbar.write(f"  ⚠️  Failed: {os.path.basename(fpath)} - {str(e)}")
            
            # Update progress bar
            pbar.update(1)
    
    print("\n")
    
    # Save results
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False, float_format='%.6f')
    
    # Summary
    total_time = time.time() - start_time
    print(f"✅ Saved {len(results):,} predictions to {output_csv}")
    print(f"\n📊 Statistics:")
    print(f"   Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"   Speed: {len(results)/total_time:.2f} molecules/second")
    print(f"   Throughput: {len(results)/total_time*3600:.0f} molecules/hour\n")
    
    # Preview
    print(f"📋 Preview (first 3 molecules):")
    print(df.head(3).to_string(index=False))
    print("\n" + "=" * 80)
