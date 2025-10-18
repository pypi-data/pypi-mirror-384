"""
doctablex.extractor
-------------------
Extracts and cleans tables from Word (.docx) documents.

Usage:
    from doctablex import extract_tables

    tables = extract_tables("bank_statement.docx")
    for i, df in enumerate(tables):
        print(f"📘 Table {i+1}")
        print(df.head())

Note:
    PDF files are not supported directly yet.
    Convert your PDF to DOCX first using https://www.ilovepdf.com/pdf_to_word
"""

import re
import pandas as pd
from docx import Document
from dateutil.parser import parse


def extract_tables_from_docx(file_path):
    """Extracts all tables from a DOCX file as list of list."""
    document = Document(file_path)
    all_tables_data = []

    for table in document.tables:
        table_data = []
        for row in table.rows:
            row_data = [re.sub(r'\s+', ' ', cell.text.strip()) for cell in row.cells]
            table_data.append(row_data)
        all_tables_data.append(table_data)
    return all_tables_data


def detect_header_row(table_data, max_rows_to_check=10):
    """Detect the row most likely to be the header."""
    for i, row in enumerate(table_data[:max_rows_to_check]):
        if not any(cell.strip() for cell in row):
            continue
        text_cells = sum(bool(re.search(r'[A-Za-z]', cell)) for cell in row)
        if text_cells / len(row) > 0.7:
            return i
    return 0


def looks_like_date(value: str) -> bool:
    """Detect if a string looks like a date using regex + parsing."""
    if not isinstance(value, str) or not value.strip():
        return False

    value = value.strip()
    date_patterns = [
        r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$",
        r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$",
        r"^[A-Za-z]{3,9}\s\d{1,2},?\s?\d{2,4}$",
        r"^\d{1,2}\s[A-Za-z]{3,9}\s\d{4}$",
        r"^\d{1,2}[-\s][A-Za-z]{3,9}[-\s]?\d{2,4}$",
    ]

    for pattern in date_patterns:
        if re.match(pattern, value):
            return True

    try:
        parse(value, fuzzy=False)
        return True
    except Exception:
        return False


def detect_column_type(series: pd.Series) -> str:
    """Detect probable data type of a column using regex patterns."""
    text_values = series.dropna().astype(str).head(50)
    patterns = {
        "numeric": re.compile(r"^-?\d+(\.\d+)?$"),
        "currency": re.compile(r"^[₦$€£]?\s?\d{1,3}(,\d{3})*(\.\d{1,2})?$"),
    }

    match_counts = {dtype: 0 for dtype in patterns}
    date_count = 0

    for value in text_values:
        val = value.strip()
        if looks_like_date(val):
            date_count += 1
        else:
            for dtype, pattern in patterns.items():
                if pattern.match(val):
                    match_counts[dtype] += 1

    if date_count > len(text_values) * 0.6:
        return "datetime"

    detected_type = max(match_counts, key=match_counts.get)
    if match_counts[detected_type] == 0:
        return "text"

    return detected_type


def convert_column(series, dtype: str):
    """Convert a column to its detected data type."""
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]

    if dtype == "numeric":
        return pd.to_numeric(series, errors="coerce")
    elif dtype == "currency":
        cleaned = series.replace(r"[₦$€£,]", "", regex=True)
        return pd.to_numeric(cleaned, errors="coerce")
    elif dtype == "datetime":
        return pd.to_datetime(series, errors="coerce", dayfirst=True)
    else:
        return series.astype(str).apply(lambda x: x.strip() if isinstance(x, str) else x)


def infer_column_types_regex(df: pd.DataFrame) -> pd.DataFrame:
    """Infer column datatypes using regex-based detection."""
    for col in df.columns:
        dtype = detect_column_type(df[col])
        df[col] = convert_column(df[col], dtype)
    return df


def tables_to_dataframes(file_path):
    """Extract all tables and convert to DataFrames with header detection + type inference."""
    extracted_tables = extract_tables_from_docx(file_path)
    dataframes = []

    for table in extracted_tables:
        if not table:
            continue

        header_index = detect_header_row(table)
        header = table[header_index]
        data = table[header_index + 1:]

        min_cols = min(len(header), min(len(r) for r in data))
        header = header[:min_cols]
        data = [r[:min_cols] for r in data]

        df = pd.DataFrame(data, columns=header)
        df = infer_column_types_regex(df)
        dataframes.append(df)

    return dataframes


def extract_tables(file_path):
    """
    Public API for users.
    Extracts tables from a DOCX file and returns a list of DataFrames.
    """
    if not file_path.lower().endswith(".docx"):
        raise ValueError(
            "❌ Only .docx files are supported. Convert PDFs using https://www.ilovepdf.com/pdf_to_word."
        )
    print(f"📄 Extracting tables from {file_path} ...")
    return tables_to_dataframes(file_path)
