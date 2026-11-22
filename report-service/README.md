# CoreFleet report service (Jakarta EE + LLM)

Jakarta EE 11 service on Open Liberty, written for Challenge 3. It started from the Eclipse o-cei [`hourglass-template`](https://gitlab.eclipse.org/eclipse-research-labs/o-cei-project/challenge-3-jakarta-ee-hourglass/hourglass-template) and uses langchain4j with OpenAI to:

1. map a domain and use case onto the Hourglass Model (the template's endpoint);
2. collect CoreFleet trips into vehicle and driver registries and write a report for each driver when asked, cached until the driver's data changes.

## Endpoints

Context root `/report`, JAX-RS application path `api`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/report/api/status` | Health and configured model (no secrets). |
| `POST` | `/report/api/trips` | Ingest a finished trip and update driver and vehicle stats. No LLM call. |
| `POST`/`GET` | `/report/api/active` | Who is driving now (vid to current driver), pushed by the fleet server. |
| `GET` | `/report/api/vehicles` · `/vehicles/{vid}` | Vehicle registry (km, trips, fuel and oil, lights, recent drivers). |
| `GET` | `/report/api/drivers` · `/drivers/{did}` | Driver registry (anagrafica, trips, km, infractions, averages, repeat offences). |
| `POST` | `/report/api/drivers/{did}/report` | Generate the driver's LLM report, or return the cached one. |
| `GET` | `/report/api/report` | History of generated reports (newest first). |
| `POST` | `/report/api/hourglass/analyze` | `{domain, useCase}` to `{stakeholders, capabilities, standardsGroups}`. |

`hourglass-model.http` has example requests for each endpoint.

## How it works

- Trips are ingested without calling the LLM and kept in an in-memory registry (`FleetStore`) with stats per driver and the state of each vehicle.
- A report is generated per driver when someone asks for it, then cached. The cache key is a hash of trips, km, infractions and average scores. If none of those changed, the stored report comes back with `cached: true` and no LLM call.
- `ChatModelProducer` builds a langchain4j `ChatModel` (OpenAI) from MicroProfile Config. The key comes from `openai.api-key`, which maps to the `OPENAI_API_KEY` environment variable, and is never compiled in.
- The platform computes the numbers (scores, counts, repeat offences, grade). The model writes the text and the Hourglass mapping.

## Configuration

| Env var | Default | Notes |
|---|---|---|
| `OPENAI_API_KEY` | (empty) | Required. Without it, calls to the model fail with HTTP 502. |
| `OPENAI_MODEL_NAME` | `gpt-4o-mini` | The template uses `gpt-5.5`; set it if your key has access. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Change it to use a proxy or a compatible API. |

## Run

### Docker (with the full stack)

From the repository root, put `OPENAI_API_KEY` in a `.env` file (git ignores it, see `.env.example`), then:

```bash
docker compose up --build
# service on http://localhost:9080/report/api/status
```

The fleet server posts every finished trip here (`INGEST_URL`) and pushes who is driving now (`ACTIVE_URL`). Reports are generated from the Drivers tab of the dashboard.

### Local (Maven + Open Liberty)

```bash
export OPENAI_API_KEY=sk-...
mvn package          # builds target/corefleet-report.war
mvn liberty:run      # serves on http://localhost:8080/report/api/status
```

The template targets Java 26 and Open Liberty 26. This module uses Java 17: it is the minimum for Jakarta EE 11 and the newest Java with an official Open Liberty image (`open-liberty:full-java17-openj9`).

## Limits

Reports are kept in memory (the last 50) and are lost on restart.
