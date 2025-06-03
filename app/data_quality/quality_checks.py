# Nulls, duplicates, counts

import pandas as pd
import numpy as np

def run_quality_checks(df):
    checks = {
        "Missing Values (%)": df.isnull().mean().round(2).to_dict(),
        "Duplicate Rows": int(df.duplicated().sum()),
        "Constant Columns": [col for col in df.columns if df[col].nunique() <= 1],
        "Outlier Columns": detect_outliers(df)
    }
    return checks

def detect_outliers(df):
    numeric_cols = df.select_dtypes(include=[np.number])
    outlier_columns = []
    for col in numeric_cols.columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = df[(df[col] < lower) | (df[col] > upper)]
        if not outliers.empty:
            outlier_columns.append(col)
    return outlier_columns
