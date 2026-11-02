import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Inbox to Report AI", page_icon="📊")
st.title("Inbox to Report AI")
st.caption("Early-access spreadsheet reporting preview — rules-based, not generative AI.")
st.warning("Use synthetic, non-sensitive data only. No paid credits, accounts or email sync are available.")
st.markdown("[Privacy notice](https://xuejiao1987.github.io/Inbox-for-report-AI/privacy.html)")
files = st.file_uploader("Upload CSV or Excel files", type=["csv", "xlsx"], accept_multiple_files=True)
if files:
    frames = []
    for f in files:
        try:
            raw = f.getvalue()
            if len(raw) > 10_000_000:
                raise ValueError("File exceeds 10MB")
            if f.name.lower().endswith(".csv"):
                try:
                    df = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig")
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(raw), encoding="latin-1")
            else:
                df = pd.read_excel(io.BytesIO(raw))
            if len(df) > 100_000:
                raise ValueError("File exceeds 100,000 rows")
            if df.columns.duplicated().any():
                raise ValueError("Duplicate columns")
            df["source_file"] = f.name
            frames.append(df)
        except Exception as exc:
            st.error(f"{f.name}: {exc}")
    if frames:
        data = pd.concat(frames, ignore_index=True)
        st.dataframe(data.head(100))
        cols = [str(c) for c in data.columns if c != "source_file"]
        numeric = [c for c in cols if pd.to_numeric(data[c].astype(str).str.replace(",", "", regex=False), errors="coerce").notna().mean() > 0.5]
        if not numeric:
            st.error("No numeric column found.")
            st.stop()
        metric = st.selectbox("Numeric metric", numeric)
        group = st.selectbox("Group by", ["(none)"] + [c for c in cols if c != metric])
        if st.button("Generate report"):
            values = pd.to_numeric(data[metric].astype(str).str.replace(",", "", regex=False), errors="coerce")
            valid = data.assign(_value=values).dropna(subset=["_value"])
            excluded = len(data) - len(valid)
            if group == "(none)":
                summary = pd.DataFrame([{"Records": len(valid), "Total": valid["_value"].sum()}])
            else:
                summary = valid.groupby(group, dropna=False)["_value"].agg(Records="count", Total="sum").reset_index()
            st.metric("Total", f"{valid['_value'].sum():,.2f}")
            st.caption(f"{excluded} rows excluded due to invalid or missing numeric values.")
            st.dataframe(summary)
            if group != "(none)" and len(summary):
                st.bar_chart(summary.set_index(group)["Total"])
            report = f"BUSINESS REPORT\nMetric: {metric}\nImported rows: {len(data)}\nValid rows: {len(valid)}\nExcluded rows: {excluded}\nTotal: {valid['_value'].sum():,.2f}\nReview source data before making decisions."
            st.text_area("Management summary", report)
            safe = summary.copy()
            for col in safe.select_dtypes(include=["object", "string"]).columns:
                safe[col] = safe[col].map(lambda x: "'" + x if isinstance(x, str) and x.lstrip().startswith(("=", "+", "-", "@")) else x)
            st.download_button("Download CSV summary", safe.to_csv(index=False).encode("utf-8-sig"), "summary.csv", "text/csv")
            st.download_button("Download report", report, "report.txt", "text/plain")
else:
    st.info("Upload a synthetic CSV or Excel file to try the preview.")
