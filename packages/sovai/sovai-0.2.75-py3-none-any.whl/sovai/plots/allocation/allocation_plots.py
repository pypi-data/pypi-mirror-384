import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sovai import data


def create_line_plot_allocation():
    df_allocation_new = data("allocation/all")
    # Current date
    today = datetime.now()
    df_melt = df_allocation_new.reset_index().melt(id_vars='date', var_name='Category', value_name='Value')
    
    # Create the initial figure
    fig = px.line(df_melt, x='date', y='Value', color='Category')
    
    # Create the layout with buttons and date range slider
    layout = go.Layout(
        updatemenus=[
            dict(
                buttons=[
                    dict(label="All Data",
                         method="update",
                         args=[{"visible": [True] * len(fig.data)},
                               {"xaxis": {"range": [df_melt['date'].min(), df_melt['date'].max()]},
                                "yaxis": {"range": [df_melt['Value'].min(), df_melt['Value'].max()]}}]),
                    dict(label="Past",
                         method="update",
                         args=[{"visible": [True] * len(fig.data)},
                               {"xaxis": {"range": [today - timedelta(days=365*50), today]},
                                "yaxis": {"range": [df_melt[(df_melt['date'] >= today - timedelta(days=365*50)) & (df_melt['date'] <= today)]['Value'].min(),
                                                    df_melt[(df_melt['date'] >= today - timedelta(days=365*50)) & (df_melt['date'] <= today)]['Value'].max()]}}]),
                    dict(label="Present",
                         method="update",
                         args=[{"visible": [True] * len(fig.data)},
                               {"xaxis": {"range": [today - timedelta(days=365*2), today + timedelta(days=365*2)]},
                                "yaxis": {"range": [df_melt[(df_melt['date'] >= today - timedelta(days=365*2)) & (df_melt['date'] <= today + timedelta(days=365*2))]['Value'].min(),
                                                    df_melt[(df_melt['date'] >= today - timedelta(days=365*2)) & (df_melt['date'] <= today + timedelta(days=365*2))]['Value'].max()]}}]),
                    dict(label="Future",
                         method="update",
                         args=[{"visible": [True] * len(fig.data)},
                               {"xaxis": {"range": [today, df_melt['date'].max()]},
                                "yaxis": {"range": [df_melt[df_melt['date'] >= today]['Value'].min(),
                                                    df_melt[df_melt['date'] >= today]['Value'].max()]}}])
                ],
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                active=3,  # Set "Future" button as active (0-indexed)
                x=0.03,
                xanchor="left",
                y=1.3,
                yanchor="top",
                bordercolor='#CCCCCC',  # Light grey border
                borderwidth=1,
                font=dict(color='#333333'),  # Dark grey text
                bgcolor='#E6E6E6',  # Light grey background for active button
            )
        ]
    )
    
    # Update the figure layout
    fig.update_layout(layout)
    
    # Set initial x-axis and y-axis ranges to show future data
    fig.update_xaxes(range=[today, df_melt['date'].max()])
    fig.update_yaxes(range=[df_melt[df_melt['date'] >= today]['Value'].min(),
                            df_melt[df_melt['date'] >= today]['Value'].max()])
    
    return fig

def create_stacked_bar_plot_allocation():
    df_allocation_new = data("allocation/all")
    # Deduct 0.2 from all the columns
    df_allocation_new = df_allocation_new - 0.2
    # Perform 0-1 normalization
    df_allocation_normalized = (df_allocation_new - df_allocation_new.min()) / (df_allocation_new.max() - df_allocation_new.min())
    # Current date
    today = datetime.now()
    df_melt = df_allocation_normalized.reset_index().melt(id_vars='date', var_name='Category', value_name='Value')
    
    # Create the initial figure
    fig = px.bar(df_melt, x='date', y='Value', color='Category', barmode='stack')
    
    # Create the layout with buttons and date range slider
    layout = go.Layout(
        updatemenus=[
            dict(
                buttons=[
                    dict(label="All Data",
                         method="update",
                         args=[{"visible": [True] * len(fig.data)},
                               {"xaxis": {"range": [df_melt['date'].min(), df_melt['date'].max()]}}]),
                    dict(label="Past",
                         method="update",
                         args=[{"visible": [True] * len(fig.data)},
                               {"xaxis": {"range": [today - timedelta(days=365*50), today]}}]),
                    dict(label="Present",
                         method="update",
                         args=[{"visible": [True] * len(fig.data)},
                               {"xaxis": {"range": [today - timedelta(days=365*2), today + timedelta(days=365*2)]}}]),
                    dict(label="Future",
                         method="update",
                         args=[{"visible": [True] * len(fig.data)},
                               {"xaxis": {"range": [today, df_melt['date'].max()]}}])
                ],
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                active=3,  # Set "Future" button as active (0-indexed)
                x=0.03,
                xanchor="left",
                y=1.3,
                yanchor="top",
                bordercolor='#CCCCCC',  # Light grey border
                borderwidth=1,
                font=dict(color='#333333'),  # Dark grey text
                bgcolor='#E6E6E6',  # Light grey background for active button
            )
        ],
    )
    
    # Update the figure layout
    fig.update_layout(layout)
    
    # Set initial x-axis range to show future data
    fig.update_xaxes(range=[today, df_melt['date'].max()])
    
    return fig
