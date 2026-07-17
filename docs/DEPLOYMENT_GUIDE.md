# Azure deployment guide

Follow these steps from the repository root. Commands are PowerShell-compatible.

## 1. Prerequisites

- An active Azure subscription with permission to create resources
- Azure CLI (`az`) and Azure Functions Core Tools (`func`)
- Python 3.11
- A GitHub repository for this project

Sign in and select the correct subscription:

```powershell
az login
az account list --output table
az account set --subscription "<SUBSCRIPTION_ID_OR_NAME>"
```

Check that your intended Function location supports Flex Consumption:

```powershell
az functionapp list-flexconsumption-locations --output table
```

If `canadacentral` is not shown, pass a listed region to `-Location`.

## 2. Provision the cloud resources

Choose a unique 4–12 character lowercase alphanumeric suffix:

```powershell
./scripts/deploy_azure.ps1 -NameSuffix asad1234 -ResourceGroup diet-analysis-rg -Location canadacentral
```

The script creates:

- `diet-analysis-rg` resource group
- private StorageV2 account with `datasets` and `function-releases` containers
- Linux Flex Consumption plan and Python 3.11 Function App
- Log Analytics workspace and Application Insights
- Azure Static Web App (Free tier)
- Function App settings for storage, blob name, cache, CORS, and telemetry

It uploads `data/All_Diets.csv`. When `func` is installed, it also publishes `backend/`.

## 3. Verify the Function endpoint

Use the Function API value printed by the script:

```powershell
$api = "https://<FUNCTION_APP>.azurewebsites.net/api/diet-insights"
Invoke-RestMethod $api | ConvertTo-Json -Depth 6
Invoke-RestMethod "$api`?diet_types=Vegan&search=curry" | ConvertTo-Json -Depth 6
```

Confirm the response contains four keys under `charts` and a numeric `metadata.execution_time_ms`.

## 4. Put the code on GitHub

Create an empty repository, then run:

```powershell
git init
git add .
git commit -m "Complete Phase 2 Azure diet dashboard"
git branch -M main
git remote add origin https://github.com/<ACCOUNT>/<REPOSITORY>.git
git push -u origin main
```

Never commit `backend/local.settings.json`, Azure publish profiles, deployment tokens, or connection strings.

## 5. Configure backend deployment

In Azure Portal, open the Function App, choose **Overview → Get publish profile**, and save the file temporarily. If the portal says basic publishing authentication is disabled, enable SCM Basic Auth Publishing Credentials under the app's configuration before downloading it.

In GitHub, open **Settings → Secrets and variables → Actions**:

1. Add variable `AZURE_FUNCTIONAPP_NAME` with the Function App resource name.
2. Add secret `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` containing the complete publish-profile XML.

Delete the local publish-profile file after adding the secret. Run **Actions → Deploy Azure Function → Run workflow**.

## 6. Configure frontend deployment

Get the Static Web App deployment token without printing it into a report or commit:

```powershell
az staticwebapp secrets list --name <STATIC_WEB_APP_NAME> --resource-group diet-analysis-rg --query properties.apiKey -o tsv
```

Add these GitHub Actions secrets:

- `AZURE_STATIC_WEB_APPS_API_TOKEN`: the token returned above
- `FUNCTION_API_BASE_URL`: `https://<FUNCTION_APP>.azurewebsites.net/api`

Run **Actions → Deploy dashboard to Azure Static Web Apps → Run workflow**. The workflow writes the production API URL into `config.js` only inside the deployment runner and uploads the static site.

## 7. End-to-end verification

Open the Static Web App URL and verify:

1. The header says **Live Azure API connected**.
2. All five summary cards contain numbers.
3. All four charts display data.
4. Select a diet and cuisine, click **Update insights**, and confirm recipe counts change.
5. Search for a recipe term and confirm the result narrows.
6. Click the circular refresh button and confirm the function runtime/refresh time updates.
7. Test on a phone-width browser window.
8. Open browser developer tools and confirm there are no console or network errors.

## 8. Capture the required submission screenshots

Replace the local-verification screenshots in the report with these Azure screenshots if your instructor expects portal evidence:

1. Resource group Overview listing Function App, Storage, Static Web App, and Application Insights
2. Function App Overview showing its public hostname
3. Storage container showing `datasets/All_Diets.csv` (do not expose keys)
4. Browser dashboard with all charts visible
5. Browser dashboard with a filter applied
6. GitHub Actions page showing successful CI and deployments

Crop screenshots to omit subscription IDs, emails, tokens, keys, and connection strings.

To regenerate the final PDF automatically, fill `docs/evidence/deployment_values.json`, save the screenshots using the filenames in `docs/evidence/README.md`, then run:

```powershell
python -m pip install -r docs/report-requirements.txt
python scripts/build_report.py
```

## 9. Common fixes

- **Dashboard says API unavailable:** verify `FUNCTION_API_BASE_URL`, rerun the frontend workflow, and check Function logs.
- **CORS error:** ensure the Function App CORS list includes the exact `https://...azurestaticapps.net` origin with no trailing slash.
- **503 service_not_configured:** check `DIET_STORAGE_CONNECTION_STRING`, `DATA_CONTAINER_NAME`, and `DATA_BLOB_NAME` in Function App settings.
- **Blob not found:** upload `data/All_Diets.csv` as `datasets/All_Diets.csv` with matching capitalization.
- **Function workflow fails on Flex:** confirm `sku: flexconsumption` and `remote-build: true` remain in the workflow.
- **Static page deploys but charts do not:** open deployed `config.js` and confirm the Function API base URL was injected.
