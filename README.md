# Blueprint BI

A LangGraph agent with a chat UI, in one repo.

```
backend/    LangGraph agent (Python)      -> http://localhost:2024
frontend/   Agent Chat UI (Next.js)       -> http://localhost:3000
```

The frontend is a copy of [langchain-ai/agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui)
with upstream history dropped, so it can be modified freely. The backend follows
the [LangGraph local server](https://docs.langchain.com/oss/python/langgraph/local-server) template.

## Prerequisites

| Tool | Version | Why |
|---|---|---|
| Python | **3.12** | Pinned in `backend/.python-version`, `pyproject.toml` and `langgraph.json`. LangGraph CLI requires ≥3.11. |
| Node | **24** (LTS) | Pinned in `.nvmrc`. Next 15.5 needs ≥20.9. |
| pnpm | **10.34.5** | Pinned via `packageManager`. Enable with `corepack enable`. |

A [Google AI Studio API key](https://aistudio.google.com/apikey) is required — the
agent uses Gemini.

## Setup

Two terminals. **Backend first** — the frontend expects it on port 2024.

### 1. Backend

```bash
cd backend
cp .env.example .env          # then add your GOOGLE_API_KEY

uv venv --python 3.12         # or: python3.12 -m venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"    # or: pip install -e ".[dev]"

langgraph dev                 # -> http://localhost:2024
```

### 2. Frontend

```bash
cd frontend/agent-chat-ui
cp .env.example .env          # defaults already point at localhost:2024
pnpm install
pnpm dev                      # -> http://localhost:3000
```

Open http://localhost:3000 and send a message.

## How the two halves connect

`langgraph.json` maps the graph in `backend/app/agent.py` to the name `agent`:

```json
"graphs": { "agent": "./app/agent.py:graph" }
```

The frontend targets it with `NEXT_PUBLIC_ASSISTANT_ID=agent`. **If you rename the
graph, rename it in both places** — a mismatch shows up as a confusing 404 from
the chat UI, not as a startup error.

## Configuration

| Variable | Where | Required | Notes |
|---|---|---|---|
| `GOOGLE_API_KEY` | `backend/.env` | yes | Import of `app/agent.py` fails fast without it. |
| `GEMINI_MODEL` | `backend/.env` | no | Defaults to `gemini-3.6-flash`. |
| `NEXT_PUBLIC_API_URL` | `frontend/.../.env` | yes | `http://localhost:2024` in dev. |
| `NEXT_PUBLIC_ASSISTANT_ID` | `frontend/.../.env` | yes | Must match a key in `langgraph.json`. |
| `LANGGRAPH_API_URL`, `LANGSMITH_API_KEY` | `frontend/.../.env` | prod only | Server-side, for the API passthrough. |

Real `.env` files are gitignored. Only `.env.example` is tracked — **never commit a key.**

> Anything prefixed `NEXT_PUBLIC_` is embedded in the browser bundle and is public.
> In production, route through the passthrough at `src/app/api/[..._path]/route.ts`
> so the deployment URL and LangSmith key stay server-side. See
> [Going to Production](https://github.com/langchain-ai/agent-chat-ui#going-to-production).

## Housekeeping

```bash
cd frontend/agent-chat-ui && pnpm audit    # expects: no known vulnerabilities
```

`backend/.langgraph_api/` is local dev-server state (checkpoints, ops log, vector
store) written by `langgraph dev`. It is gitignored — safe to delete if the dev
server gets into a bad state.

There is currently **no CI**. Run `pnpm build`, `pnpm lint` and `pnpm audit`
before pushing.
