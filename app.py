import hashlib
import streamlit as st
from report_core import SAMPLE_CSV, read_tables, numeric_values, combine_tables, make_report, safe_csv

st.set_page_config(page_title="Inbox to Report AI", page_icon="📊")
st.title("Inbox to Report AI")
st.caption("Preview 0.2 · Early-access spreadsheet reporting preview — rules-based, not generative AI.")
st.warning("Use synthetic, non-sensitive data only. No paid credits, accounts or email sync are available.")
st.markdown("[Privacy notice](https://xuejiao1987.github.io/Inbox-for-report-AI/privacy.html) · [Support](mailto:xuejiaocao1987@gmail.com)")
use_sample = st.checkbox("Try sample data", help="Use three synthetic sales records. Expected total: 2,950.")
files = st.file_uploader("Upload CSV or Excel files", type=["csv", "xlsx"], accept_multiple_files=True, disabled=use_sample)
st.caption("Up to 10MB and 100,000 rows per file. Excel preview reads the first sheet.")
inputs = [("sample_sales.csv", SAMPLE_CSV.encode())] if use_sample else [(f.name, f.getvalue()) for f in (files or [])]
if inputs:
    fingerprint = hashlib.sha256()
    for name, raw in inputs:
        fingerprint.update(name.encode())
        fingerprint.update(hashlib.sha256(raw).digest())
    try:
        tables = read_tables(inputs)
    except ValueError as exc:
        st.session_state.pop("generated_report", None)
        st.error(str(exc))
        st.info("Fix or remove the failed upload before generating a report. No partial report was generated.")
        st.stop()
    if tables:
        data, source_column = combine_tables(tables)
        st.dataframe(data.head(100))
        cols = [c for c in data.columns if c != source_column]
        numeric = [c for c in cols if numeric_values(data[c]).notna().mean() > 0.5]
        if not numeric:
            st.session_state.pop("generated_report", None)
            st.error("No numeric column found.")
            st.stop()
        metric = st.selectbox("Numeric metric", numeric)
        group = st.selectbox("Group by", [None] + [c for c in cols if c != metric], format_func=lambda x: "(none)" if x is None else x)
        report_key = (fingerprint.hexdigest(), metric, group)
        if st.session_state.get("report_key") != report_key:
            st.session_state.pop("generated_report", None)
        st.session_state["report_key"] = report_key
        if st.button("Generate report"):
            st.session_state["generated_report"] = make_report(data, metric, group)
        if "generated_report" in st.session_state:
            summary, total, excluded, report = st.session_state["generated_report"]
            st.metric("Total", f"{total:,.2f}")
            st.caption(f"{excluded} rows excluded due to invalid or missing numeric values.")
            st.dataframe(summary)
            if group is not None and len(summary):
                st.bar_chart(summary.set_index(summary.columns[0])["Total"])
            st.text_area("Management summary", report, key="report_text_" + repr(report_key), disabled=True)
            st.download_button("Download CSV summary", safe_csv(summary), "summary.csv", "text/csv")
            st.download_button("Download report", report, "report.txt", "text/plain")
    else:
        st.session_state.pop("generated_report", None)
else:
    st.session_state.pop("generated_report", None)
    st.info("Upload a synthetic CSV or Excel file, or select Try sample data to try the preview.")
