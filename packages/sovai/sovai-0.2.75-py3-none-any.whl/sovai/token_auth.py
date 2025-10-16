from sovai.api_config import ApiConfig, save_key
# Removed verify_token import from top level
from sovai.errors.sovai_errors import InvalidCredentialsError


def token_auth(token: str):
    """Authenticates using a token, saves it, and verifies it."""

    # Lazy load verify_token here, just before use
    from sovai.utils.client_side import verify_token

    ApiConfig.token = token
    ApiConfig.token_type = "Bearer"
    save_key() # Assumes save_key doesn't trigger heavy imports

    # Now call the imported function
    is_valid, user_id = verify_token(verbose=False) # Uses lazy-loaded verify_token

    if not is_valid:
        # print('invalid') # Keep commented or use logging
        raise InvalidCredentialsError("Invalid or expired token. Please authenticate.")

    # Optionally, you could return something useful, like the validity or user_id
    # print(f"Token verified successfully for user ID: {user_id}") # Or use logging
    # return is_valid, user_id