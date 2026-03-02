# Azure Web Apps — Multi-Customer Demo

Minimal Node.js + Express app with two customer sub-pages, designed for Azure App Service (Free tier).

## Folder Structure

```
azure-webapps/
├── server.js          # Express app — all routes in one file
├── package.json
├── .env.example       # Environment variable template
├── .gitignore
└── README.md
```

## Quick Start

```bash
cd azure-webapps
npm install
npm start
```

Open http://localhost:3000

## Routes

| Route        | Description                                |
|--------------|--------------------------------------------|
| `/`          | Landing page with links to both customers  |
| `/CustomerA` | Customer A portal (teal background)        |
| `/CustomerB` | Customer B portal (amber background)       |
| `/health`    | JSON health check                          |
| `/*`         | 404 page with link back to home            |

Every customer page displays live Node.js runtime info (version, uptime, timestamp, hostname) rendered server-side.

## Environment Variables

| Variable   | Description  | Default |
|------------|-------------|---------|
| `PORT`     | Server port | `3000`  |

Copy `.env.example` to `.env` to override:

```bash
cp .env.example .env
```

## Deploy to Azure App Service

> **Cost note**: Confirm the App Service SKU/tier and estimated cost before deploying.

```bash
# Login and deploy (will prompt for resource group / plan)
az login
az webapp up --name <app-name> --runtime "NODE:18-lts" --sku F1
```

The `F1` SKU is the **free tier** — no charge for light usage.
