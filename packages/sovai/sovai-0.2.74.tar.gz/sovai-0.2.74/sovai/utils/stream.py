from typing import Any
import io
import pandas as pd
from requests import Response  # type: ignore


import io
import pyarrow.ipc as ipc
import pandas as pd


def stream_data(res: Response) -> pd.DataFrame:
    """
    Get streaming data from server and convert to pd.DataFrame.
    Ensure 'ticker' column (if it exists) is at the front of the DataFrame.

    :param Response res: Response object from requests.
    :return pd.DataFrame: DataFrame with 'ticker' column at the front if it exists.
    """
    f = io.BytesIO()
    for chunk in res.iter_content(chunk_size=100000):
        f.write(chunk)
    f.seek(0)

    data = pd.read_pickle(f)

    # Move 'ticker' column to the front if it exists
    if "ticker" in data.columns:
        cols = ["ticker"] + [col for col in data.columns if col != "ticker"]
        data = data[cols]

    return data


def stream_data_pyarrow(response: Response) -> pd.DataFrame:
    """
    Read a Response object containing a serialized Arrow table and convert it to a Pandas DataFrame.

    :param Response response: The response object from an HTTP request containing serialized Arrow table.
    :return pd.DataFrame: DataFrame representation of the Arrow table.
    """
    # Read the content of the response into a BytesIO object
    stream = io.BytesIO(response.content)

    # Deserialize the Arrow table from the stream
    reader = ipc.open_stream(stream)
    table = reader.read_all().to_pandas()

    # Optionally rearrange columns if 'ticker' is present
    if "ticker" in table.columns:
        cols = ["ticker"] + [col for col in table.columns if col != "ticker"]
        table = table[cols]

    return table
