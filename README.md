# Biostat Chatbot Agent

LLM-assisted chatbot that guides clinical users through defining a statistical analysis, validates inputs against study catalogs, and dispatches SAS macros to produce results. The app ships with a Flask UI, a local slot-filling flow, and optional wiring for a Google ADK multi-agent orchestrator.

- Conversationally classifies user intent into supported analyses (ANCOVA, Binary, TTE, MMRM).
- Pulls allowed values from local catalog JSON files in `schema/` for endpoints, populations, covariates, response variables, and covariance structures.
- Confirms parameters with the user, generates a SAS program, runs it through `saspy`, and uploads the PDF output via a SAS macro wrapper.
- Prefers an ADK-hosted agent graph when `ADK_ENDPOINT`/`ADK_API_KEY` are configured; otherwise uses the built-in `BiostatChatbot` class.
- Persists lightweight chat history to SQLite (`adk.db`) and writes per-session text logs under `chat_history/`.

## Project Layout
- `app.py`: Flask entry point exposing `/` (web UI) and `/get` (chat endpoint).
- `orchestrator_service.py`: Facade that routes messages to ADK when available or falls back to the local chatbot.
- `BiostatChatbot.py`: Core local flow for intent detection, slot filling, validation, confirmation, and SAS execution.
- `adk_runtime.py`: Graph/tool definitions and minimal REST client to talk to an ADK control plane.
- `SASConnect.py`: SAS integration via `saspy`; builds macro calls, executes, and uploads outputs.
- `schema/`: Analysis definitions and dataset catalogs (JSON) used to validate/offer parameter options.
- `templates/index.html`: Simple chat UI.
- `docs/agentic-architecture.md`: Notes on mapping the local flow to a multi-agent design.

## Prerequisites
- Python 3.10+ (Flask 3.x, httpx, groq, google-generativeai, saspy).
- Access to SAS (e.g., SAS OnDemand) configured via `sascfg_personal.py`.
- SAS macros available at `/home/u50452179/src/<analysis>_macro.sas` on the SAS host, and an upload macro `upload_file_aws`.

## Setup
1) Create and activate a virtual environment.
2) Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3) Export secrets:
   - `GEMINI_API_KEY` (default LLM).
   - Optional: `GROQ_API_KEY` (for `llama3-70b-8192`).
   - Optional ADK wiring: `ADK_ENDPOINT`, `ADK_API_KEY`, `ADK_GRAPH_ID` (default `biostat-orchestrator`), `ADK_DB_PATH` (default `adk.db`).
4) Ensure `sascfg_personal.py` points to your SAS deployment and credentials.

## Run the App
```bash
export FLASK_APP=app.py
flask run
```
Then open http://127.0.0.1:5000 and start chatting. The `/get` route expects a `msg` query param and returns markdown rendered to HTML in the UI.

## How It Works (local flow)
1) `find_stat_method` matches user text to an analysis using `schema/standard_analysis_schema.json`.
2) `set_analysis` seeds the required parameters from the analysis-specific schema (e.g., `ancova1_analysis_schema.json`).
3) `evaluate_info` / `evaluate_info_loop` ask for missing slots one at a time, showing options from the dataset catalogs in `schema/dataset_*.json`.
4) When all slots are filled, `update_info` asks for confirmation; on “Yes,” `execute_analysis` builds a SAS program in `generated/`, runs it via `saspy`, and `upload_file` returns the PDF URL.

## Developing
- Catalog JSONs in `schema/` drive allowed values; update them to change available options.
- Chat logs are written under `chat_history/` and SQLite storage at `adk.db` (path override via `ADK_DB_PATH`).
- `register_graph_and_tools` in `adk_runtime.py` can be used to register the agent graph and tools with an ADK control plane once available.
- No automated tests are included; validate changes by running the Flask app and exercising the chat flow.
