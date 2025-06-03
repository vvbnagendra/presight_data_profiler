import pandas as pd

def convert_dates(df):
    for col in df.columns:
        # Check if column contains datetime.date or object that looks like dates
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_datetime64_any_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                # ignore columns that can't be converted
                pass
    return df