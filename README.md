# Diet Cloud Dashboard — Phase 2

A complete Phase 2 implementation that moves the Phase 1 Diets Dataset analysis into Azure and presents the results through a public, interactive web dashboard.

**Project team:** Asad Arif, Can Ozveren, and Muhammad Talha Arif

## What is included

- Python Azure Functions v2 HTTP API in `backend/`
- Private Azure Blob Storage dataset access with a short in-memory cache
- Four chart-ready analyses: average macros, recipe distribution, protein-versus-carbs, and leading cuisines
- Search, diet, cuisine, clear, and source-refresh controls
- Function execution time, request ID, source, and record-count metadata
- Responsive, accessible frontend in `frontend/`
- Bicep infrastructure for Flex Consumption, Blob Storage, Application Insights, and Azure Static Web Apps
- GitHub Actions for tests and separate backend/frontend deployments
- Local zero-dependency demo server
- Submission report and step-by-step deployment guide in `docs/`

## Architecture

```text
Browser
  │  HTTPS GET /api/diet-insights?diet_types=...&cuisine=...&search=...
  ▼
Azure Static Web Apps ───────► Azure Function (Python/Flex Consumption)
                                      │
                                      ├── reads private All_Diets.csv
                                      ▼
                              Azure Blob Storage
                                      │
                                      └── telemetry → Application Insights
```

The browser receives aggregated JSON only. The storage connection string stays in Function App settings and is never exposed to the frontend.

## Run the complete dashboard locally

Python 3.11+ is sufficient; the demo server uses only the standard library.

```powershell
python scripts/local_demo_server.py
```

Open `http://127.0.0.1:8000`. The demo exercises the same cleaning and aggregation module used by Azure Functions, using `data/All_Diets.csv` as its source.

Run the unit tests:

```powershell
python -m unittest discover -s backend/tests -v
```

## Run through Azure Functions Core Tools

1. Create and activate a Python 3.11 virtual environment.
2. Install `backend/requirements.txt`.
3. Copy `backend/local.settings.example.json` to `backend/local.settings.json`.
4. From `backend/`, run `func start`.
5. In a second terminal, serve `frontend/` on port 8000 or run the included demo server.
6. For a separate frontend server, set `frontend/config.js` to `http://localhost:7071/api`.

`local.settings.json` is intentionally excluded from source control because settings can contain secrets.

## Deploy to Azure

The detailed, copy-ready procedure is in [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md). The shortest path is:

```powershell
az login
./scripts/deploy_azure.ps1 -NameSuffix asad1234
```

The suffix must be 4–12 lowercase letters/numbers and should be unique. The script provisions the resource group resources, uploads the dataset, and publishes the Function when Azure Functions Core Tools is installed. The included workflows then provide repeatable GitHub deployments.

Required GitHub configuration:

| Type | Name | Value |
|---|---|---|
| Variable | `AZURE_FUNCTIONAPP_NAME` | Function App resource name |
| Secret | `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` | Function App publish-profile XML |
| Secret | `FUNCTION_API_BASE_URL` | `https://<function-app>.azurewebsites.net/api` |
| Secret | `AZURE_STATIC_WEB_APPS_API_TOKEN` | Static Web App deployment token |

After deployment, fill `docs/evidence/deployment_values.json`, add the four named evidence screenshots described in `docs/evidence/README.md`, and run `python scripts/build_report.py`. The final PDF is regenerated with the real public links and appended Azure/GitHub evidence.

## API contract

`GET /api/diet-insights`

Optional query parameters:

- `diet_types`: comma-separated diet names
- `cuisine`: exact cuisine label
- `search`: substring match across recipe, diet, and cuisine
- `refresh=true`: bypass the Function's dataset cache

Successful responses contain `summary`, `filters`, `charts`, and `metadata`. The frontend uses no storage credentials and performs no analysis in the browser.

## Rubric coverage

| Rubric category | Implementation evidence |
|---|---|
| Deployment (20) | Bicep Flex Consumption Function, storage, monitoring, deployment script, Function workflow |
| Frontend dashboard (20) | Responsive dashboard, dynamic states, filters, accessible table, error handling |
| Data visualization (20) | Four distinct canvas visualizations built from live API data |
| Integration (20) | Production API endpoint injected by GitHub secret; real HTTP filtering and refresh |
| Cloud practices (10) | Resource group, private container, Function App settings, TLS, CORS, Application Insights |
| Documentation (10) | Architecture, deployment guide, report PDF, testing evidence, and submission checklist |

## Security and cloud-practice notes

- The `datasets` container is private; only the Function receives its connection string.
- HTTPS and TLS 1.2 are enforced in the infrastructure template.
- CORS is restricted to the generated Static Web App hostname by Bicep.
- The public endpoint is anonymous because it returns read-only aggregated course data. Do not place a Function key in browser JavaScript.
- For a production system, migrate storage access from a connection string to managed identity and Key Vault after the course demonstration.

## Official references

- [Azure Functions Python developer reference](https://learn.microsoft.com/en-nz/azure/azure-functions/functions-reference-python)
- [Azure Functions app settings reference](https://learn.microsoft.com/en-us/azure/azure-functions/functions-app-settings)
- [Create Flex Consumption resources with Bicep](https://learn.microsoft.com/en-us/azure/azure-functions/functions-create-first-function-bicep)
- [Azure Functions GitHub Actions deployment](https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-github-actions)
- [Azure Static Web Apps build configuration](https://learn.microsoft.com/en-in/azure/static-web-apps/build-configuration)
- [Azure Static Web Apps configuration](https://learn.microsoft.com/en-us/azure/static-web-apps/configuration)
