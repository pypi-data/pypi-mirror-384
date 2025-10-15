from typing import Union, Optional

import pandas as pd
import plotly.express as px
import plotly.io as pio
from plotly.graph_objs import Figure
from sovai.errors.sovai_errors import InvalidInputData
from sovai.utils.helpers import dict_depth


def set_dark_mode(fig: Figure):
    return fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(10, 10, 10, 1)",
        paper_bgcolor="rgba(10, 10, 10, 1)",
    )


def plotting_data(
    df: Union[pd.DataFrame, dict],
    x: Optional[str] = None,
    y: Optional[str] = None,
    chart_type: str = "line",
    **kwargs,
) -> None:
    """
    This function takes dataFrame or dict (JSON) and then draw plot using your paramiters and chart type

    :param pd.DataFrame df:
    :param str x: defaults to None
    :param str y: defaults to None
    :param str chart_type: defaults to "line"
    """

    if isinstance(df.to_dict(), dict) and dict_depth(df.to_dict()) > 1:
        # print("first")
        # pio.show(df.to_dict())

        fig = pio.from_json(df.to_json())
        fig = set_dark_mode(fig)
        fig.show()

    else:
        if not x or not y:
            print("convet series to dict")
            # pio.show(df.to_dict())
            print(df)
            raise InvalidInputData("Missing input params x or y")
        if chart_type == "line":
            fig = px.line(df, x=x, y=y, **kwargs)
            fig.show()
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x, y=y, **kwargs)
            fig.show()
    return fig
