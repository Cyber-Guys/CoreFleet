# CoreFleet dashboard

Operations console for CoreFleet, built with Vue 3 (Composition API, `<script setup>`), vue-router and Chart.js. It has five tabs:

- Dashboard: active vehicles, CLOUD/EDGE status, Cloud vs Edge chart, connected vehicles with live speed
- Veicoli: vehicle registry and live telemetry of running trips
- Drivers: driver registry and the "Genera report" button
- Reports: report history
- About

## Stack

- Vue 3 with Vite, `<script setup>` in every component
- vue-router for the five tabs
- Chart.js for the doughnut chart (Cloud orange, Edge purple)
- Scoped CSS, with design tokens in `src/assets/styles/theme.css`
- Fonts: Chakra Petch for headings, Inter for body text, JetBrains Mono for plates and telemetry

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

You can also start it with the whole stack from the repository root (`docker compose up --build`), which also runs the Zenoh router, fleet server, simulator and report service. The dashboard is at http://localhost:8080.

## Structure

```
src/
├── main.js                 # app bootstrap
├── App.vue                 # shell: sidebar + topbar (search) + router-view
├── router/index.js         # Dashboard / Veicoli / Drivers / Reports / About routes
├── assets/styles/theme.css # design tokens, base, shared glow/pulse keyframes
├── services/fleetApi.js    # API client: getActive/getVehicles/getDrivers/getReports/…
├── composables/useFleet.js # shared store: live fleet data + search query
├── components/
│   ├── AppSidebar.vue
│   ├── AppSearchBar.vue
│   ├── DriverReportCard.vue # renders a generated DriverReport (Drivers + Reports)
│   ├── ui/                 # BaseWidget, StatusDot, AppIcon
│   └── widgets/            # ActiveVehicles, Status, ModeChart, VehicleList
└── views/                  # DashboardView, VehiclesView, DriversView, ReportsView, NetworkAnalysisView, AboutView
```

## Data

All data comes from the Jakarta report service: connected vehicles and live telemetry (`/report/api/active`), registries (`/vehicles`, `/drivers`), reports (`/drivers/{did}/report`) and history (`/report`).

The app calls `/report-api` on its own origin. In Docker, nginx forwards it to the report service; with `npm run dev`, the Vite dev server does (`VITE_DEV_REPORT_URL`, see `.env.example`). Set `VITE_REPORT_API_URL` at build time only if the browser should call the report service at another URL.

## Navigation and search

The selected vehicle or driver is in the URL (`/vehicles?vid=…`, `/drivers?did=…`), so the tabs link to each other: from a vehicle's recent drivers to that driver, from a driver's cars to that vehicle, from a Dashboard row to that vehicle. The search bar filters the current tab by plate, driver name or id. With no match it shows "Nessun risultato trovato."

## Accessibility

The layout works on mobile (the sidebar collapses to icons), keyboard focus is visible, `prefers-reduced-motion` is respected and the page uses semantic landmarks.

## Next

- Live map (Leaflet or MapLibre) from the `lat`/`lon` in `/report/api/active`.
- Persist registries and reports (the service keeps them in memory today).
