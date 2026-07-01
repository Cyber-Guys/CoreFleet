# CoreFleet Hourglass Report Service (Jakarta EE + LLM)

Jakarta EE 11 (Open Liberty) service that completes **Challenge 3**. Built from the
Eclipse o-cei [`hourglass-template`](https://gitlab.eclipse.org/eclipse-research-labs/o-cei-project/challenge-3-jakarta-ee-hourglass/hourglass-template),
it uses **langchain4j** + OpenAI to:

1. map a domain/use case onto the **Hourglass Model** (the template's endpoint), and
2. accumulate CoreFleet **trips** into vehicle & driver registries and generate a
   structured, **on-demand cached** report per **driver**.

## Endpoints

Context root `/report`, JAX-RS application path `api`.

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/report/api/status` | Health + configured model (no secrets). |
| `POST` | `/report/api/trips` | Ingest a finished trip → update driver + vehicle stats. **No LLM.** |
| `POST`/`GET` | `/report/api/active` | Live "who is driving now" (vid → current driver), pushed by the fleet server. |
| `GET`  | `/report/api/vehicles` · `/vehicles/{vid}` | Vehicle registry (km, trips, fuel/oil, lights, recent drivers). |
| `GET`  | `/report/api/drivers` · `/drivers/{did}` | Driver registry (anagrafica, trips, km, infractions, averages, recidivist). |
| `POST` | `/report/api/drivers/{did}/report` | Generate **or return cached** the driver's LLM report. |
| `GET`  | `/report/api/report` | History of generated reports (newest first). |
| `POST` | `/report/api/hourglass/analyze` | `{domain, useCase}` → `{stakeholders, capabilities, standardsGroups}`. |

See `hourglass-model.http` for ready-to-run examples.

## How it's wired

- Trips are **ingested** (no LLM) and accumulated in an in-memory registry
  (`FleetStore`): per-driver stats + per-vehicle asset state.
- Reports are generated **on demand, per driver**, and **cached**: the cache key is a
  hash of `trips + km + infractions + average scores`. Unchanged data ⇒ the stored
  report is returned with `cached: true` and **no LLM call**.
- `ChatModelProducer` builds a langchain4j `ChatModel` (OpenAI) from MicroProfile
  Config; the key comes from `openai.api-key` ← **`OPENAI_API_KEY`** env, never compiled in.
- The platform owns the numbers (scores, counts, recidivist, grade); the model writes
  only the narrative + the Hourglass mapping.

## Configuration

| Env var | Default | Notes |
|---|---|---|
| `OPENAI_API_KEY` | _(empty)_ | Required. A missing key returns HTTP 502 at call time. |
| `OPENAI_MODEL_NAME` | `gpt-4o-mini` | Template uses `gpt-5.5`; set this if your key has access. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Override for a proxy/compatible API. |

## Run

### Docker (part of the full stack)

From the repo root, put `OPENAI_API_KEY` in a gitignored `.env` (see `.env.example`), then:

```bash
docker compose up --build
# service on http://localhost:9080/report/api/status
```

The fleet server posts every finished trip here automatically (`INGEST_URL`) and
pushes the live "who's driving now" map (`ACTIVE_URL`). Reports are generated on
demand from the **Drivers** tab.

### Local (Maven + Open Liberty)

```bash
export OPENAI_API_KEY=sk-...
mvn package          # builds target/corefleet-report.war
mvn liberty:run      # serves on http://localhost:8080/report/api/status
```

> Note: the template targets Java 26 / Open Liberty 26; this module is pinned to
> **Java 17** — the Jakarta EE 11 minimum and the newest Java with an official
> Open Liberty image (`open-liberty:full-java17-openj9`).

## Notes

- This service holds reports in memory (last 50). Persisting them is a later step.
