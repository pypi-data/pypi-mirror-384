import pandas as pd

## I will eventually clean this up by using wasabi presigned URL from fastapi.


import pandas as pd
import os
from datetime import datetime, timedelta


def save_or_update_tickers():

    # Define parameters for save_or_update_tickers
    output_directory = "data"
    output_filename = "tickers.parq"
    download_url = "https://storage.googleapis.com/sovai-public/accounting/tickers_transformed.parq"

    # Create the directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    # Full path for the output file
    output_path = os.path.join(output_directory, output_filename)
    # print(output_path)

    # Check if the file exists and if it's older than 7 days
    if os.path.exists(output_path):
        file_age = datetime.now() - datetime.fromtimestamp(
            os.path.getmtime(output_path)
        )
        if file_age < timedelta(days=7):
            # print("File is up-to-date, no need to download.")
            return

    # Download and save the new file
    print("Downloading and saving new file.")
    tickers_meta = pd.read_parquet(download_url)
    tickers_meta.to_parquet(output_path)


import pandas as pd

## I will eventually clean this up by using wasabi presigned URL from fastapi.


def save_or_update_codes():

    # Define parameters for save_or_update_tickers
    output_directory = "data"
    output_filename = "codes.parq"
    download_url = "https://storage.googleapis.com/sovai-public/sovai-master/output/df_codes.parquet"

    # Create the directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    # Full path for the output file
    output_path = os.path.join(output_directory, output_filename)
    # print(output_path)

    # Check if the file exists and if it's older than 7 days
    if os.path.exists(output_path):
        file_age = datetime.now() - datetime.fromtimestamp(
            os.path.getmtime(output_path)
        )
        if file_age < timedelta(days=7):
            # print("File is up-to-date, no need to download.")
            return

    # Download and save the new file
    print("Downloading and saving new file.")
    codes_meta = pd.read_parquet(download_url)
    codes_meta.to_parquet(output_path)


def update_data_files():
    """
    Manually updates the tickers and codes data files if they are outdated.
    """
    save_or_update_tickers()
    save_or_update_codes()
