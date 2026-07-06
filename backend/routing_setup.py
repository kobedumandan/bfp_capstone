"""
Shared construction of the GeoAI routing engine.

Used both by the API lifespan (the main-process engine that serves the
/api/routing/* endpoints and the stale-driver watchdog) and by each
routing-pool worker process, so the two are guaranteed to load the same graph
and the same GAT-predicted constraint weights.

Kept free of FastAPI/DB imports so pool subprocesses stay lightweight.
"""
import json
import logging

from ai import (
    GeoAIRoutingEngine, load_qgis_graph, load_roads_gpkg, load_panabo_graph,
    register_env, Config,
)
from ai.config import BASE_DIR

logger = logging.getLogger(__name__)


def _load_constraint_style() -> dict:
    path = Config.CONSTRAINT_STYLE_PATH
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_routing_engine(register_gym: bool = True) -> "GeoAIRoutingEngine | None":
    """Load the road graph + GNN engine and apply routing weights.

    Returns a ready-to-use engine, or None if the graph data could not be
    loaded (callers degrade gracefully). `register_gym` is only needed by the
    main process (RL env registration); pool workers pass False.
    """
    roads_gpkg = BASE_DIR / "data" / "roads_panabo.gpkg"
    nodes_file = BASE_DIR / "data" / "panabo_nodes.geojson"
    edges_file = BASE_DIR / "data" / "panabo_edges.geojson"

    try:
        if roads_gpkg.exists():
            graph = load_roads_gpkg(roads_gpkg)
        elif nodes_file.exists() and edges_file.exists():
            graph = load_qgis_graph(nodes_file, edges_file)
        else:
            graph = load_panabo_graph()

        model_path = Config.GRAPHSAGE_MODEL_PATH
        engine = GeoAIRoutingEngine(
            gnn_type=Config.GNN_TYPE,
            use_rl=Config.USE_RL,
            use_sumo=Config.USE_SUMO,
            gnn_model_path=str(model_path) if model_path.exists() else None,
            in_channels=Config.NODE_FEATURE_DIM,
            hidden_channels=Config.GNN_HIDDEN,
            out_channels=Config.GNN_OUT,
            device=Config.DEVICE,
        )
        engine.graph = graph

        constraints_path = Config.PREDICTED_CONSTRAINTS_PATH
        if constraints_path.exists():
            with open(constraints_path, encoding="utf-8") as f:
                predicted = json.load(f)
            style = _load_constraint_style()
            multiplier_by_type = {
                k: v.get("routing_multiplier", 1.0)
                for k, v in style.items()
                if isinstance(v, dict)
            }
            engine.apply_predicted_constraints(predicted.get("features", []), multiplier_by_type)
        else:
            edge_weights_path = Config.EDGE_WEIGHTS_PATH
            if edge_weights_path.exists():
                with open(edge_weights_path) as f:
                    edge_weights = json.load(f)
                engine.apply_edge_weights(edge_weights)

        if register_gym:
            register_env()
        return engine
    except Exception as exc:
        logger.warning("build_routing_engine failed: %s", exc)
        return None
