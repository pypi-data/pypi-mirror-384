
import sovai as sov
from sovai.api_config import ApiConfig
import requests
import pandas as pd

import requests
from sovai.api_config import ApiConfig

def get_openai_key(verbose=False):
    """
    Retrieve the OpenAI API key from the SovAI API.
    :param verbose: If True, print additional information about the request.
    :return: The OpenAI API key as a string, or None if the request fails.
    """
    url = f"{ApiConfig.base_url}/llm/get_openai_key"
    headers = {
        "Authorization": f"Bearer {ApiConfig.token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        openai_key = result["api_key"]
        
        if not openai_key:
            if verbose:
                print("OpenAI key not found in the response")
            return None
        
        if verbose:
            print("Successfully retrieved OpenAI key")
        
        return openai_key
    except requests.RequestException as e:
        if verbose:
            print(f"Failed to retrieve OpenAI key: {e}")
        return None


def generate_sovai_code(prompt, verbose=False, run=False):
    url = f"{ApiConfig.base_url}/llm/generate_sovai_code"
    headers = {
        "Authorization": f"Bearer {ApiConfig.token}",
        "Content-Type": "application/json"
    }
    payload = {"prompt": prompt}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        generated_code = result.get("generated_code")
        
        # Modify the generated code to assign the result to a variable
        generated_code = f"result = {generated_code}"
        
        if verbose or run:
            print("Generated SovAI code:")
            print(generated_code)
        if run:
            print("\nExecuting generated code...")
            # Execute the code using Python's exec function in the context of sov
            local_vars = {}
            exec(generated_code, {"sov": sov}, local_vars)
            # Return the result
            return local_vars.get('result')
        else:
            return generated_code
    except requests.RequestException as e:
        if verbose:
            print(f"Request failed: {e}")
        return None



# def generate_sovai_code(prompt, verbose=False):
#     url = f"{ApiConfig.base_url}/llm/generate_sovai_code"
#     headers = {
#         "Authorization": f"Bearer {ApiConfig.token}",
#         "Content-Type": "application/json"
#     }
#     payload = {"prompt": prompt}
    
#     try:
#         response = requests.post(url, json=payload, headers=headers)
#         response.raise_for_status()
#         result = response.json()
#         generated_code = result.get("generated_code")
        
#         if verbose:
#             print(f"Generated SovAI code:")
#             print(generated_code)
        
#         return generated_code
#     except requests.RequestException as e:
#         if verbose:
#             print(f"Request failed: {e}")
#         return None

