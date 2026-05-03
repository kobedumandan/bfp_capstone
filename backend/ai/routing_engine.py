"""
GeoAI Routing Engine — ties together the GNN models, RL agents,
NetworkX graph, and SUMO simulation into one callable interface
that the FastAPI endpoints will use.

Call flow for a dispatch request:
  1. Build/update RoadNetworkGraph from latest PostGIS data.
  2. Run GNN (GAT or PMGCN) to score every node → routing heat-map.
  3. Feed GNN embeddings + live SUMO congestion into RL agent → next action.
  4. Reconstruct full route with NetworkX Dijkstra (GNN-weighted edges).
  5. Return route (WKT LINESTRING), ETA, and confidence score.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
import torch

from .gnn_models import GAT, PMGCN
from .rl_agents import PPOAgent
from .graph_builder import RoadNetworkGraph
from .sumo_interface import SUMOInterface

logger = logging.getLogger(__name__)


class GeoAIRoutingEngine:
    
    def __init__(
        self,
        gnn_type: str = "gat",
        use_rl: bool = True,
        use_sumo: bool = False,
        gnn_model_path: Optional[str] = None,
        rl_model_path: Optional[str] = None,
        sumo_kwargs: Optional[Dict] = None,
        in_channels: int = 7,
        hidden_channels: int = 64,
        out_channels: int = 16,
        device: str = "cpu",
    ):
        self.device = torch.device(device)
        self.use_rl = use_rl
        self.use_sumo = use_sumo

        # ── GNN model ─────────────────────────────────────────────────────────
        if gnn_type == "pmgcn":
            self.gnn = PMGCN(
                in_channels=in_channels,
                hidden_channels=hidden_channels,
                task_out_channels=out_channels,
            ).to(self.device)
        else:
            self.gnn = GAT(
                in_channels=in_channels,
                hidden_channels=hidden_channels,
                out_channels=out_channels,
            ).to(self.device)

        if gnn_model_path:
            self._load_gnn(gnn_model_path)
        self.gnn.eval()

        # ── RL agent (PPO) ────────────────────────────────────────────────────
        self.rl_agent: Optional[PPOAgent] = None
        if use_rl:
            self.rl_agent = PPOAgent(model_path=rl_model_path or "checkpoints/ppo_dispatch")
            if rl_model_path:
                try:
                    self.rl_agent.load()
                    logger.info("PPO agent loaded from %s", rl_model_path)
                except Exception as exc:
                    logger.warning("PPO load failed (%s) — running without trained RL weights.", exc)

        # ── SUMO interface ────────────────────────────────────────────────────
        self.sumo: Optional[SUMOInterface] = None
        if use_sumo:
            self.sumo = SUMOInterface(**(sumo_kwargs or {}))
            try:
                self.sumo.start()
                logger.info("SUMO simulation connected.")
            except Exception as exc:
                logger.warning("SUMO start failed (%s) — falling back to static routing.", exc)
                self.sumo = None

        # ── Road network graph ─────────────────────────────────────────────────
        self.graph = RoadNetworkGraph()
    
    """ UP UP
    Unified routing engine for fire-response dispatch.

    Args:
        gnn_type:        Which GNN to use for node scoring ('gat' or 'pmgcn').
        use_rl:          Whether to apply RL-based action selection on top of GNN.
        use_sumo:        Whether to pull live congestion data from SUMO.
        gnn_model_path:  Path to pre-trained GNN weights (.pt file).
        rl_model_path:   Path to pre-trained PPO model directory.
        sumo_kwargs:     Kwargs forwarded to SUMOInterface if use_sumo=True.
        in_channels:     GNN input node feature dimension (must match graph_builder.NODE_FEATURE_DIM).
        hidden_channels: GNN hidden embedding size.
        out_channels:    GNN output dimension per node.
        device:          'cpu' or 'cuda'.
    """

    # ── GNN helpers ───────────────────────────────────────────────────────────

    def _load_gnn(self, path: str):
        state = torch.load(path, map_location=self.device)
        self.gnn.load_state_dict(state)
        logger.info("GNN weights loaded from %s", path)

    def _run_gnn(self, data) -> torch.Tensor:
        """Run GNN forward pass and return node embeddings / scores."""
        x = data.x.to(self.device)
        edge_index = data.edge_index.to(self.device)
        with torch.no_grad():
            if isinstance(self.gnn, PMGCN):
                scores, _ = self.gnn(x, edge_index)
            else:
                scores = self.gnn(x, edge_index)
        return scores  # shape: [num_nodes, out_channels]

    # ── Congestion update ─────────────────────────────────────────────────────

    def _update_congestion_from_sumo(self):
        """Pull live congestion from SUMO and apply to graph nodes."""
        if self.sumo is None or not self.sumo.is_connected:
            return
        try:
            self.sumo.step()
            congestion_map = self.sumo.get_congestion_map()
            # Map SUMO edge IDs to graph node IDs (requires edge→node mapping)
            for edge_id, level in congestion_map.items():
                node_id = self._sumo_edge_to_node(edge_id)
                if node_id is not None:
                    self.graph.update_congestion(node_id, level)
        except Exception as exc:
            logger.warning("SUMO congestion update failed: %s", exc)

    def _sumo_edge_to_node(self, edge_id: str) -> Optional[int]:
        """Map a SUMO edge ID to a graph node ID. Override to suit your network."""
        # Convention: SUMO edge IDs are formatted as "node_{id}_to_{id}"
        # or the destination node is the controlling node for congestion.
        try:
            return int(edge_id.split("_")[-1])
        except (ValueError, IndexError):
            return None

    # ── Main routing API ──────────────────────────────────────────────────────

    def compute_route(
        self,
        source_node: int,
        target_node: int,
    ) -> Dict[str, Any]:
        """
        Compute the optimal fire-response route from source to target node.

        Returns a dict with:
          - route_nodes: ordered list of graph node IDs
          - eta_seconds: estimated travel time
          - gnn_confidence: float [0, 100]
          - route_wkt: WKT LINESTRING suitable for PostGIS storage
        """
        t0 = time.perf_counter()

        # 1. Update congestion from SUMO if available
        self._update_congestion_from_sumo()

        # 2. Build PyTorch Geometric data from current graph state
        pyg_data = self.graph.to_pyg()
        if pyg_data.num_nodes == 0:
            raise ValueError("Road network graph has no nodes. Call graph.add_node() first.")

        # 3. Run GNN to get per-node scores
        node_scores = self._run_gnn(pyg_data)  # [N, out_channels]
        node_weights = node_scores.norm(dim=-1).cpu().numpy()  # scalar per node

        # 4. Apply GNN weights as inverse edge costs for Dijkstra
        nodes = sorted(self.graph._node_features.keys())
        node_to_idx = {n: i for i, n in enumerate(nodes)}
        for u, v, data in self.graph.G.edges(data=True):
            idx_u = node_to_idx.get(u, 0)
            gnn_factor = max(0.1, 1.0 - float(node_weights[idx_u]) * 0.1)
            data["weight"] = data.get("travel_time_s", 60.0) * gnn_factor

        # 5. Shortest path with GNN-weighted edges
        route_nodes = self.graph.shortest_path(source_node, target_node)
        eta_seconds = self.graph.shortest_path_length(source_node, target_node)

        # 6. Build WKT LINESTRING from node coordinates
        coords = [
            (self.graph.G.nodes[n]["lon"], self.graph.G.nodes[n]["lat"])
            for n in route_nodes
        ]
        wkt = "LINESTRING(" + ", ".join(f"{lon} {lat}" for lon, lat in coords) + ")"

        # 7. Compute confidence score
        path_scores = [float(node_weights[node_to_idx[n]]) for n in route_nodes if n in node_to_idx]
        confidence = float(np.clip(np.mean(path_scores) * 10, 0, 100)) if path_scores else 50.0

        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(
            "Route %d→%d: %d nodes, ETA %.0fs, confidence %.1f%%, computed in %.1fms",
            source_node, target_node, len(route_nodes), eta_seconds, confidence, elapsed,
        )

        return {
            "route_nodes": route_nodes,
            "eta_seconds": round(eta_seconds),
            "gnn_confidence": round(confidence, 1),
            "route_wkt": wkt,
            "computation_ms": round(elapsed, 1),
        }

    def nearest_station_node(self, incident_lat: float, incident_lon: float) -> Optional[int]:
        """Return the graph node ID of the nearest fire station to an incident."""
        candidates = self.graph.nodes_near(incident_lat, incident_lon, radius_km=20.0)
        for node_id, _ in candidates:
            if self.graph.G.nodes[node_id].get("is_station"):
                return node_id
        return None

    def shutdown(self):
        if self.sumo:
            self.sumo.close()
