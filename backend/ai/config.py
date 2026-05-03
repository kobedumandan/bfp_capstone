"""
Centralised configuration for the AI / GeoAI routing module.

All paths are resolved relative to the backend/ directory so they work
regardless of where uvicorn is launched from.
"""

from pathlib import Path
import os

# backend/
BASE_DIR = Path(__file__).parent.parent

class Config:
    # ── Project / Location ────────────────────────────────────────────────────
    PLACE_NAME = "Panabo City, Davao del Norte, Philippines"
    COORD_SRID = 4326  # WGS84

    # ── Directory layout ──────────────────────────────────────────────────────
    CACHE_DIR       = BASE_DIR / "cache"
    CHECKPOINT_DIR  = BASE_DIR / "checkpoints"
    SUMO_DIR        = BASE_DIR / "sumo"

    # ── Cached OSM graph (avoids re-downloading every restart) ────────────────
    OSM_GRAPHML     = CACHE_DIR / "panabo_graph.graphml"

    # ── Model checkpoints ─────────────────────────────────────────────────────
    GNN_MODEL_PATH  = CHECKPOINT_DIR / "gnn_model.pt"
    PPO_MODEL_PATH  = str(CHECKPOINT_DIR / "ppo_dispatch")
    DQN_MODEL_PATH  = str(CHECKPOINT_DIR / "dqn_dispatch")
    DDPG_MODEL_PATH = str(CHECKPOINT_DIR / "ddpg_dispatch")
    A3C_MODEL_PATH  = str(CHECKPOINT_DIR / "a3c_dispatch.pt")

    # ── SUMO network files ────────────────────────────────────────────────────
    SUMO_NET_FILE   = str(SUMO_DIR / "panabo.net.xml")
    SUMO_ROUTE_FILE = str(SUMO_DIR / "panabo.rou.xml")
    SUMO_PORT       = int(os.getenv("SUMO_PORT", "8813"))
    SUMO_STEP_LEN   = 1.0  # seconds per simulation step

    # ── GNN hyperparameters ───────────────────────────────────────────────────
    GNN_TYPE            = os.getenv("GNN_TYPE", "gat")      # 'gat' | 'pmgcn'
    NODE_FEATURE_DIM    = 7
    GNN_HIDDEN          = 64
    GNN_OUT             = 16

    # ── RL / Gymnasium environment ────────────────────────────────────────────
    ENV_ID              = "DispatchRouting-v0"
    MAX_NEIGHBORS       = 8    # action-space size (Discrete)
    MAX_STEPS_PER_EP    = 200  # episode truncation limit
    ARRIVAL_BONUS       = 100.0
    STEP_TIME_PENALTY   = 1.0 / 60.0   # per second of travel time
    INVALID_ACTION_PEN  = -10.0
    CONGESTION_PENALTY  = 5.0

    # ── Feature normalisation constants ───────────────────────────────────────
    MAX_DIST_KM         = 50.0   # Panabo City bounding box diagonal
    MAX_SPEED_KMH       = 80.0
    MAX_ETA_S           = 600.0  # 10 minutes

    # ── Runtime flags (toggle via environment variables) ──────────────────────
    USE_SUMO            = os.getenv("USE_SUMO", "false").lower() == "true"
    USE_RL              = os.getenv("USE_RL", "false").lower() == "true"
    DEVICE              = os.getenv("TORCH_DEVICE", "cpu")
