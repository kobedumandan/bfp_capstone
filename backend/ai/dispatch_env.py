"""
DispatchRouting-v0 — Custom Gymnasium environment for fire-response routing.

Each episode:
  - Start: a fire station node (source)
  - Goal:  an incident node (target)
  - Agent: picks which neighbouring road node to move to at each step
  - Done:  agent reaches target node, or max_steps exceeded

Observation vector (16 floats):
  [current_node_features(7), target_node_features(7), dist_to_target(1), steps_norm(1)]

Action space:
  Discrete(MAX_NEIGHBORS) — index into sorted neighbor list.
  If action >= actual neighbor count, the agent stays in place (penalised).

Reward:
  - Each step: -(travel_time_s * STEP_TIME_PENALTY) - congestion * CONGESTION_PENALTY
  - Invalid action: INVALID_ACTION_PEN
  - Arrival: +ARRIVAL_BONUS
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from .graph_builder import RoadNetworkGraph, _haversine_km
from .config import Config

logger = logging.getLogger(__name__)


class DispatchRoutingEnv(gym.Env):

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        graph: RoadNetworkGraph,
        max_steps: int = Config.MAX_STEPS_PER_EP,
        max_neighbors: int = Config.MAX_NEIGHBORS,
    ):
        super().__init__()
        self.graph = graph
        self.max_steps = max_steps
        self.max_neighbors = max_neighbors

        obs_dim = Config.NODE_FEATURE_DIM * 2 + 2  # 16
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(max_neighbors)

        self._current_node: Optional[int] = None
        self._target_node: Optional[int] = None
        self._steps: int = 0
        self._station_nodes: list[int] = []
        self._incident_nodes: list[int] = []

        self._build_node_lists()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _build_node_lists(self):
        for n, d in self.graph.G.nodes(data=True):
            if d.get("is_station"):
                self._station_nodes.append(n)
            if d.get("is_incident"):
                self._incident_nodes.append(n)

        all_nodes = list(self.graph.G.nodes())
        if not self._station_nodes:
            self._station_nodes = all_nodes
        if not self._incident_nodes:
            self._incident_nodes = all_nodes

    # ── Observation ───────────────────────────────────────────────────────────

    def _node_features(self, node_id: int) -> np.ndarray:
        feats = self.graph._node_features.get(node_id, [0.0] * Config.NODE_FEATURE_DIM)
        arr = np.array(feats, dtype=np.float32)
        # Normalise lat/lon relative to Panabo City centre (~7.308, 125.684)
        arr[0] = (arr[0] - 7.308) / 0.5
        arr[1] = (arr[1] - 125.684) / 0.5
        arr[5] = arr[5] / Config.MAX_SPEED_KMH
        return arr

    def _get_obs(self) -> np.ndarray:
        curr_feat = self._node_features(self._current_node)
        tgt_feat  = self._node_features(self._target_node)

        curr_data = self.graph.G.nodes[self._current_node]
        tgt_data  = self.graph.G.nodes[self._target_node]
        dist_km   = _haversine_km(
            curr_data["lat"], curr_data["lon"],
            tgt_data["lat"],  tgt_data["lon"],
        )
        dist_norm  = np.float32(dist_km / Config.MAX_DIST_KM)
        steps_norm = np.float32(self._steps / self.max_steps)

        return np.concatenate([curr_feat, tgt_feat, [dist_norm, steps_norm]])

    # ── Gymnasium API ─────────────────────────────────────────────────────────

    def reset(self, *, seed: Optional[int] = None, options=None):
        super().reset(seed=seed)
        rng = np.random.default_rng(seed)

        self._current_node = int(rng.choice(self._station_nodes))
        candidates = [n for n in self._incident_nodes if n != self._current_node]
        if not candidates:
            candidates = [n for n in self.graph.G.nodes() if n != self._current_node]
        self._target_node = int(rng.choice(candidates))
        self._steps = 0

        return self._get_obs(), {}

    def step(self, action: int):
        neighbors = list(self.graph.G.successors(self._current_node))
        self._steps += 1

        if action < len(neighbors):
            next_node = neighbors[action]
            edge_data  = self.graph.G.get_edge_data(self._current_node, next_node) or {}
            travel_time = float(edge_data.get("travel_time_s", 60.0))
            congestion  = float(
                self.graph._node_features.get(next_node, [0] * Config.NODE_FEATURE_DIM)[4]
            )
            step_reward = (
                -(travel_time * Config.STEP_TIME_PENALTY)
                - congestion * Config.CONGESTION_PENALTY
            )
            self._current_node = next_node
        else:
            step_reward = Config.INVALID_ACTION_PEN

        arrived   = self._current_node == self._target_node
        truncated = self._steps >= self.max_steps

        reward = step_reward + (Config.ARRIVAL_BONUS if arrived else 0.0)

        return self._get_obs(), reward, arrived, truncated, {}

    def render(self):
        curr = self.graph.G.nodes[self._current_node]
        tgt  = self.graph.G.nodes[self._target_node]
        dist = _haversine_km(curr["lat"], curr["lon"], tgt["lat"], tgt["lon"])
        print(
            f"Step {self._steps:3d} | node {self._current_node} → target {self._target_node} "
            f"| dist {dist:.3f} km"
        )

    def close(self):
        pass


# ── Gymnasium registration ────────────────────────────────────────────────────

def register_env():
    """
    Register DispatchRouting-v0 with Gymnasium so agents can call
    gym.make('DispatchRouting-v0').

    Must be called after the graph is built:
        from ai.dispatch_env import register_env
        register_env()
    """
    from gymnasium.envs.registration import register, registry

    if Config.ENV_ID in registry:
        return

    register(
        id=Config.ENV_ID,
        entry_point="ai.dispatch_env:DispatchRoutingEnv",
        kwargs={"graph": None},  # caller must pass graph= in gym.make()
        max_episode_steps=Config.MAX_STEPS_PER_EP,
    )
    logger.info("Registered Gymnasium environment '%s'", Config.ENV_ID)
