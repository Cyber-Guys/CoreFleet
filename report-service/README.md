# CoreFleet Hourglass Report Service (Jakarta EE + LLM)

Jakarta EE 11 (Open Liberty) service that completes **Challenge 3**. Built from the
Eclipse o-cei [`hourglass-template`](https://gitlab.eclipse.org/eclipse-research-labs/o-cei-project/challenge-3-jakarta-ee-hourglass/hourglass-template),
it uses **langchain4j** + OpenAI to:

1. map a domain/use case onto the **Hourglass Model** (the template's endpoint), and
2. turn a CoreFleet **driving-session summary** into a structured **driving report**.

## Endpoints

Context root `/report`, JAX-RS application path `api`.

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/report/api/status` | Health + configured model (no secrets). |
| `POST` | `/report/api/hourglass/analyze` | `{domain, useCase}` → `{stakeholders, capabilities, standardsGroups}`. |
| `POST` | `/report/api/report` | Session summary JSON → `DrivingReport` (scores + narrative + hourglass). |
| `GET`  | `/report/api/report` | Recent generated reports (newest first). |

See `hourglass-model.http` for ready-to-run examples.

## How the LLM is wired

- `ChatModelProducer` builds a langchain4j `ChatModel` (OpenAI) from MicroProfile
  Config. The key comes from `openai.api-key`, which maps to the **`OPENAI_API_KEY`
  environment variable** — it is never compiled in.
- `AiServiceFactory` builds typed `AiServices` whose methods declare a prompt and a
  **POJO return type**; langchain4j drives the model to emit matching structured JSON.
- Numeric scores stay grounded in the telemetry; the model writes the narrative and
  the hourglass mapping.

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

The fleet server posts every finished session to this service automatically
(`REPORT_URL`).

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
