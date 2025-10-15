def md_from(df):
    """
    markdown style
    """
    from tabulate import tabulate
    try:

        import pandas
        if isinstance(df, pandas.DataFrame):
            data = df.values.tolist()
        else:
            raise TypeError  # 继续尝试 Polars
    except:
        import polars
        if isinstance(df, polars.DataFrame):
            data = df.rows()

        else:
            raise TypeError("Unsupported DataFrame type.")

    return tabulate(data, headers=df.columns, tablefmt='github')
