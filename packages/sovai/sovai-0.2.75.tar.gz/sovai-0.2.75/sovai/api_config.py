from pathlib import Path
from typing import Optional, Union

from dotenv import dotenv_values

### save le chose a faire.

class ApiConfig:
    """
    The main API Configuration
    """

    token: Optional[str] = None
    base_url: str = "https://data.sov.ai"
    token_type: str = "Bearer"
    verify_ssl: bool = True


def read_key(envpath: Union[str, Path]) -> Optional[str]:
    """
    Read .env file with credentials (e.g TOKEN or API_TOKEN) and store to the ApiConfig

    :param Union[str, Path] envpath
    :raises FileNotFoundError
    :return str
    """
    if isinstance(envpath, str):
        envpath = Path(envpath)

    if not envpath.exists():
        raise FileNotFoundError("Invalid .env file path or missing file")

    config = dotenv_values(envpath)
    ApiConfig.token = _lookup_token(config)
    return ApiConfig.token


def save_key(envpath: Union[str, Path] = ".env") -> None:
    """
    Save retrieve token from the server to .env file in the root directory

    :param Union[str, Path] envpath: _description_, defaults to ".env"
    """
    if isinstance(envpath, str):
        envpath = Path(envpath)

    with open(envpath, "w", encoding="utf8") as fh:
        fh.write(f"API_TOKEN={ApiConfig.token}")


def _lookup_token(config: dict[str, Optional[str]]) -> Optional[str]:
    """
    Lookup function which gets token from config

    :return Optional[str]: token from env variables or None
    """
    lookups = ["token", "key"]
    for name, value in config.items():
        for lookup in lookups:
            if lookup in name.lower():
                return value
    return None
