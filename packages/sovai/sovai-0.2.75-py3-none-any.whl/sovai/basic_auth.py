import requests  # type: ignore

from sovai.api_config import ApiConfig, save_key
from sovai.errors.sovai_errors import InvalidCredentialsError, ServiceUnavailableError


def basic_auth(email: str, password: str) -> bool:
    """
    The basic authentication method retrieves the token from the API server
    and stores it in the ApiConfig and .env file in the root directory

    :param str email
    :param str password
    """
    credentials: dict = {"email": email, "password": password}
    login_endpoint_url: str = f"{ApiConfig.base_url}/login/"

    try:
        res = requests.post(
            login_endpoint_url, json=credentials, verify=ApiConfig.verify_ssl
        )
        res.raise_for_status()
        res = res.json()
        ApiConfig.token = res["access_token"]
        ApiConfig.token_type = res["token_type"]
        save_key()
        return True
    except Exception:
        if res.status_code == 401:
            raise InvalidCredentialsError("The user doesn't exist in the system")
        if res.status_code == 503:
            raise ServiceUnavailableError("Temporary Service Unavailable")
    return False
