# FireOPS 🔥🧑‍🚒

A fire-response dispatch and incident-management system built for the Bureau of Fire
Protection (BFP). FireOPS gives dispatchers a real-time web command center and gives
field personnel a companion mobile app, tied together by a FastAPI backend that plans
optimal fire-truck routes using a Graph Neural Network (GNN) trained on local road data.

> This repository holds the **web dashboard** and **backend**. The personnel mobile app
> (React Native / Expo) lives in a separate `bfp_capstone_mobile/` project.

---

## What it does

- **Incident intake & mapping** — Log fire incidents, view them on a live Leaflet map
  with heatmaps, station coverage isochrones, and predicted road constraints.
- **AI routing** — A GNN-based routing engine plans fastest truck routes over the Panabo
  road network, accounting for narrow roads and traffic-crowded areas predicted by the model.
- **Dispatch & teams** — Auto-dispatch selects the best available response team/truck,
  then tracks the crew live as they head to the scene.
- **Live tracking & deviations** — Personnel positions stream in over WebSocket; the
  backend detects when a manned truck deviates from its route and computes a reconnecting
  path automatically.
- **Reporter location via SMS** — Sends a citizen reporter a one-tap link (PhilSMS) to
  share their exact location while filing a report.
- **Metrics & coverage** — Dashboards for response coverage per barangay and operational
  metrics.

---

## Tech stack

| Layer      | Stack                                                                      |
|------------|----------------------------------------------------------------------------|
| Backend    | Python, FastAPI, Uvicorn, SQLAlchemy + Alembic, GeoAlchemy2                 |
| Database   | PostgreSQL with the **PostGIS** extension                                   |
| AI/Routing | PyTorch + PyTorch Geometric (GNN), NetworkX, GeoPandas, Shapely            |
| Frontend   | React 19, Vite, Leaflet / react-leaflet, leaflet.heat                       |
| Messaging  | PhilSMS (reporter location links), WebSocket (real-time dashboard updates)  |

---

## Repository layout

```
bfp_capstone/
├── backend/                 # FastAPI application
│   ├── main.py              # App entry point (routes, WebSocket, lifespan)
│   ├── run.py               # Production Uvicorn launcher (WEB_CONCURRENCY workers)
│   ├── models.py            # SQLAlchemy ORM models
│   ├── database.py          # Engine / session / connection pool
│   ├── ai/                  # GNN routing engine, graph builder, RL/SUMO experiments
│   ├── coverage_engine.py   # Station reachability / barangay coverage
│   ├── auto_dispatch.py     # Best-team selection
│   ├── routing_pool.py      # Process-pool offload for CPU-bound route builds
│   ├── sms.py               # PhilSMS integration
│   ├── alembic/             # Database migrations
│   ├── seed_*.py            # Seed scripts (admin, barangays, personnel, incidents)
│   ├── data/                # Road-network & candidate geopackages (.gpkg)
│   └── requirements.txt
├── frontend/                # React + Vite web dashboard
│   ├── src/
│   │   ├── components/      # Pages + modals (Incidents, Teams, Trucks, Metrics, …)
│   │   ├── api.js           # API client
│   │   └── main.jsx
│   └── package.json
├── gnn-files-to-be-checked/ # Raw GNN input geopackages under review
└── gps-sms-test/            # Standalone GPS/SMS test harness (json-server)
```

---

## Prerequisites

- **Python 3.11+** and **Node.js 18+**
- **PostgreSQL 14+** with the **PostGIS** extension enabled
- (Optional) An **ngrok** / dev-tunnel URL if you need the mobile app or SMS reporter
  links to reach your local backend
- (Optional) A **PhilSMS** API token to actually send SMS

---

## Running the backend

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate            # Windows (PowerShell/CMD)
# source venv/bin/activate       # macOS/Linux

# 2. Install PyTorch FIRST (match your hardware — see requirements.txt header)
#    CPU only:
pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
#    Then install torch-geometric and the rest:
pip install torch-geometric
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env           # then edit values (DATABASE_URL, tokens, PUBLIC_BASE_URL)

# 4. Create the database + PostGIS, then run migrations
#    (in psql:  CREATE DATABASE bfp_capstone;  \c bfp_capstone  CREATE EXTENSION postgis;)
alembic upgrade head

# 5. Seed baseline data (optional but recommended for a fresh DB)
python seed_admin.py
python seed_barangays.py
python seed_personnel.py
python seed_incidents.py

# 6. Run the API
python run.py                    # http://127.0.0.1:8000  (interactive docs at /docs)
```

To run with multiple workers for CPU-bound route rebuilds:

```bash
WEB_CONCURRENCY=4 python run.py
```

> ⚠️ Multi-worker mode does **not** share WebSocket connections or in-memory reporter
> sessions across processes yet — see the note at the top of `run.py` before enabling it
> in production.

### Backend environment variables

| Variable            | Purpose                                                        |
|---------------------|----------------------------------------------------------------|
| `DATABASE_URL`      | PostgreSQL/PostGIS connection string                           |
| `JWT_SECRET`        | Secret used to sign auth tokens (**change from the default**)  |
| `PUBLIC_BASE_URL`   | Public tunnel URL used to build reporter location links        |
| `PHILSMS_API_TOKEN` | PhilSMS token for sending reporter SMS                          |
| `PHILSMS_SENDER_ID` | Registered PhilSMS sender name                                 |
| `SEND_SMS`          | `true` to actually send SMS (defaults to `false` / dry run)    |
| `WEB_CONCURRENCY`   | Uvicorn worker count (default `1`)                             |
| `ROUTING_POOL_SIZE` | Worker processes for offloaded route computation (default `2`) |

See `backend/.env.example` for the full list.

---

## Running the frontend

```bash
cd frontend
npm install

# Point the client at your backend
#   edit frontend/.env → VITE_API_BASE_URL=http://127.0.0.1:8000  (or your tunnel URL)

npm run dev        # start Vite dev server (default http://localhost:5173)
npm run build      # production build into dist/
npm run preview    # preview the production build
npm run lint       # ESLint
```

Log in with the admin account created by `seed_admin.py`.
