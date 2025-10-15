[![Sovai Python SDK package](https://github.com/sovai-research/SovAI/actions/workflows/main.yml/badge.svg)](https://github.com/sovai-research/SovAI/actions/workflows/main.yml) 
[![Publish Sovai SDK to TestPyPI](https://github.com/sovai-research/SovAI/actions/workflows/python-package.yml/badge.svg)](https://github.com/sovai-research/SovAI/actions/workflows/python-package.yml)

# SovAI SDK Tool Kit Package

Python SDK Tool Kit, which provides some functions that help you fast receive information from Cloud API.

## Quick start

### Prerequisites:

- Python 3.8+

### Create the main app with authorization

```python
import sovai as sv

# There are three ways how to login to the API

# 1. Configuration API connection
sv.ApiConfig.token = "super_secret_token"
sv.ApiConfig.base_url = "https://google.com"

# 2. Read token from .env file e.g API_TOKEN=super_secret_token
sv.read_key('.env')

# 3. The Basic authentication method
sv.basic_auth("test@test.com", "super_strong_password")

# And then continue working with get some data from API and manipulating them
```

### Retrieve data from different endpoints from the API server

```python
# Retrieve data
gs_df = sv.get("bankruptcy/monthly", params={"version": 20221013})
```

### Retrieve charts data with plotting graphs

```python
# Retrieve data with plotting special flag `plot=True`
data_pca = sv.get(
    endpoint="bankruptcy/charts", params={"tickers": "A", "chart": "pca"}, plot=True
)
```
