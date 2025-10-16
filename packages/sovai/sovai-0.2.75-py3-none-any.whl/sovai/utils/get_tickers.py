import pandas as pd
from functools import lru_cache


@lru_cache(maxsize=None)
def equity_tickers(file_path):
    df_tickers = pd.read_parquet(file_path)

    equity_categories = [
        "Domestic Common Stock",
        "ADR Common Stock",
        "Domestic Common Stock Primary Class",
        "Domestic Common Stock Secondary Class",
        "Canadian Common Stock",
        "ADR Common Stock Primary Class",
        "ADR Common Stock Secondary Class",
        "Canadian Common Stock Primary Class",
        "Canadian Common Stock Secondary Class",
    ]

    equity_df = df_tickers[df_tickers["category"].isin(equity_categories)]
    return list(equity_df["ticker"].unique())
