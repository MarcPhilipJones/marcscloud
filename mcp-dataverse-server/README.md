# Dataverse MCP Server (Local)

Local Python project scaffold for an **MCP over SSE** server that can read/update **Contacts** in your Dynamics 365 / Dataverse environment.

This repo already contains the Dataverse connection metadata used by the Logic Apps workflows:

- Dataverse base URL: `https://org6cb3e9fb.crm4.dynamics.com`
- Tenant ID: `996f568a-cc69-450a-b684-ae784069e679`
- Client ID: `beb6cb7d-3328-4c2f-be9a-aab746be614a`

Secrets are **not** stored in this project. Use environment variables.

## Prereqs

- Python 3.11+ (workspace currently has a 3.13 venv)

## Setup

1) Create a `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

2) Fill in `DATAVERSE_CLIENT_SECRET` in `.env`.

3) Install dependencies:

```powershell
python -m pip install -e .
```

## Run (local)

```powershell
python -m mcp_dataverse_server
```

This starts an HTTP server on `http://127.0.0.1:8000`.

## Expose with ngrok (for ChatGPT Developer Mode)

In a separate terminal:

```powershell
ngrok http 8000
```

Use the HTTPS URL ngrok gives you and set your MCP Server URL to:

- `https://<your-ngrok-subdomain>.ngrok-free.app/sse`

### Authentication setting in ChatGPT

For a presales demo, the simplest is to choose **no authentication** in the ChatGPT UI (if available).

If you want a minimal shared-secret check, set `MCP_AUTH_TOKEN` in `.env` and send:

- `Authorization: Bearer <token>`

(Note: whether ChatGPT can send a custom Bearer token depends on the UI’s supported auth modes.)

## Notes

- The Logic App workflows call Dataverse Web API endpoints like:
  - `GET /api/data/v9.2/contacts(<guid>)?...`
  - `PATCH /api/data/v9.2/contacts(<guid>)`
- This scaffold keeps **writes** behind `DATAVERSE_ALLOW_WRITES=true`.

