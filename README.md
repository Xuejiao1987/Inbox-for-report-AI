# Inbox to Report AI

Early-access spreadsheet reporting preview. The public site is static GitHub Pages content in the repository root. This is **not** yet a paid SaaS product.

## Website
Enable GitHub Pages: Settings → Pages → Deploy from a branch → main → /(root). The site URL will be https://xuejiao1987.github.io/Inbox-for-report-AI/ after GitHub reports a successful deployment.

## Status
Public landing and policy drafts; payments, authentication, credit tracking, email integration and AI model analysis are not yet implemented. Demo should accept only synthetic data. Contact xuejiaocao1987@gmail.com.


## Run the interactive preview
Install `requirements.txt`, then run `streamlit run app.py`.
On Streamlit Community Cloud, use this repository, branch `main`, and entrypoint `app.py`.
No API keys or payment credentials are required for the rules-based preview.

Select **Try sample data**, choose `revenue` and group by `region`, then generate a report.
The expected total is **2,950** (North **2,100**; South **850**), with three valid rows.
Reports remain available after reruns/downloads and are cleared when inputs or selections change.
CSV/XLSX uploads are limited to 10MB and 100,000 rows per file; Excel reads the first sheet.

## Regression checks
Run `python -m unittest discover -s tests -v` after installing the requirements.
Tests cover calculations, Excel headers, reserved columns, safe CSV export, and Streamlit report state.
Use only the synthetic sample when checking the public preview. Never commit secrets or customer data.
