import pandas as pd
import os
import time
from datetime import timedelta
from pathlib import Path

# Cache configuration
CACHE_DIR = Path("data")
CACHE_TTL_SECONDS = timedelta(days=7).total_seconds()

def _get_file_age_seconds(file_path: Path) -> float | None:
    """Return file age in seconds, or None if it doesn't exist."""
    try:
        return time.time() - file_path.stat().st_mtime
    except (FileNotFoundError, OSError):
        return None


def _cached_parquet(url: str, filename: str) -> pd.DataFrame:
    """
    Fetch a Parquet file from a URL into a local cache directory if missing or expired,
    then load and return it as a pandas DataFrame.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / filename
    age = _get_file_age_seconds(path)
    if age is None or age > CACHE_TTL_SECONDS:
        print(f"Downloading {url} to {path}")
        df = pd.read_parquet(url)
        df.to_parquet(path)
    else:
        print(f"Loading from cache: {path}")
        df = pd.read_parquet(path)
    return df


def get_ticker_meta() -> pd.DataFrame:
    """Return the tickers metadata, cached for 7 days."""
    return _cached_parquet(
        url="https://storage.googleapis.com/sovai-public/accounting/tickers_transformed.parq",
        filename="tickers.parq"
    )


def get_codes_meta() -> pd.DataFrame:
    """Return the codes metadata, cached for 7 days."""
    return _cached_parquet(
        url="https://storage.googleapis.com/sovai-public/sovai-master/output/df_codes.parquet",
        filename="codes.parq"
    )


def update_data_files():
    """
    Manually pre-warm both ticker and code caches.
    """
    get_ticker_meta()
    get_codes_meta()
