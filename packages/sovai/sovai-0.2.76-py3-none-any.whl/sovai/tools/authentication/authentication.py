import sovai as sov
from sovai.api_config import ApiConfig
import requests
import pickle
import base64
from pyarrow.fs import S3FileSystem as S3File
import s3fs


def get_s3_filesystem_pickle(storage_provider: str, verbose: bool = False):
    """
    Retrieve the S3FileSystem for the specified storage provider using pickle.
    
    :param storage_provider: Either 'wasabi' or 'digitalocean'
    :param verbose: If True, print additional information about the request
    :return: S3FileSystem object, or None if the request fails
    """
    if storage_provider.lower() not in ['wasabi', 'digitalocean']:
        raise ValueError("storage_provider must be either 'wasabi' or 'digitalocean'")

    url = f"{ApiConfig.base_url}/credentials/get_s3_filesystem_pickle"
    headers = {
        "Authorization": f"Bearer {ApiConfig.token}",
        "Content-Type": "application/json"
    }
    params = {"storage_provider": storage_provider.lower()}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        encoded = response.content
        pickled = base64.b64decode(encoded)
        s3fs = pickle.loads(pickled)

        return s3fs

    except requests.RequestException as e:
        if verbose:
            print(f"Failed to retrieve S3FileSystem for {storage_provider}: {e}")
        return None



def get_s3fs_filesystem_json(storage_provider: str, verbose: bool = False):
    """
    Retrieve the S3FileSystem for the specified storage provider using JSON.
    
    :param storage_provider: Either 'wasabi' or 'digitalocean'
    :param verbose: If True, print additional information about the request
    :return: S3FileSystem object, or None if the request fails
    """
    if storage_provider.lower() not in ['wasabi', 'digitalocean']:
        raise ValueError("storage_provider must be either 'wasabi' or 'digitalocean'")

    url = f"{ApiConfig.base_url}/credentials/get_s3_filesystem_json"
    headers = {
        "Authorization": f"Bearer {ApiConfig.token}",
        "Content-Type": "application/json"
    }
    params = {"storage_provider": storage_provider.lower()}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        cred = response.json()

        if verbose:
            print(f"Successfully retrieved S3 credentials for {storage_provider}")

        s3fsa = s3fs.S3FileSystem(
            key=cred['access_key'],
            secret=cred['secret_key'],
            client_kwargs={'endpoint_url': cred['endpoint']}
        )

        try:
            s3fsa.ls('/')
            if verbose:
                print(f"Successfully verified S3FileSystem for {storage_provider}")
            return s3fsa
        except Exception as e:
            if verbose:
                print(f"Failed to verify S3FileSystem: {str(e)}")
            return None

    except requests.RequestException as e:
        if verbose:
            print(f"Failed to retrieve S3 credentials for {storage_provider}: {e}")
        return None
    
def get_s3_filesystem_json(storage_provider: str, verbose: bool = False):
    """
    Retrieve the S3FileSystem for the specified storage provider using JSON.
    
    :param storage_provider: Either 'wasabi' or 'digitalocean'
    :param verbose: If True, print additional information about the request
    :return: S3FileSystem object, or None if the request fails
    """
    if storage_provider.lower() not in ['wasabi', 'digitalocean']:
        raise ValueError("storage_provider must be either 'wasabi' or 'digitalocean'")

    url = f"{ApiConfig.base_url}/credentials/get_s3_filesystem_json"
    headers = {
        "Authorization": f"Bearer {ApiConfig.token}",
        "Content-Type": "application/json"
    }
    params = {"storage_provider": storage_provider.lower()}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        cred = response.json()

        if verbose:
            print(f"Successfully retrieved S3 credentials for {storage_provider}")

        s3fsa = S3File(
            access_key=cred['access_key'],
            secret_key=cred['secret_key'],
            endpoint_override=cred['endpoint']
        )

        try:
            s3fsa.ls('/')
            if verbose:
                print(f"Successfully verified S3FileSystem for {storage_provider}")
            return s3fsa
        except Exception as e:
            if verbose:
                print(f"Failed to verify S3FileSystem: {str(e)}")
            return None

    except requests.RequestException as e:
        if verbose:
            print(f"Failed to retrieve S3 credentials for {storage_provider}: {e}")
        return None

# Usage example:
# s3fs = get_s3_filesystem_pickle('wasabi', verbose=True)
# or
# s3fs = get_s3_filesystem_json('wasabi', verbose=True)
# if s3fs:
#     # Use s3fs in your operations
#     files = s3fs.ls('/')
#     print(files)
# else:
#     print("Failed to get S3FileSystem")