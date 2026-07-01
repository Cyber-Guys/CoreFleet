# CoreFleet — Dashboard

Fleet operations console for **CoreFleet**. Vue 3 (Composition API, `<script setup>`),
vue-router, Chart.js. Cyber/Tech control-room UI with five tabs: **Dashboard**
(active count, CLOUD/EDGE status, Cloud-vs-Edge chart, connected vehicles + live
speed), **Veicoli** (registry + a running trip's live telemetry), **Drivers**
(registry + "Genera report"), **Reports** (history), **About**.

## Stack

- **Vue 3** + Vite, `<script setup>` everywhere
- **vue-router** — Dashboard · Veicoli · Drivers · Reports · About
- **Chart.js** — doughnut (Cloud = orange, Edge = purple)
- Scoped CSS, design tokens in `src/assets/styles/theme.css`
- Type: Chakra Petch (display) · Inter (body) · JetBrains Mono (plates/telemetry)

## Run locally

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # production build -> dist/
```

## Docker

```bash
docker build -t corefleet-dashboard .
docker run -p 8080:80 corefleet-dashboard      # http://localhost:8080
```

Or via the repository's top-level stack (`docker compose up --build`), which also
starts the Zenoh router, fleet server and simulator. The dashboard is served at
**http://localhost:8080**.

## Structure

```
src/
├── main.js                 # app bootstrap
├── App.vue                 # shell: sidebar + topbar (search) + router-view
├── router/index.js         # Dashboard / Veicoli / Drivers / Reports / About routes
├── assets/styles/theme.css # design tokens, base, shared glow/pulse keyframes
├── data/mockData.js        # mock snapshot for the Dashboard KPI widgets
├── services/fleetApi.js    # API client: getActive/getVehicles/getDrivers/getReports/…
├── composables/useFleet.js # singleton store: mock KPIs + shared search query
├── components/
│   ├── AppSidebar.vue
│   ├── AppSearchBar.vue
│   ├── DriverReportCard.vue # renders a generated DriverReport (Drivers + Reports)
│   ├── ui/                 # BaseWidget, StatusDot, AppIcon
│   └── widgets/            # ActiveVehicles, Status, ModeChart, VehicleList (live)
└── views/                  # DashboardView, VehiclesView, DriversView, ReportsView, AboutView
```

## Data sources

- The **Dashboard** headline widgets (active count, CLOUD/EDGE status, Cloud-vs-Edge
  chart) run on a **mock store** (`useFleet` / `mockData.js`) for a lively feel.
- Everything else is **live** from the Jakarta service (`VITE_REPORT_API_URL`,
  default `http://localhost:9080`): connected vehicles + live telemetry
  (`/report/api/active`), registries (`/vehicles`, `/drivers`), on-demand reports
  (`/drivers/{did}/report`) and history (`/report`).

In Docker set `VITE_REPORT_API_URL=/report-api` to use the bundled nginx proxy.
`fleetApi.getSnapshot()` still has a stubbed `adaptZenoh()` for reading live fleet
state straight from the Zenoh router REST — an optional future path.

## Navigation & search

Detail selection is URL-addressable (`/vehicles?vid=…`, `/drivers?did=…`), so the
tabs cross-link: a vehicle's recent drivers → that driver, a driver's cars used →
that vehicle, a Dashboard row → that vehicle. The topbar search filters the current
tab (plate / driver name / id); no match shows **“Nessun risultato trovato.”**

## Accessibility / quality floor

Responsive to mobile (sidebar collapses to an icon rail), visible keyboard focus,
`prefers-reduced-motion` respected, semantic landmarks.

## Next

- Live map (Leaflet/MapLibre) from the `lat`/`lon` in `/report/api/active`.
- Persist registries/reports (currently in-memory in the service).
