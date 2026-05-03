"""
SUMO (Simulation of Urban MObility) interface via TraCI.

Connects to a running SUMO instance for:
  - Realistic traffic simulation in Panabo City road network
  - Live congestion data feed into the GNN graph
  - Route validation and ETA estimation
  - Training environment for RL agents

Prerequisites:
  1. Install SUMO: https://sumo.dlr.de/docs/Installing/
  2. Set the SUMO_HOME environment variable to your SUMO installation path.
  3. Add %SUMO_HOME%/tools to PYTHONPATH (Windows) or $SUMO_HOME/tools (Linux/Mac).
  4. Prepare a SUMO network file (.net.xml) for Panabo City using OSM data:
       python $SUMO_HOME/tools/osmWebWizard.py  (or netconvert from OSM)
"""

from __future__ import annotations

import os
import sys
import subprocess
import time
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# add sumo i nto path at import
_SUMO_HOME = os.environ.get("SUMO_HOME", "")
if _SUMO_HOME:
    _tools = os.path.join(_SUMO_HOME, "tools")
    if _tools not in sys.path:
        sys.path.insert(0, _tools)

try:
    import traci
    import sumolib
    _SUMO_AVAILABLE = True
except ImportError:
    _SUMO_AVAILABLE = False
    logger.warning(
        "TraCI / sumolib not importable. Install SUMO and set SUMO_HOME, "
        "or run: pip install traci sumolib"
    )


def _require_sumo():
    if not _SUMO_AVAILABLE:
        raise RuntimeError(
            "SUMO is not installed or SUMO_HOME is not set. "
            "See backend/ai/sumo_interface.py for setup instructions."
        )


