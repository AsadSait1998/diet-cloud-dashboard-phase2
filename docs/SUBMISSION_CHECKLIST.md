# Phase 2 submission checklist

## Team and repository

- [ ] Team names appear in README and report: Asad Arif, Can Ozveren, Muhammad Talha Arif
- [ ] GitHub repository is public or shared with the instructor
- [ ] `main` branch contains frontend, backend, infrastructure, workflows, dataset, tests, and docs
- [ ] No secrets, tokens, keys, publish profiles, or `local.settings.json` are committed
- [ ] Repository URL copied for submission

## Azure deliverables

- [ ] Azure Function deployed successfully
- [ ] `GET /api/diet-insights` returns HTTP 200 JSON
- [ ] `datasets/All_Diets.csv` exists in private Azure Blob Storage
- [ ] Static Web App is publicly accessible
- [ ] Dashboard header shows **Live Azure API connected**
- [ ] Filters and refresh change the API request/result
- [ ] Application Insights receives Function requests

## Rubric proof

- [ ] At least three visualizations visible (project provides four)
- [ ] Function execution time visible in dashboard hero
- [ ] Search, diet, cuisine, clear, and refresh controls tested
- [ ] Resource group, app settings, storage, and CORS configuration demonstrated
- [ ] Successful GitHub CI and deployment runs visible

## Files/links to submit

- [ ] Deployed Azure Function URL: `https://________________.azurewebsites.net/api/diet-insights`
- [ ] Deployed dashboard URL: `https://________________.azurestaticapps.net`
- [ ] GitHub repository URL: `https://github.com/________________/________________`
- [ ] `Phase2_Diet_Cloud_Dashboard_Report.pdf`
- [ ] Optional source archive: `Diet_Cloud_Dashboard_Phase2.zip`

## Final PDF screenshot replacement

- [ ] Replace local dashboard screenshot with public Azure dashboard screenshot if required
- [ ] Add resource-group Overview screenshot
- [ ] Add Blob container screenshot without secrets
- [ ] Add successful GitHub Actions screenshot
- [ ] Export the final report to PDF and open every page once before submission

## Suggested presentation split

- **Asad Arif:** project overview, architecture, and live dashboard walkthrough
- **Can Ozveren:** Azure Function, Blob Storage, API contract, and filters
- **Muhammad Talha Arif:** GitHub Actions, testing, cloud practices, challenges, and conclusion

