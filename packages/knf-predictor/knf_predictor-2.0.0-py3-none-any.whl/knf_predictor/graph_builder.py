"""
Graph construction from XYZ files
=================================
Converts molecular structures to PyTorch Geometric graphs.
"""

import torch
import numpy as np
from torch_geometric.data import Data


# Atomic properties for feature engineering
ATOMIC_PROPERTIES = {
    'H':  {'num': 1,  'mass': 1.008,   'vdw': 1.20, 'eneg': 2.20, 'val': 1, 'cov': 0.31},
    'C':  {'num': 6,  'mass': 12.011,  'vdw': 1.70, 'eneg': 2.55, 'val': 4, 'cov': 0.76},
    'N':  {'num': 7,  'mass': 14.007,  'vdw': 1.55, 'eneg': 3.04, 'val': 3, 'cov': 0.71},
    'O':  {'num': 8,  'mass': 15.999,  'vdw': 1.52, 'eneg': 3.44, 'val': 2, 'cov': 0.66},
    'F':  {'num': 9,  'mass': 18.998,  'vdw': 1.47, 'eneg': 3.98, 'val': 1, 'cov': 0.57},
    'P':  {'num': 15, 'mass': 30.974,  'vdw': 1.80, 'eneg': 2.19, 'val': 5, 'cov': 1.07},
    'S':  {'num': 16, 'mass': 32.065,  'vdw': 1.80, 'eneg': 2.58, 'val': 6, 'cov': 1.05},
    'Cl': {'num': 17, 'mass': 35.453,  'vdw': 1.75, 'eneg': 3.16, 'val': 1, 'cov': 1.02},
    'Br': {'num': 35, 'mass': 79.904,  'vdw': 1.85, 'eneg': 2.96, 'val': 1, 'cov': 1.20},
    'I':  {'num': 53, 'mass': 126.904, 'vdw': 1.98, 'eneg': 2.66, 'val': 1, 'cov': 1.39},
}


def get_atomic_features(atom):
    """
    Extract 14-dimensional feature vector for an atom
    
    Features:
    - Atomic number (normalized)
    - Mass (normalized)
    - Van der Waals radius (normalized)
    - Covalent radius (normalized)
    - Electronegativity (normalized)
    - Valence (normalized)
    - One-hot encoding (H, C, N, O, F, S, P, Cl)
    """
    props = ATOMIC_PROPERTIES.get(
        atom, 
        {'num': 0, 'mass': 1.0, 'vdw': 1.5, 'eneg': 2.0, 'val': 0, 'cov': 0.7}
    )
    
    return np.array([
        props['num'] / 53.0,    # Atomic number
        props['mass'] / 127.0,  # Mass
        props['vdw'] / 2.0,     # VdW radius
        props['cov'] / 1.5,     # Covalent radius
        props['eneg'] / 4.0,    # Electronegativity
        props['val'] / 6.0,     # Valence
        # One-hot encoding
        1.0 if atom == 'H' else 0.0,
        1.0 if atom == 'C' else 0.0,
        1.0 if atom == 'N' else 0.0,
        1.0 if atom == 'O' else 0.0,
        1.0 if atom == 'F' else 0.0,
        1.0 if atom == 'S' else 0.0,
        1.0 if atom == 'P' else 0.0,
        1.0 if atom == 'Cl' else 0.0,
    ], dtype=np.float32)


def build_graph(atoms, coords, cutoff=5.0):
    """
    Build PyTorch Geometric graph from atoms and coordinates
    
    Args:
        atoms (list): List of atomic symbols
        coords (np.ndarray): Nx3 array of coordinates
        cutoff (float): Distance cutoff for edges (Angstroms)
    
    Returns:
        Data: PyTorch Geometric graph object
    """
    n = len(atoms)
    
    # Node features (14-dimensional)
    x = np.array([get_atomic_features(a) for a in atoms])
    
    # Build edges within cutoff
    edge_index = []
    edge_attr = []
    
    for i in range(n):
        for j in range(i+1, n):
            d = np.linalg.norm(coords[i] - coords[j])
            
            if d < cutoff:
                # Add bidirectional edges
                edge_index.extend([[i, j], [j, i]])
                
                # Edge features (7-dimensional)
                r_vec = (coords[j] - coords[i]) / (d + 1e-8)
                edge_feat = [
                    d / cutoff,           # Normalized distance
                    r_vec[0],             # Direction x
                    r_vec[1],             # Direction y
                    r_vec[2],             # Direction z
                    1.0 / (d + 1e-8),     # Inverse distance
                    np.exp(-d),           # Gaussian
                    d ** 2                # Distance squared
                ]
                edge_attr.extend([edge_feat, edge_feat])
    
    # Handle isolated nodes (self-loops)
    if not edge_index:
        edge_index = [[i, i] for i in range(n)]
        edge_attr = [[0., 0., 0., 0., 0., 1., 0.] for _ in range(n)]
    
    return Data(
        x=torch.tensor(x, dtype=torch.float), 
        edge_index=torch.tensor(np.array(edge_index).T, dtype=torch.long),
        edge_attr=torch.tensor(np.array(edge_attr), dtype=torch.float),
        batch=torch.zeros(n, dtype=torch.long)
    )


def read_xyz(path):
    """
    Read XYZ file
    
    Args:
        path (str): Path to XYZ file
    
    Returns:
        tuple: (atoms, coords) where atoms is list of symbols,
               coords is Nx3 numpy array
    """
    with open(path, 'r') as f:
        lines = f.readlines()
    
    n_atoms = int(lines[0].strip())
    atoms = []
    coords = []
    
    for line in lines[2:2+n_atoms]:
        parts = line.strip().split()
        if len(parts) >= 4:
            atoms.append(parts[0])
            coords.append([float(parts[1]), float(parts[2]), float(parts[3])])
    
    return atoms, np.array(coords)
