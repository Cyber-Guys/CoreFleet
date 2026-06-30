# CoreFleet SDV — Dashboard

Fleet operations console for **CoreFleet SDV**. Vue 3 (Composition API, `<script setup>`),
vue-router, Chart.js. Cyber/Tech control-room UI: live vehicle count, CLOUD/EDGE
transmission status, a Cloud-vs-Edge split chart, and a searchable vehicle registry.

## Stack

- **Vue 3** + Vite, `<script setup>` everywhere
- **vue-router** — Dashboard · Reports · About Us
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
├── router/index.js         # Dashboard / Reports / About routes
├── assets/styles/theme.css # design tokens, base, shared glow/pulse keyframes
├── data/mockData.js        # mock snapshot (mirrors the server's data shape)
├── services/fleetApi.js    # data seam — mock now, Zenoh REST later
├── composables/useFleet.js # singleton store: state, search filter, live ticker
├── components/
│   ├── AppSidebar.vue
│   ├── AppSearchBar.vue
│   ├── ui/                 # BaseWidget, StatusDot, AppIcon
│   └── widgets/            # ActiveVehicles, Status, ModeChart, VehicleList
└── views/                  # DashboardView, ReportsView, AboutView
```

## Data: mock → live

All data flows through `src/services/fleetApi.js`. Today `getSnapshot()` returns
mock data; the shape matches the fleet server (`vid`, `mode`, `profile`, `eco`,
`safety`, `lat`, `lon`). To go live:

1. Set `VITE_USE_MOCK=false` and `VITE_FLEET_API_URL` (e.g. `/fleet-api` to use the
   bundled nginx proxy to the Zenoh router's REST API on `:8000`).
2. Implement `adaptZenoh()` to map `core/fleet/**` samples into the snapshot shape.

No component changes are needed — they only read the store.

## Search

The topbar search filters the vehicle registry by **plate (targa)** or **driver
profile**, case-insensitive. With no match it shows **“Nessun risultato trovato.”**

## Accessibility / quality floor

Responsive to mobile (sidebar collapses to an icon rail), visible keyboard focus
on the search field, `prefers-reduced-motion` respected, semantic landmarks.

## Next

- Live map (Leaflet/MapLibre) from `lat`/`lon` — the data is already in the store.
- Wire `adaptZenoh()` to the router REST endpoint.
- Surface the server's bandwidth/energy-saved stats as a KPI strip.
