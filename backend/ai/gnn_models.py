"""
Graph Neural Network models for GeoAI fire-response routing.

Models implemented:
  - GCN       : Graph Convolutional Network (Kipf & Welling, 2017)
  - GAT       : Graph Attention Network (Veličković et al., 2018)
  - GraphSAGE : Inductive Representation Learning (Hamilton et al., 2017)
  - PMGCN     : Personalized Multi-task GCN for multi-objective routing
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import (
    GCNConv,
    GATConv,
    SAGEConv,
)
from torch_geometric.nn import global_mean_pool


# ── GCN ───────────────────────────────────────────────────────────────────────

class GCN(nn.Module):
    """
    Graph Convolutional Network for road-network node embeddings.

    Args:
        in_channels:  Number of input node features (e.g., lat, lon, speed, congestion).
        hidden_channels: Size of hidden embedding.
        out_channels: Output dimension (e.g., route score per node).
        num_layers:   Depth of the network.
        dropout:      Dropout probability between layers.
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 3,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.dropout = dropout
        self.convs = nn.ModuleList()

        self.convs.append(GCNConv(in_channels, hidden_channels))
        for _ in range(num_layers - 2):
            self.convs.append(GCNConv(hidden_channels, hidden_channels))
        self.convs.append(GCNConv(hidden_channels, out_channels))

    def forward(self, x, edge_index):
        for conv in self.convs[:-1]:
            x = conv(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.convs[-1](x, edge_index)
        return x


# ── GAT ───────────────────────────────────────────────────────────────────────

class GAT(nn.Module):
    """
    Graph Attention Network for attention-weighted road-segment routing.

    Multi-head attention lets the model focus on the most relevant neighbouring
    nodes (intersections) when predicting optimal dispatch routes.

    Args:
        in_channels:     Input node feature dimension.
        hidden_channels: Hidden dimension per attention head.
        out_channels:    Output dimension.
        heads:           Number of attention heads in intermediate layers.
        dropout:         Dropout on attention coefficients.
        num_layers:      Total GAT layers.
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        heads: int = 4,
        dropout: float = 0.3,
        num_layers: int = 3,
    ):
        super().__init__()
        self.dropout = dropout
        self.convs = nn.ModuleList()

        self.convs.append(GATConv(in_channels, hidden_channels, heads=heads, dropout=dropout))
        for _ in range(num_layers - 2):
            self.convs.append(
                GATConv(hidden_channels * heads, hidden_channels, heads=heads, dropout=dropout)
            )
        # Final layer: single head, no concatenation
        self.convs.append(
            GATConv(hidden_channels * heads, out_channels, heads=1, concat=False, dropout=dropout)
        )

    def forward(self, x, edge_index):
        for conv in self.convs[:-1]:
            x = conv(x, edge_index)
            x = F.elu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.convs[-1](x, edge_index)
        return x


# ── GraphSAGE ─────────────────────────────────────────────────────────────────

class GraphSAGE(nn.Module):
    """
    GraphSAGE for inductive generalisation across unseen road sub-graphs.

    Useful when new intersections or road segments are added to Panabo City's
    network without retraining from scratch.

    Args:
        in_channels:     Input node feature dimension.
        hidden_channels: Hidden embedding size.
        out_channels:    Output dimension.
        num_layers:      Number of SAGE aggregation layers.
        dropout:         Dropout probability.
        aggr:            Aggregation scheme ('mean', 'max', 'lstm').
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 3,
        dropout: float = 0.3,
        aggr: str = "mean",
    ):
        super().__init__()
        self.dropout = dropout
        self.convs = nn.ModuleList()

        self.convs.append(SAGEConv(in_channels, hidden_channels, aggr=aggr))
        for _ in range(num_layers - 2):
            self.convs.append(SAGEConv(hidden_channels, hidden_channels, aggr=aggr))
        self.convs.append(SAGEConv(hidden_channels, out_channels, aggr=aggr))

    def forward(self, x, edge_index):
        for conv in self.convs[:-1]:
            x = conv(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.convs[-1](x, edge_index)
        return x


# ── PMGCN ─────────────────────────────────────────────────────────────────────

class PMGCNTask(nn.Module):
    """Single task head used by PMGCN."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_channels, in_channels // 2),
            nn.ReLU(),
            nn.Linear(in_channels // 2, out_channels),
        )

    def forward(self, x):
        return self.fc(x)


class PMGCN(nn.Module):
    """
    Personalized Multi-task GCN (PMGCN) for simultaneous optimisation of
    multiple routing objectives:
        - Task 0: ETA minimisation  (travel time)
        - Task 1: Risk minimisation (incident severity along route)
        - Task 2: Resource balance  (personnel workload distribution)

    A shared GCN backbone produces node embeddings; per-task heads decode them
    into objective-specific scores. A learnable weight vector combines heads
    into a single routing score, personalised per dispatch context.

    Args:
        in_channels:     Input node feature dimension.
        hidden_channels: Shared backbone hidden size.
        task_out_channels: Output dimension for each task head.
        num_tasks:       Number of optimisation objectives.
        num_layers:      Backbone GCN depth.
        dropout:         Dropout probability.
    """

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        task_out_channels: int = 1,
        num_tasks: int = 3,
        num_layers: int = 4,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.dropout = dropout
        self.num_tasks = num_tasks

        # Shared GCN backbone
        self.backbone = nn.ModuleList()
        self.backbone.append(GCNConv(in_channels, hidden_channels))
        for _ in range(num_layers - 1):
            self.backbone.append(GCNConv(hidden_channels, hidden_channels))

        # Per-task decoder heads
        self.task_heads = nn.ModuleList(
            [PMGCNTask(hidden_channels, task_out_channels) for _ in range(num_tasks)]
        )

        # Learnable task-weight vector (softmax-normalised at inference)
        self.task_weights = nn.Parameter(torch.ones(num_tasks))

    def forward(self, x, edge_index):
        # Shared backbone
        for conv in self.backbone:
            x = conv(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        # Per-task predictions
        task_outputs = [head(x) for head in self.task_heads]

        # Weighted combination → single routing score per node
        weights = F.softmax(self.task_weights, dim=0)
        combined = sum(w * t for w, t in zip(weights, task_outputs))
        return combined, task_outputs
