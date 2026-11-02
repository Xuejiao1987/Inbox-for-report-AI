"""Pure, testable helpers for the rules-based preview."""
import io
import numpy as np
import pandas as pd

SAMPLE_CSV = 'date,region,revenue\n2026-10-01,North,1200\n2026-10-02,South,850\n2026-10-03,North,900\n'


def read_table(name, raw):
    if len(raw) > 10_000_000:
        raise ValueError('File exceeds 10MB')
    if name.lower().endswith('.csv'):
        try:
            data = pd.read_csv(io.BytesIO(raw), encoding='utf-8-sig')
        except UnicodeDecodeError:
            data = pd.read_csv(io.BytesIO(raw), encoding='latin-1')
    else:
        data = pd.read_excel(io.BytesIO(raw))
    if len(data) > 100_000:
        raise ValueError('File exceeds 100,000 rows')
    if data.empty:
        raise ValueError('File contains no data rows')
    data.columns = [str(c) for c in data.columns]
    if data.columns.duplicated().any():
        raise ValueError('Duplicate columns after converting column names to text')
    return data


def read_tables(inputs):
    """Reject the whole batch if any upload fails; never report partial data."""
    tables = []
    errors = []
    for name, raw in inputs:
        try:
            tables.append((name, read_table(name, raw)))
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    if errors:
        raise ValueError("\n".join(errors))
    return tables


def numeric_values(series):
    return pd.to_numeric(series.astype(str).str.replace(',', '', regex=False), errors='coerce').replace([np.inf, -np.inf], np.nan)


def combine_tables(tables):
    columns = {c for _, frame in tables for c in frame.columns}
    source_column = 'source_file'
    while source_column in columns:
        source_column = '_' + source_column
    frames = []
    for name, frame in tables:
        frame = frame.copy()
        frame[source_column] = name
        frames.append(frame)
    return pd.concat(frames, ignore_index=True), source_column


def make_report(data, metric, group):
    values = numeric_values(data[metric])
    valid_mask = values.notna()
    valid_values = values[valid_mask]
    excluded = int((~valid_mask).sum())
    if group is None:
        summary = pd.DataFrame([{'Records': len(valid_values), 'Total': valid_values.sum()}])
    else:
        # Internal columns never overwrite a user-provided column.
        work = pd.DataFrame({'group': data.loc[valid_mask, group], 'value': valid_values})
        summary = work.groupby('group', dropna=False)['value'].agg(Records='count', Total='sum').reset_index()
        # Avoid collisions with generated metric labels (e.g. an input named Total).
        label = group if group not in ('Records', 'Total') else f'{group} (group)'
        summary = summary.rename(columns={'group': label})
    total = float(valid_values.sum())
    report = f'BUSINESS REPORT\nMetric: {metric}\nImported rows: {len(data)}\nValid rows: {len(valid_values)}\nExcluded rows: {excluded}\nTotal: {total:,.2f}\nReview source data before making decisions.'
    return summary, total, excluded, report


def safe_csv(summary):
    def safe(value):
        return "'" + value if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')) else value
    result = summary.copy()
    result.columns = [safe(c) for c in result.columns]
    for col in result.select_dtypes(include=['object', 'string']).columns:
        result[col] = result[col].map(safe)
    return result.to_csv(index=False).encode('utf-8-sig')
