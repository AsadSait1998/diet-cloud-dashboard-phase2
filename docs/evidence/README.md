# Final Azure evidence

After deployment:

1. Fill the three public values in `deployment_values.json`.
2. Add any or all of the following PNG screenshots to this folder:
   - `resource-group.png`
   - `blob-container.png`
   - `public-dashboard.png`
   - `github-actions.png`
3. Crop out emails, subscription IDs, tokens, keys, connection strings, and unrelated browser tabs.
4. From the repository root, run:

```powershell
python -m pip install -r docs/report-requirements.txt
python scripts/build_report.py
```

The generated `docs/Phase2_Diet_Cloud_Dashboard_Report.pdf` will contain the public URLs and append every evidence image found here.
