import pandas as pd
def upsert(df, *primary_keys: str, record: dict):
    index_keys = df.index.names if isinstance(df.index, pd.MultiIndex) else [df.index.name]
    condition = True

    for key in primary_keys:
        if key in df.columns:
            condition &= (df[key] == record[key])
        elif key in index_keys:
            condition &= (df.index.get_level_values(key) == record[key])
        else:
            raise KeyError(f"'{key}' not found in either columns or index")

    match_indices = df[condition].index

    if not match_indices.empty:
        for col, value in record.items():
            if col in df.columns:
                df.loc[match_indices, col] = value
    else:
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)

    return df