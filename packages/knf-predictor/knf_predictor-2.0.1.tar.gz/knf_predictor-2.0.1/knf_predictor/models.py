"""
Neural network architectures for KNF prediction
================================================
Contains 5 GNN architectures and the ensemble model.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn import Linear, Sequential, ReLU, GELU, LayerNorm, Dropout
from torch_geometric.nn import GATv2Conv, TransformerConv, GCNConv, GINConv, SAGEConv
from torch_geometric.nn import global_mean_pool, global_add_pool, global_max_pool


class Model1_GAT(nn.Module):
    """Graph Attention Network with 4 layers"""
    
    def __init__(self, node_feat=14, edge_feat=7, hidden=128):
        super().__init__()
        self.conv1 = GATv2Conv(node_feat, hidden, heads=6, dropout=0.15, 
                              edge_dim=edge_feat, concat=True)
        self.conv2 = GATv2Conv(hidden*6, hidden, heads=6, dropout=0.15, 
                              edge_dim=edge_feat, concat=True)
        self.conv3 = GATv2Conv(hidden*6, hidden//2, heads=4, dropout=0.15, 
                              edge_dim=edge_feat, concat=True)
        self.conv4 = GATv2Conv(hidden*2, hidden//2, heads=2, dropout=0.1, 
                              edge_dim=edge_feat, concat=False)
        
        pooled = (hidden//2) * 3
        self.head = Sequential(
            Linear(pooled, 384), GELU(), LayerNorm(384), Dropout(0.2),
            Linear(384, 256), GELU(), LayerNorm(256), Dropout(0.2),
            Linear(256, 128), GELU(), LayerNorm(128), Dropout(0.15),
            Linear(128, 64), GELU(), LayerNorm(64), Linear(64, 9)
        )
    
    def forward(self, batch):
        x = F.gelu(self.conv1(batch.x, batch.edge_index, batch.edge_attr))
        x = F.gelu(self.conv2(x, batch.edge_index, batch.edge_attr))
        x = F.gelu(self.conv3(x, batch.edge_index, batch.edge_attr))
        x = F.gelu(self.conv4(x, batch.edge_index, batch.edge_attr))
        
        pooled = torch.cat([
            global_mean_pool(x, batch.batch), 
            global_max_pool(x, batch.batch), 
            global_add_pool(x, batch.batch)
        ], dim=-1)
        
        return self.head(pooled)


class Model2_Transformer(nn.Module):
    """Transformer-based GNN with 4 layers"""
    
    def __init__(self, node_feat=14, edge_feat=7, hidden=128):
        super().__init__()
        self.conv1 = TransformerConv(node_feat, hidden, heads=6, dropout=0.15, 
                                     edge_dim=edge_feat, concat=True)
        self.conv2 = TransformerConv(hidden*6, hidden, heads=6, dropout=0.15, 
                                     edge_dim=edge_feat, concat=True)
        self.conv3 = TransformerConv(hidden*6, hidden//2, heads=4, dropout=0.15, 
                                     edge_dim=edge_feat, concat=True)
        self.conv4 = TransformerConv(hidden*2, hidden//2, heads=2, dropout=0.1, 
                                     edge_dim=edge_feat, concat=False)
        
        pooled = (hidden//2) * 3
        self.head = Sequential(
            Linear(pooled, 320), GELU(), LayerNorm(320), Dropout(0.25),
            Linear(320, 192), GELU(), LayerNorm(192), Dropout(0.2),
            Linear(192, 96), GELU(), LayerNorm(96), Dropout(0.15),
            Linear(96, 48), GELU(), LayerNorm(48), Linear(48, 9)
        )
    
    def forward(self, batch):
        x = F.gelu(self.conv1(batch.x, batch.edge_index, batch.edge_attr))
        x = F.gelu(self.conv2(x, batch.edge_index, batch.edge_attr))
        x = F.gelu(self.conv3(x, batch.edge_index, batch.edge_attr))
        x = F.gelu(self.conv4(x, batch.edge_index, batch.edge_attr))
        
        pooled = torch.cat([
            global_mean_pool(x, batch.batch), 
            global_max_pool(x, batch.batch),
            global_add_pool(x, batch.batch)
        ], dim=-1)
        
        return self.head(pooled)


class Model3_GIN(nn.Module):
    """Graph Isomorphism Network"""
    
    def __init__(self, node_feat=14, hidden=128):
        super().__init__()
        
        nn1 = Sequential(Linear(node_feat, hidden), ReLU(), Linear(hidden, hidden))
        self.conv1 = GINConv(nn1, train_eps=True)
        
        nn2 = Sequential(Linear(hidden, hidden), ReLU(), Linear(hidden, hidden))
        self.conv2 = GINConv(nn2, train_eps=True)
        
        nn3 = Sequential(Linear(hidden, hidden//2), ReLU(), Linear(hidden//2, hidden//2))
        self.conv3 = GINConv(nn3, train_eps=True)
        
        pooled = (hidden//2) * 3
        self.head = Sequential(
            Linear(pooled, 256), GELU(), LayerNorm(256), Dropout(0.2),
            Linear(256, 192), GELU(), LayerNorm(192), Dropout(0.2),
            Linear(192, 128), GELU(), LayerNorm(128), Dropout(0.15),
            Linear(128, 64), GELU(), LayerNorm(64), Linear(64, 9)
        )
    
    def forward(self, batch):
        x = F.relu(self.conv1(batch.x, batch.edge_index))
        x = F.relu(self.conv2(x, batch.edge_index))
        x = F.relu(self.conv3(x, batch.edge_index))
        
        pooled = torch.cat([
            global_mean_pool(x, batch.batch), 
            global_max_pool(x, batch.batch),
            global_add_pool(x, batch.batch)
        ], dim=-1)
        
        return self.head(pooled)


class Model4_Hybrid(nn.Module):
    """Hybrid GAT + GCN architecture"""
    
    def __init__(self, node_feat=14, edge_feat=7, hidden=128):
        super().__init__()
        
        # GAT branch
        self.gat1 = GATv2Conv(node_feat, hidden//2, heads=4, dropout=0.15, 
                             edge_dim=edge_feat, concat=True)
        self.gat2 = GATv2Conv(hidden*2, hidden//2, heads=2, dropout=0.1, 
                             edge_dim=edge_feat, concat=False)
        
        # GCN branch
        self.gcn1 = GCNConv(node_feat, hidden//2)
        self.gcn2 = GCNConv(hidden//2, hidden//2)
        
        pooled = hidden * 3  # Both branches pooled
        self.head = Sequential(
            Linear(pooled, 320), GELU(), LayerNorm(320), Dropout(0.2),
            Linear(320, 256), GELU(), LayerNorm(256), Dropout(0.2),
            Linear(256, 128), GELU(), LayerNorm(128), Dropout(0.15),
            Linear(128, 64), GELU(), LayerNorm(64), Linear(64, 9)
        )
    
    def forward(self, batch):
        # GAT branch
        x_gat = F.gelu(self.gat1(batch.x, batch.edge_index, batch.edge_attr))
        x_gat = F.gelu(self.gat2(x_gat, batch.edge_index, batch.edge_attr))
        
        # GCN branch
        x_gcn = F.relu(self.gcn1(batch.x, batch.edge_index))
        x_gcn = F.relu(self.gcn2(x_gcn, batch.edge_index))
        
        # Pool both branches
        pool_gat = torch.cat([
            global_mean_pool(x_gat, batch.batch), 
            global_max_pool(x_gat, batch.batch),
            global_add_pool(x_gat, batch.batch)
        ], dim=-1)
        
        pool_gcn = torch.cat([
            global_mean_pool(x_gcn, batch.batch), 
            global_max_pool(x_gcn, batch.batch),
            global_add_pool(x_gcn, batch.batch)
        ], dim=-1)
        
        pooled = torch.cat([pool_gat, pool_gcn], dim=-1)
        return self.head(pooled)


class Model5_SAGE(nn.Module):
    """GraphSAGE with mean/max aggregation"""
    
    def __init__(self, node_feat=14, hidden=128):
        super().__init__()
        self.conv1 = SAGEConv(node_feat, hidden, aggr='mean')
        self.conv2 = SAGEConv(hidden, hidden, aggr='max')
        self.conv3 = SAGEConv(hidden, hidden//2, aggr='mean')
        
        pooled = (hidden//2) * 3
        self.head = Sequential(
            Linear(pooled, 256), GELU(), LayerNorm(256), Dropout(0.2),
            Linear(256, 192), GELU(), LayerNorm(192), Dropout(0.2),
            Linear(192, 128), GELU(), LayerNorm(128), Dropout(0.15),
            Linear(128, 64), GELU(), LayerNorm(64), Linear(64, 9)
        )
    
    def forward(self, batch):
        x = F.relu(self.conv1(batch.x, batch.edge_index))
        x = F.relu(self.conv2(x, batch.edge_index))
        x = F.relu(self.conv3(x, batch.edge_index))
        
        pooled = torch.cat([
            global_mean_pool(x, batch.batch), 
            global_max_pool(x, batch.batch),
            global_add_pool(x, batch.batch)
        ], dim=-1)
        
        return self.head(pooled)


class KNF_Ensemble(nn.Module):
    """
    Weighted ensemble of 5 GNN architectures
    
    Weights optimized via Bayesian optimization:
    - GAT: 20%
    - Transformer: 35%
    - GIN: 0% (excluded)
    - Hybrid: 35%
    - SAGE: 10%
    """
    
    def __init__(self):
        super().__init__()
        self.model_gat = Model1_GAT()
        self.model_transformer = Model2_Transformer()
        self.model_gin = Model3_GIN()
        self.model_hybrid = Model4_Hybrid()
        self.model_sage = Model5_SAGE()
        
        # Ensemble weights (optimized)
        self.register_buffer('weights', torch.tensor([0.20, 0.35, 0.00, 0.35, 0.10]))
    
    def forward(self, batch):
        """Forward pass with weighted ensemble"""
        return (
            self.weights[0] * self.model_gat(batch) + 
            self.weights[1] * self.model_transformer(batch) +
            self.weights[2] * self.model_gin(batch) + 
            self.weights[3] * self.model_hybrid(batch) +
            self.weights[4] * self.model_sage(batch)
        )
