# Phase 1 to Phase 2 traceability

| Phase 1 asset/behavior | Phase 2 implementation |
|---|---|
| `All_Diets.csv` in the local project | Same 7,806-row dataset uploaded to private `datasets/All_Diets.csv` in Azure Blob Storage |
| Local Azurite connection string | Function App setting `DIET_STORAGE_CONNECTION_STRING` created by Bicep |
| `lambda_function.py` run as a local script | Decorator-based Azure Functions v2 HTTP trigger in `backend/function_app.py` |
| Pandas cleaning and mean imputation | Dependency-light, unit-tested cleaning in `backend/analysis_service.py` |
| Average macros only in simulated JSON | Summary, filter metadata, and four chart-ready API datasets |
| Local Matplotlib/Seaborn PNG outputs | Responsive browser canvas charts redrawn after every API request |
| Local console/file outputs | Public dashboard plus Application Insights request/error telemetry |
| Simulated CI/CD workflow | Validation, Flex Consumption deployment, and Static Web Apps deployment workflows |
| Tailwind-only HTML shell with empty canvases | Complete responsive UI, API integration, loading/errors, filters, refresh, KPIs, and accessible table |

The original Phase 1 dataset and analytical intent are preserved. The Phase 2 code is reorganized around cloud boundaries so that analysis is reusable, testable, and exposed safely to a public frontend.
