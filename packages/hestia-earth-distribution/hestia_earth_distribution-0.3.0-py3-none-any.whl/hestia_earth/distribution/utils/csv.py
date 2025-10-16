from io import BytesIO
import pandas as pd


def df_to_csv_buffer(df: pd.DataFrame):
    buffer = BytesIO()
    df.to_csv(buffer)
    return buffer.getvalue()


def drop_incomplete_cycles(df: pd.DataFrame, col_suffix: str = 'completeness'):
    df = df.to_frame() if isinstance(df, pd.Series) else df
    columns = [col for col in df.columns if col.startswith(col_suffix)]
    for col in columns:
        df = df[df[col]].drop(col, axis=1)
    return df
