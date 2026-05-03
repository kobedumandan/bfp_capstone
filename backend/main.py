from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import check_connection
from ai import GeoAIRoutingEngine, load_qgis_graph, load_panabo_graph, register_env, Config

logger = logging.getLogger(__name__)

# ── Application lifespan ──────────────────────────────────────────────────────

routing_engine: GeoAIRoutingEngine = None  # populated in lifespan


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global routing_engine

    nodes_file = Config.BASE_DIR / "data" / "panabo_nodes.geojson"
    edges_file = Config.BASE_DIR / "data" / "panabo_edges.geojson"

    if nodes_file.exists() and edges_file.exists():
        logger.info("Loading road network from QGIS GeoJSON exports …")
        graph = load_qgis_graph(nodes_file, edges_file)
    else:
        logger.info("QGIS files not found — downloading from OSM (first run only) …")
        graph = load_panabo_graph()

    routing_engine = GeoAIRoutingEngine(
        gnn_type=Config.GNN_TYPE,
        use_rl=Config.USE_RL,
        use_sumo=Config.USE_SUMO,
        in_channels=Config.NODE_FEATURE_DIM,
        hidden_channels=Config.GNN_HIDDEN,
        out_channels=Config.GNN_OUT,
        device=Config.DEVICE,
    )
    routing_engine.graph = graph

    register_env()
    logger.info("GeoAI routing engine ready. Graph: %s", graph.summary())

    yield  # server runs here

    if routing_engine:
        routing_engine.shutdown()
    logger.info("Routing engine shut down.")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BFP Capstone — GeoAI Fire Response API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    source_node: int
    target_node: int


class RouteResponse(BaseModel):
    route_nodes: list[int]
    eta_seconds: int
    gnn_confidence: float
    route_wkt: str
    computation_ms: float


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "BFP Capstone API is running"}


@app.get("/health")
def health():
    db_ok = check_connection()
    return {"api": "ok", "database": "ok" if db_ok else "unavailable"}


@app.post("/api/routing/compute", response_model=RouteResponse)
def compute_route(req: RouteRequest):
    try:
        result = routing_engine.compute_route(req.source_node, req.target_node)
        return RouteResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Routing error: {exc}")


@app.get("/api/routing/graph/summary")
def graph_summary():
    return routing_engine.graph.summary()


@app.get("/api/routing/nearest-station")
def nearest_station(lat: float, lon: float):
    node_id = routing_engine.nearest_station_node(lat, lon)
    if node_id is None:
        raise HTTPException(status_code=404, detail="No station node found near that location.")
    node_data = routing_engine.graph.G.nodes[node_id]
    return {"node_id": node_id, "lat": node_data["lat"], "lon": node_data["lon"]}
