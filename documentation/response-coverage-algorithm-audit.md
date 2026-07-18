# Response Coverage — Algorithm Audit & Defense Notes

**Purpose:** Document the algorithm behind the Response Coverage planning page, the
academic literature and industry standards that back it, and the known limitations
(with prepared answers) for the capstone defense.

**Source of truth:** `backend/coverage_engine.py` and the API wiring in
`backend/main.py` (`/api/coverage/*`, lines ~659–737).

---

## 1. Short answer

The Response Coverage page is a **network-based reachability isochrone + coverage-gap
analysis**. Under the hood it is a **multi-source Dijkstra shortest-path** from the
fire stations over the road graph, using travel-time edge weights, bucketed into
**3 / 5 / 8-minute bands**, then intersected with barangay boundaries to produce
per-barangay coverage percentages.

Every component rests on established, citable methods and standards. The single most
important defensible design choice is that coverage is measured along the **road
network** (real travel distance), **not** as a Euclidean circle around each station.

---

## 2. What the algorithm actually does (as implemented)

1. **Station → graph snap.** Each station with coordinates is snapped to its nearest
   road-network node within 2 km (`_station_source_nodes`, `main.py:668`).
2. **Multi-source Dijkstra.** `nx.multi_source_dijkstra_path_length` computes, for
   every reachable node, the **minimum travel time from the nearest station**, cut off
   at the widest band (8 min). Edge weights are the *same constraint-aware travel-time
   costs the router uses*; blocked roads (∞ cost) are treated as impassable
   (`coverage_engine.py:118`).
3. **Band bucketing.** Each reachable road segment is assigned to the tightest time
   band its slower endpoint falls in (≤3 ⊂ ≤5 ⊂ ≤8 minutes).
4. **Isochrone polygons.** Each band's reachable road lines are merged (`linemerge`),
   buffered ~40 m, and unioned into a filled "coverage blob" that follows the road
   corridors rather than a naive circle. (Merging before buffering makes the buffer
   ~10× cheaper.)
5. **Per-barangay coverage %.** Each band polygon is intersected with each barangay
   boundary; coverage % = intersected area ÷ barangay area, classified
   **covered ≥ 80% / partial ≥ 40% / gap < 40%**, sorted worst-covered first.

**Characterization:** a network-distance **service-area / closest-facility** analysis
producing a descriptive **coverage map** — not a Euclidean buffer, and not (yet) an
optimization model.

---

## 3. Literature & standards backing the approach

### 3.1 Core method — shortest path + service areas
- **Dijkstra (1959)** — the shortest-path algorithm itself. The multi-source variant
  is the standard "closest facility / service area" formulation used in GIS network
  analysis (e.g., ArcGIS Network Analyst Service Areas, pgRouting driving-distance).
- Network-based accessibility is well-documented as **more accurate than circular
  buffers** for emergency services, because travel follows the road network.

### 3.2 Coverage as a formal concept (strongest academic anchor)
- **Toregas, Swain, ReVelle & Bergman (1971)** — the **Location Set Covering Problem
  (LSCP)**: cover all demand within a time/distance standard.
- **Church & ReVelle (1974)** — the **Maximal Covering Location Problem (MCLP)**:
  maximize demand covered within a response-time standard.

Our per-barangay "% covered within N minutes" is a direct, descriptive instance of the
MCLP coverage concept. This subfield — **emergency facility location / covering
models** — is the academic home of the feature.

### 3.3 Why 3 / 5 / 8 minutes — response-time standards
- **NFPA 1710** (career departments): 60 s turnout + **240 s (4 min) travel** for the
  first engine, and **480 s (8 min) travel** for the full first-alarm assignment,
  measured at the 90th percentile. Our **5-min and 8-min bands map directly onto
  NFPA 1710 travel benchmarks**; the 3-min band is a stricter internal tier.
- **NFPA 1720** (volunteer/combination departments) — demand-zone-based response goals.
- **CFAI** (Commission on Fire Accreditation International) and the **ISO Fire
  Suppression Rating Schedule** (classic 1.5-mile engine / 2.5-mile ladder distance
  coverage) — additional precedents for standard-based coverage.
- The 8-minute figure aligns with the empirical **flashover window** (~8 min) — the
  physical reason response time matters and why fire-loss/casualty studies find
  outcomes worsen as response time grows.

**Defense framing:** *"We didn't invent a threshold — the bands are grounded in
NFPA 1710 travel-time benchmarks, and the coverage concept is the Maximal Covering
Location Problem from emergency-services operations research."*

---

## 4. Known limitations & prepared answers

Raise these first — it reads as rigor, not weakness.

1. **Coverage is measured by land _area_, not population or structures.**
   Fire risk tracks people and buildings, not hectares. A large, sparsely-populated
   barangay can read as a "gap" that barely matters, and vice-versa. MCLP normally
   weights demand.
   **Answer:** deliberate v1 simplification; the defensible upgrade is population- or
   building-count-weighted coverage (data permitting).

2. **The 80% / 40% status thresholds are internal conventions, not a standard.**
   NFPA compliance is judged at the **90th percentile of actual incident times**, not
   % of area.
   **Answer:** frame 80/40 as planning tiers for visual triage; can be re-anchored to
   a 90% target to be NFPA-aligned.

3. **Bands are pure travel time** — dispatch/turnout/setup excluded. NFPA totals
   include ~60 s turnout.
   **Answer:** we model station-to-scene travel; add a fixed turnout offset for
   NFPA-comparable totals.

**Lesser caveats (one line each):**
- Free-flow constraint-aware speeds — no live or time-of-day traffic.
- Nearest-station only — does not model a station being busy on another call (the
  "backup coverage" / reliability extension, **BACOP**, exists if asked).
- The ~40 m road buffer makes area % approximate — a planning aid, not a survey
  boundary.
- Static demand (fixed barangay boundaries); stations snapped within 2 km.

---

## 5. One-line defense summary

> "Response Coverage is a network-based service-area analysis: a multi-source Dijkstra
> from every station over real road travel-times, bucketed into NFPA 1710-aligned
> 3/5/8-minute bands, then scored per barangay as a descriptive Maximal-Covering-style
> gap map. It uses the same constraint-aware costs as the router, so what it shows is
> honestly what a truck can traverse."

---

## 6. References

- Dijkstra, E. W. (1959). *A note on two problems in connexion with graphs.*
  Numerische Mathematik, 1, 269–271.
- Toregas, C., Swain, R., ReVelle, C., & Bergman, L. (1971). *The location of emergency
  service facilities.* Operations Research, 19(6), 1363–1373.
- Church, R., & ReVelle, C. (1974). *The maximal covering location problem.* Papers in
  Regional Science, 32(1), 101–118.
- National Fire Protection Association. *NFPA 1710: Standard for the Organization and
  Deployment of Fire Suppression Operations, EMS, and Special Operations to the Public
  by Career Fire Departments.*
- National Fire Protection Association. *NFPA 1720: Standard for … by Volunteer Fire
  Departments.*
- Commission on Fire Accreditation International (CFAI). *Standards of Cover.*
- Insurance Services Office (ISO). *Fire Suppression Rating Schedule.*

*(Note: verify edition years / page numbers against the copies cited in your paper's
bibliography before submission.)*
