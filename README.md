# CoreFleet

**Adaptive cloud–edge fleet telemetry over Eclipse Zenoh, with LLM-generated driving reports.**

CoreFleet is a hackathon project for the [CEI-Sphere Hackathon — Code the Continuum](https://ceisphere.eu/events/code-continuum). It combines **Challenge 1 (Eclipse Zenoh & Sustainable Edge-Cloud)** and **Challenge 3 (Jakarta EE, AI & the Hourglass Model)** into a single, coherent product.

---

## 1. The Concept

CoreFleet is a fictional **taxi-sharing / car-sharing startup**. We own the vehicles and lease them to drivers (taxi operators or subscribers). Every car carries an **IoT edge device** (OBD2 reader + accelerometer + GPS) that streams live telemetry back to our platform.

The platform must scale to a large, growing fleet **without saturating the network or wasting energy**. To do that, it continuously chooses, per the current network pressure, *how* each vehicle should transmit:

- **`CLOUD` mode**: the device streams raw telemetry every second. The server does all the processing. Maximum fidelity, maximum bandwidth.
- **`EDGE` mode**: once the channel saturates, the server moves the **overflow vehicles** (newest first) to aggregate locally and send a compact summary every 15 seconds instead. Drastically lower bandwidth and transmission energy, at the cost of temporal resolution.

The server arbitrates this trade-off in real time, **per vehicle**, so the fleet settles into a hybrid mix — as many cars in CLOUD as the channel can carry, the rest on EDGE. A web app shows the connected fleet with **live telemetry** plus vehicle and driver registries; **on demand**, an **LLM-backed Jakarta EE service** produces a structured report on how each **driver** drives and treats the company's cars.

This directly mirrors the Challenge 1 narrative: *comparing "cloud-only" vs "edge-accelerated" deployments and measuring bandwidth/energy savings*, while the driver reports fulfil Challenge 3.

---

## 2. Why It Matters

The core insight of the cloud–edge continuum is that **moving computation toward the data source reduces the volume that must travel across the network**, which reduces both bandwidth cost and transmission energy. CoreFleet makes this tangible:

- It **measures** the bytes/second produced in each mode and estimates the transmission energy saved (`JOULES_PER_MB`).
- It **adapts automatically**: the system is not statically "cloud" or "edge", it shifts along the continuum based on live load.
- It keeps a **defensible separation of concerns**: physically-grounded numbers come from the telemetry pipeline; the LLM only writes the human-facing narrative on top of those numbers.

---

## 3. Architecture

```mermaid
flowchart LR
    subgraph Vehicles["Fleet (edge devices)"]
        V1["Vehicle agent\nOBD2 + GPS + IMU"]
        V2["Vehicle agent"]
        Vn["Vehicle agent ..."]
    end

    subgraph Bus["Eclipse Zenoh"]
        R(("Zenoh router\ntcp:7447 / rest:8000"))
    end

    subgraph Backend["Platform"]
        S["Fleet server\n(subscriber + controller)"]
        J["Jakarta EE service\nregistries + LLM reports"]
    end

    W["Web app\nDashboard / Veicoli / Drivers / Reports"]

    V1 -- raw / summary --> R
    V2 -- raw / summary --> R
    Vn -- raw / summary --> R
    R -- mode (CLOUD/EDGE) --> V1
    R -- mode --> V2
    R -- mode --> Vn
    R --> S
    S -- mode decisions --> R
    S -- trip ingest + live active --> J
    W -- REST --> J
```

### Components

| Component | Path | Role | Status |
|---|---|---|---|
| **Shared library** | `corefleet/` | Zenoh protocol (keys, modes, codec) + `VehicleClient`, imported by both vehicle and server. | ✅ |
| **Fleet simulator** | `fleet_simulator/` | Simulates **cars** (assets) + **drivers** (people) + **trips**; each active trip is an agent streaming OBD2/GPS over Zenoh. | ✅ |
| **Zenoh router** | `zenoh_router/` | Dockerized Eclipse Zenoh router (wire `:7447`, REST `:8000`). | ✅ |
| **Fleet server** | `zenoh_router/subscriber/fleet_server.py` | Subscribes to telemetry, detects congestion, publishes mode decisions, scores each trip and ingests it into the registry service. | ✅ |
| **Dashboard** | `webapp/` | Vue 3 control-room UI: Dashboard, **Veicoli**, **Drivers**, **Reports** (history), About. | ✅ |
| **Jakarta EE + LLM service** | `report-service/` | Open Liberty + langchain4j; vehicle & driver registries, on-demand cached driver reports, Hourglass mapping. | ✅ |
| **Live map** | _planned_ | Fleet positions (Leaflet / MapLibre) fed from `lat`/`lon`. | ⏳ |

---

## 4. Zenoh Protocol

`vid` = vehicle id (the licence plate). All keys live under the `core/fleet` namespace.

| Key expression | Direction | Payload | Mode | Notes |
|---|---|---|---|---|
| `core/fleet/{vid}/alive` | Vehicle → Server | _liveliness token_ | — | Declared on ignition. Auto-undeclared (DELETE sample) on disconnect → free crash detection. |
| `core/fleet/{vid}/raw` | Vehicle → Server | JSON telemetry | `CLOUD` | One sample per second. |
| `core/fleet/{vid}/summary` | Vehicle → Server | JSON aggregate | `EDGE` | One sample per 15-second window. |
| `core/fleet/{vid}/session` | Vehicle → Server | JSON aggregate | — | Final full-session aggregate, published once on trip end; triggers the trip ingest into the registries. |
| `core/fleet/{vid}/mode` | Server → Vehicle | `"CLOUD"` \| `"EDGE"` | — | **Per-vehicle** mode. The server assigns each car CLOUD or EDGE independently so the fleet runs a **hybrid mix**. Exposed as a **queryable** (`core/fleet/*/mode`) so a vehicle joining mid-run reads its own current value, then subscribes to it for changes. |

The server subscribes with wildcards: `core/fleet/*/raw`, `core/fleet/*/summary`, `core/fleet/*/session`, `core/fleet/*/alive`, so it scales to any number of vehicles without per-vehicle subscription bookkeeping. The end-of-trip ingest is triggered by the `session` payload (an explicit end-of-drive event), so it is independent of liveliness-message ordering.

Every payload also carries the **driver** taking the trip (`did`, `driver_name`) and the **trip id** (`trip_id`). The final `session` payload additionally carries the driver's anagrafica (`driver_surname`, `driver_cf`, `driver_nationality`) and a `vehicle` snapshot (`odo_km`, `fuel_pct`, `oil_pct`, `lights`) — the data the registries are built from.

> **Design notes / improvements over a naïve design**
> - **Liveliness tokens** instead of a manual `alive`/`dead` message pair: presence is tracked by Zenoh itself, so a device that crashes or loses connectivity is detected automatically.
> - **`vid` lives in the key path**, not the payload, so subscribers can filter and store per-vehicle by key expression.
> - Each `core/fleet/{vid}/mode` key is **queryable / retained** so a late-joining vehicle learns *its own* assigned mode immediately, before the next control tick.
> - JSON is used for the v1 demo; a **CBOR / protobuf** encoding is planned to quantify the bandwidth win.

---

## 5. Adaptive CLOUD ↔ EDGE Logic (per-vehicle hybrid)

The channel is not flipped globally. Instead the server **fills the channel with CLOUD up to a saturation target, then offloads the overflow to EDGE** — so at any moment the fleet is a *hybrid mix* of both modes rather than all-one-or-the-other. On every control tick it recomputes how many vehicles the channel can afford to keep in CLOUD:

```
avg_raw_bytes = live EWMA of observed raw-payload size
max_cloud     = max(1, ⌊ BW_LIMIT_BYTES_S × CLOUD_SATURATION / (avg_raw_bytes × CLOUD_HZ) ⌋)

vehicles sorted by join order (oldest first):
    the first  max_cloud  → CLOUD   (1 Hz raw telemetry)
    the rest              → EDGE    (15 s aggregate)
```

So the channel is filled to `CLOUD_SATURATION` (default `0.8` = 80 %) of `BW_LIMIT_BYTES_S`, and **older vehicles keep CLOUD priority** — a newly-joined car is the first to be pushed to EDGE when the channel saturates, and is promoted back to CLOUD as soon as an older trip ends and frees capacity. Each change is published on that vehicle's own `core/fleet/{vid}/mode` key. `avg_raw_bytes` is measured live from real payloads, so the split tracks the actual byte rate, not a guess.

*Example (`BW_LIMIT_BYTES_S=3000`, `CLOUD_SATURATION=0.8`, `avg_raw≈248 B`):* up to ~9 vehicles stay CLOUD; with 15 active the split settles at **9 CLOUD + 6 EDGE** — `MODE reassign: 9 cloud + 6 edge (max_cloud=9, avg_raw=248B)`.

Energy saved is estimated as `bytes_saved / 1e6 × JOULES_PER_MB` against an all-CLOUD baseline — the headline metric for the Challenge 1 comparison, printed every `STATS_INTERVAL_S` seconds as a `[stats] cloud=… edge=… active=…` line. Everything is configurable via environment variables (`BW_LIMIT_BYTES_S`, `CLOUD_SATURATION`, `JOULES_PER_MB`).

Two aggregation scopes are maintained per trip:

- a **rolling 15-second window** aggregate, transmitted and reset while the vehicle is in `EDGE` mode;
- a **full-session** aggregate, accumulated for the whole trip and used for the end-of-trip ingest that feeds the driver/vehicle registries.

With only a few cars the whole fleet stays **CLOUD** (live 1 Hz telemetry on the dashboard); lower `BW_LIMIT_BYTES_S`, raise `MAX_VEHICLES`, or let the built-in demand cycle (`DEMAND_PERIOD_S`) push more cars on the road to watch the hybrid split — and the bandwidth/energy drop — appear.

---

## 6. Telemetry Data Model

### `raw` sample (CLOUD mode) — OBD2 PIDs + augmented GPS

| Field | Source | Unit |
|---|---|---|
| `vid`, `t` | — | id, seconds |
| `did`, `driver_name`, `trip_id` | trip | driver (person) + trip id |
| `speed_kmh` | PID 0x0D | km/h |
| `rpm` | PID 0x0C | rpm |
| `throttle` | PID 0x11 | % |
| `load` | PID 0x04 | % |
| `coolant_c` | PID 0x05 | °C |
| `fuel_lph` | PID 0x5E | L/h |
| `lat`, `lon` | GPS | deg |
| `limit_kmh` | map (augmented) | km/h |

The driver id/name ride on every sample so the server can serve **who is driving now** live (see `/report/api/active`).

### `summary` aggregate (EDGE window / end-of-trip session)

Distance, duration, average & max speed, average rpm, fuel used, L/100 km, and **driving-quality counters**: harsh accelerations, harsh braking, over-rev seconds, cold-engine over-rev seconds, idle seconds, speeding seconds.

The final `session` payload additionally carries the driver's anagrafica (`driver_surname`, `driver_cf`, `driver_nationality`) and a **vehicle snapshot** (`odo_km`, `fuel_pct`, `oil_pct`, `lights`) — the fields the registries are built from.

These counters are derived from physically-grounded thresholds (see `fleet_simulator/config.py`) so the downstream scores rest on real signals rather than on the LLM inventing numbers. Speeding still lowers the safety score, but a **multa** (fine) is only recorded for *sustained* speeding that gets *caught* (`FINE_MIN_SPEEDING_S`, `FINE_CATCH_RATE`).

---

## 7. Cars, Drivers & Trips

CoreFleet models the business literally:

- **Cars** are assets. The fleet starts with a batch and grows over the run. A car has an odometer, fuel and oil levels and warning lights that **persist across trips** (and is refuelled/serviced at the depot when low).
- **Drivers** are people, and they **churn**: new customers arrive continuously, and a satisfied one may **reconfirm** for a later trip (a bad experience — the car handed back with warning lights — makes them less likely to return). A returning driver rotates across different cars. Each driver has an anagrafica (nome, cognome, codice fiscale, nazionalità) and a baseline driving style. Tuned by `RECONFIRM_RATE` / `SATISFACTION_RATE`.
- A **trip** = a driver taking an available car for a finite drive. On end, both return to their pools; the same driver may later take another car.

The OBD2 device lives on the **car** (it is the telemetry source), but scoring and reporting are about the **driver** — that's the real product value (insurance/coaching follow the person).

## 8. Registries & Driver Reports (Challenge 3: Jakarta EE + LLM)

The Jakarta service (`report-service/`, Open Liberty + langchain4j, built from the Eclipse [`hourglass-template`](https://gitlab.eclipse.org/eclipse-research-labs/o-cei-project/challenge-3-jakarta-ee-hourglass/hourglass-template)) is the **platform API**. Each finished trip is **ingested** (no LLM); reports are generated **on demand, per driver, and cached**.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/report/api/trips` | Ingest a finished trip → update driver + vehicle stats. No LLM. |
| `POST`/`GET` | `/report/api/active` | Live "who is driving now" **+ live telemetry** (speed, rpm, throttle, fuel, position) per vehicle; pushed by the server every ~2s, read by the dashboard. |
| `GET`  | `/report/api/vehicles` · `/vehicles/{vid}` | Vehicle registry: km totali, n° trip, carburante/olio, spie, ultimi conducenti. |
| `GET`  | `/report/api/drivers` · `/drivers/{did}` | Driver registry: anagrafica, viaggi, km, multe/infrazioni, medie, recidivo. |
| `POST` | `/report/api/drivers/{did}/report` | Generate (or return **cached**) the driver's LLM report. Returns the prose fast; kicks off the image job in the background. |
| `GET`  | `/report/api/drivers/{did}/report/image` | Poll the driver's generated **Hourglass image** → `{status: pending\|ready, imageUrl}`. |
| `GET`  | `/report/api/report` | History of generated reports. |
| `POST` | `/report/api/hourglass/analyze` | The template's generic Hourglass mapping (`{domain, useCase}`). |
| `GET`  | `/report/api/status` | Health + configured model (no secrets). |

**Caching**: a driver's report is regenerated only when their data changed since last time — the cache key is a hash of `trips + km + infractions + average scores`. Identical data ⇒ the stored report is returned with `cached: true` and **no LLM call**.

**Deterministic vs narrative**: the platform owns the numbers (scores, counts, recidivist behaviours, trend, grade); the **LLM only writes the prose** and the Hourglass mapping (stakeholders / capabilities-waist / standards groups). Reproducible and easy to defend. A **multa** additionally applies a fixed safety-score penalty (`REPORT_FINE_SAFETY_PENALTY`, default 25) — a deterministic hit, not an LLM opinion.

**Async Hourglass image**: alongside the report the service generates a per-driver illustrative image via the OpenAI **Responses API** `image_generation` tool (`OPENAI_IMAGE_MODEL`, default `gpt-5-mini`). Image generation is slow (~30–60 s), so `POST …/report` returns the prose immediately and submits the image on a background executor; the dashboard shows a spinner and polls `…/report/image` until it returns `status: ready` with a `data:image/png;base64,…` URL. The call goes over a raw `HttpClient` pinned to **HTTP/1.1** (OpenJ9 HTTP/2 hangs) and is idempotent per driver.

The OpenAI key is read from the **`OPENAI_API_KEY`** environment variable (via a gitignored `.env`); it is never committed. See `report-service/README.md`.

---

## 9. Repository Structure

```
.
├── corefleet/                  # Shared library (vehicle + server)
│   ├── protocol.py             # Key expressions, Mode enum, JSON codec
│   └── client.py               # VehicleClient: liveliness, mode, publishers
├── fleet_simulator/            # Cars + drivers + trips simulator
│   ├── __main__.py             # Entry point: python -m fleet_simulator
│   ├── config.py               # Physical constants, driver profiles, thresholds
│   ├── fleet_simulator.py      # Runner: car/driver pools + trip scheduler
│   ├── agent.py                # VehicleAgent: one trip's physics + Zenoh loop
│   ├── vehicle_simulator.py    # Per-trip physics + raw/window/session payloads
│   ├── Dockerfile
│   └── types/                  # driver_profile, driver, vehicle_state, edge_aggregate
├── zenoh_router/
│   ├── docker-compose.yaml     # Standalone router (router only)
│   └── subscriber/
│       ├── fleet_server.py     # Subscriber + congestion controller + trip ingest
│       └── Dockerfile
├── report-service/             # Jakarta EE 11 + langchain4j (Challenge 3)
│   ├── src/main/java/dukes/    # fleet/ (registries, reports) + hourglass/ + ai/
│   └── Dockerfile              # Maven build -> Open Liberty (Java 17)
├── webapp/                     # Vue 3 dashboard (Dashboard/Veicoli/Drivers/Reports)
├── docker-compose.yaml         # Full stack: router + server + sim + report + webapp
├── .env.example                # OPENAI_API_KEY lives in a gitignored .env
├── requirements.txt
└── README.md
```

---

## 10. Getting Started

### Prerequisites
- Docker + Docker Compose (Python 3.13 / Java 17 images)
- Or, for local runs: Python 3.10+ and `pip install -r requirements.txt`

### Full stack (recommended)

Provide your OpenAI key for the report service (kept out of git):

```bash
cp .env.example .env        # then edit .env and set OPENAI_API_KEY
docker compose up --build
```

This brings up the router, fleet server, simulator, **report service** and
**dashboard**. The simulator starts with a batch of cars and grows the fleet;
new customers arrive continuously and take cars for finite trips. Watch the
`fleet-server` logs for the bandwidth/energy `[stats]` lines and `trip … ingested`
lines — each finished trip updates the driver/vehicle registries. Open the
dashboard: the **Veicoli** tab shows a running trip's **live telemetry**, and on the
**Drivers** tab you can pick a driver and press **Genera report**.

- Dashboard: **http://localhost:8080**
- Report service: **http://localhost:9080/report/api/status**
- Live "who's driving now": `…/report/api/active` · Drivers / Vehicles: `…/report/api/drivers` · `…/report/api/vehicles`
- Router REST: **http://localhost:8000** (`core/fleet/**`)

With a few cars the whole fleet runs in **CLOUD**, so the dashboard shows live 1 Hz
telemetry (speed/rpm/throttle/fuel) for a running trip. As more cars come on the road
(raise `MAX_VEHICLES`, or wait for the demand cycle peak) the channel saturates and the
newest vehicles are pushed to **EDGE** — you'll see `MODE reassign: N cloud + M edge`
in the logs, the `[stats] cloud=… edge=…` split, the bandwidth/energy drop, and those
cars' telemetry become coarser (15 s window aggregates). Lower `BW_LIMIT_BYTES_S`
(e.g. `1800`) or `CLOUD_SATURATION` to force the split with fewer cars.

Tunables live in `docker-compose.yaml`: `START_VEHICLES`, `MAX_VEHICLES`,
`SPAWN_INTERVAL_S`, `TRIP_MIN_S`/`TRIP_MAX_S`, `RECONFIRM_RATE`,
`SATISFACTION_RATE`, `DEMAND_PERIOD_S`, `DEMAND_MIN`, `DURATION_S` (simulator);
`BW_LIMIT_BYTES_S`, `CLOUD_SATURATION`, `JOULES_PER_MB`, `FINE_MIN_SPEEDING_S`,
`FINE_CATCH_RATE`, `ACTIVE_INTERVAL_S`, `STATS_INTERVAL_S` (server);
`OPENAI_MODEL_NAME`, `OPENAI_IMAGE_MODEL`, `REPORT_FINE_SAFETY_PENALTY` (report).

### Distributed deployment (split across machines)

The stack also runs **spread over several PCs** — the Challenge 1 "continuum" story. No
host or IP is hardcoded in source: every cross-service URL in `docker-compose.yaml` is a
`${VAR:-default}` that falls back to a compose service name on a single host. To split,
copy the file to each machine, set the peers' IPs in a `.env` (see `.env.example`), and
start only the services that live there:

```bash
# Laptop B — Zenoh router
docker compose up zenoh-router

# Laptop A — simulator (points at B)
ZENOH_ROUTER=tcp/<B-IP>:7447 docker compose up fleet-simulator

# Laptop C — backend + UI (point at B)
ZENOH_ROUTER=tcp/<B-IP>:7447 ZENOH_REST_URL=http://<B-IP>:8000 \
  docker compose up fleet-server fleet-report fleet-webapp
```

The browser always talks to the webapp's own **nginx**, which reverse-proxies
`/report-api` → the report service and the Zenoh REST endpoint (upstreams injected via
`REPORT_SERVICE_URL` / `ZENOH_REST_URL` with `envsubst`), so the frontend has no backend
host baked into the bundle and works identically on one host or many.

### Run components locally

```bash
python -m venv .venv && source .venv/bin/activate   # fish: source .venv/bin/activate.fish
pip install -r requirements.txt

# 1) router only
docker compose -f zenoh_router/docker-compose.yaml up

# 2) server  (new shell, from repo root)
ZENOH_ROUTER=tcp/localhost:7447 PYTHONPATH=. python zenoh_router/subscriber/fleet_server.py

# 3) simulator (new shell, from repo root)
ZENOH_ROUTER=tcp/localhost:7447 python -m fleet_simulator
```

---

## 11. Roadmap

- [x] **Simulator over Zenoh** — liveliness, `mode` query/subscribe, `raw`/`summary`/`session` publish.
- [x] **Fleet server / controller** — wildcard subs, **per-vehicle hybrid** CLOUD/EDGE control (fill to `CLOUD_SATURATION`, overflow → EDGE), per-vehicle mode queryable, per-trip scoring + ingest, bandwidth/energy stats.
- [x] **Cars + drivers + trips** — asset pool, driver **churn** (new customers + reconfirms), finite trips, drivers rotating across cars, per-car fuel/oil/odometer/lights.
- [x] **Live telemetry** — "who's driving now" + speed/rpm/throttle/fuel per running trip; cross-links between vehicles ↔ drivers.
- [x] **Jakarta registries + reports** — vehicle & driver stats, on-demand **cached** driver reports, history, Hourglass mapping (langchain4j + OpenAI).
- [x] **Async Hourglass image** — per-driver illustrative image via the OpenAI Responses `image_generation` tool, generated on a background executor and polled by the dashboard.
- [x] **Distributed deployment** — split across machines via `.env` IP overrides + webapp nginx reverse-proxy, no host baked into source.
- [x] **Vue 3 dashboard** — Dashboard, Veicoli (live trip), Drivers (with "Genera report"), Reports history.
- [x] **Full Docker stack** — router + server + simulator + report service + dashboard.
- [ ] **Live map** — fleet positions from `lat`/`lon` (Leaflet/MapLibre).
- [ ] **Persistence** — registries + reports survive a restart (currently in-memory).
- [ ] **Compact encoding** — CBOR/protobuf variant to measure the real bandwidth win.

---

## Appendix — Hackathon Challenges

### CEI-Sphere Hackathon — Code the Continuum

> Code the Continuum brings together students, developers, researchers, innovators, open-source communities, pilot teams and solution providers for two days of hands-on collaboration around the cloud-edge-IoT continuum.
>
> The event creates a practical space for experimentation, co-creation and exchange, where participants will work on real challenges related to open technologies, interoperability and the reuse of assets across large-scale pilot environments.

#### First Challenge - O-CEI: Eclipse Zenoh & Sustainable Edge-Cloud

> Participants will explore how Eclipse Zenoh can support energy-aware edge-cloud applications by comparing "cloud-only" and "edge-accelerated" deployments. Through hands-on experimentation, they will measure how optimising data flows across the continuum can reduce bandwidth usage and contribute to lower energy consumption.

- **Concrete scenarios**:
  + **Challenge 1.A**: Distributed image processing with Zenoh, comparing cloud vs edge execution.
  + **Challenge 1.B**: Geo-distributed content delivery using Zenoh and SkyFlok, comparing traffic across edge and cloud.
- **Task**: Install Zenoh client libraries (e.g. Python or Rust), run demo repositories, adapt them with your own data, and compare edge vs cloud configurations.
- **Inputs**: Example source code and demo repositories (GitHub).
- **Expected demo (Definition of Done)**: At least one scenario running successfully, with visible Zenoh message exchanges and a short explanation of results.
- **Skills**: Programming (Python, Rust, C/C++), basic networking and distributed systems knowledge.
- **Requirements**: Laptop (Windows, Ubuntu or macOS) capable of running Zenoh demos and installing development tools.
- **Mentors**: Software engineers from ZettaScale.

#### Third Challenge - ECLIPSE FOUNDATION: Jakarta EE, AI & the Hourglass Model

> Proposed by the Eclipse Foundation, this challenge invites participants to design and implement a Jakarta EE application that models and analyses enterprise domains using the [Hourglass Model](https://ceisphere.eu/hourglass-model). The mapping will be supported by an external Large Language Model (LLM), integrated through modern AI engineering and agentic techniques.

- **Concrete scenario**: Generate the Hourglass Model for a given domain and use case.
- **Task**: Design and implement a Jakarta EE application that models and analyses enterprise domains using the Hourglass Model, supported by an external LLM and agentic tools.
- **Inputs**: Skeleton project, OpenAI API key, starter guides and links to relevant resources.
- **Expected demo (Definition of Done)**: A complete, runnable Jakarta EE project.
- **Skills**: Java, Maven and general knowledge of agentic AI techniques.
- **Mentor**: Ivar Grimstad, Jakarta EE Developer Advocate, Eclipse Foundation.