class SUMOInterface:
    """
    Wraps a TraCI connection to a SUMO simulation.

    Typical usage:
        sumo = SUMOInterface(net_file="panabo.net.xml", gui=False)
        sumo.start()
        for step in range(1000):
            sumo.step()
            congestion = sumo.get_edge_congestion("edge_123")
        sumo.close()
    """

    def __init__(
        self,
        net_file: str = "sumo/panabo.net.xml",
        route_file: str = "sumo/panabo.rou.xml",
        config_file: Optional[str] = None,
        port: int = 8813,
        step_length: float = 1.0,
        gui: bool = False,
        seed: int = 42,
    ):
        _require_sumo()
        self.net_file = net_file
        self.route_file = route_file
        self.config_file = config_file
        self.port = port
        self.step_length = step_length
        self.gui = gui
        self.seed = seed
        self._process: Optional[subprocess.Popen] = None
        self._connected = False
        self._step = 0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        """Launch SUMO and open a TraCI connection."""
        binary = "sumo-gui" if self.gui else "sumo"
        sumo_bin = os.path.join(_SUMO_HOME, "bin", binary)
        if not os.path.exists(sumo_bin):
            sumo_bin = binary  # rely on PATH

        if self.config_file:
            cmd = [sumo_bin, "-c", self.config_file,
                   "--remote-port", str(self.port),
                   "--seed", str(self.seed),
                   "--step-length", str(self.step_length)]
        else:
            cmd = [sumo_bin,
                   "-n", self.net_file,
                   "-r", self.route_file,
                   "--remote-port", str(self.port),
                   "--seed", str(self.seed),
                   "--step-length", str(self.step_length),
                   "--no-warnings", "true",
                   "--log", "sumo.log"]

        self._process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)  # give SUMO time to bind the port
        traci.init(port=self.port)
        self._connected = True
        self._step = 0
        logger.info("SUMO started on port %d", self.port)

    def step(self, n: int = 1):
        """Advance simulation by n steps."""
        for _ in range(n):
            traci.simulationStep()
            self._step += 1

    def close(self):
        if self._connected:
            traci.close()
            self._connected = False
        if self._process:
            self._process.terminate()
            self._process = None
        logger.info("SUMO stopped at step %d", self._step)

    def reset(self):
        self.close()
        self.start()

    # ── Vehicle management ────────────────────────────────────────────────────

    def add_vehicle(
        self,
        vehicle_id: str,
        route_id: str,
        depart: float = 0.0,
        type_id: str = "firetruckType",
    ):
        """Insert a vehicle (fire truck) into the simulation."""
        traci.vehicle.add(vehicle_id, route_id, typeID=type_id, depart=depart)

    def set_vehicle_route(self, vehicle_id: str, edge_ids: List[str]):
        """Dynamically reroute a vehicle to follow a specific edge list."""
        traci.vehicle.setRoute(vehicle_id, edge_ids)

    def get_vehicle_position(self, vehicle_id: str) -> Tuple[float, float]:
        """Returns (lon, lat) of the vehicle's current position."""
        x, y = traci.vehicle.getPosition(vehicle_id)
        lon, lat = traci.simulation.convertGeo(x, y)
        return lon, lat

    def get_vehicle_speed(self, vehicle_id: str) -> float:
        return traci.vehicle.getSpeed(vehicle_id)  # m/s

    def get_vehicle_eta(self, vehicle_id: str) -> float:
        """Estimated remaining travel time in seconds."""
        return traci.vehicle.getExpectedTravelTime(vehicle_id)

    def get_all_vehicles(self) -> List[str]:
        return list(traci.vehicle.getIDList())

    # ── Traffic state ─────────────────────────────────────────────────────────

    def get_edge_congestion(self, edge_id: str) -> float:
        """
        Normalised congestion [0, 1] for a road edge.
        0 = free flow, 1 = fully congested.
        """
        capacity = traci.lane.getLastStepVehicleNumber(edge_id + "_0")
        max_cap = traci.lane.getLength(edge_id + "_0") / 7.5  # ~7.5 m per vehicle
        return min(1.0, capacity / max_cap) if max_cap > 0 else 0.0

    def get_edge_travel_time(self, edge_id: str) -> float:
        """Current travel time (seconds) on an edge."""
        return traci.edge.getTraveltime(edge_id)

    def get_all_edges(self) -> List[str]:
        return list(traci.edge.getIDList())

    def get_congestion_map(self) -> Dict[str, float]:
        """Congestion level for every edge in the network."""
        return {e: self.get_edge_congestion(e) for e in self.get_all_edges()}

    # ── Route validation ──────────────────────────────────────────────────────

    def compute_route_eta(self, from_edge: str, to_edge: str) -> float:
        """Ask SUMO for the shortest-path travel time between two edges."""
        stage = traci.simulation.findRoute(from_edge, to_edge)
        return stage.travelTime

    def get_route_edges(self, from_edge: str, to_edge: str) -> List[str]:
        """Shortest-path edge sequence from SUMO's Dijkstra."""
        stage = traci.simulation.findRoute(from_edge, to_edge)
        return list(stage.edges)

    # ── Observation builder for RL environment ────────────────────────────────

    def build_observation(
        self,
        vehicle_id: str,
        target_edge: str,
        graph_embedding: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Assemble an observation vector for an RL agent step.

        Components (concatenated):
          - vehicle speed (normalised)
          - remaining ETA (normalised)
          - congestion of current edge
          - optional GNN node embedding for current position
        """
        speed = self.get_vehicle_speed(vehicle_id) / 30.0  # normalise by ~max speed
        eta = min(self.get_vehicle_eta(vehicle_id) / 600.0, 1.0)  # cap at 10 min
        curr_edge = traci.vehicle.getRoadID(vehicle_id)
        congestion = self.get_edge_congestion(curr_edge) if curr_edge else 0.0

        base_obs = np.array([speed, eta, congestion], dtype=np.float32)
        if graph_embedding is not None:
            return np.concatenate([base_obs, graph_embedding.astype(np.float32)])
        return base_obs

    @property
    def current_step(self) -> int:
        return self._step

    @property
    def is_connected(self) -> bool:
        return self._connected
