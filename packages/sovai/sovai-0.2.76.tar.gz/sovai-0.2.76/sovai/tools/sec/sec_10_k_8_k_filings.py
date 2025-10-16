
def large_filing_module(ticker=None, form=None, date_input=None, verbose=False):
    import pandas as pd
    import plotly.graph_objects as go
    import dash
    from dash import dcc, html
    from dash.dependencies import Input, Output, State
    import dash_bootstrap_components as dbc

    import nest_asyncio
    import asyncio
    nest_asyncio.apply()


    # Assuming your dataframe is called 'pivoted'

    # The SEC filing indexes are published around 10:45 PM EST nightly. This is what is returned by get_filings

    # To get the most recent filings not yet published in the SEC filing index use get_latest_filings()

    def get_data_range(df):
        start_year = int(df.columns[0][:4])
        end_year = int(df.columns[-1][:4])
        return start_year, end_year

    def get_data_and_metrics(df, lookback_years):
        end_year = int(df.columns[-1][:4])
        start_year = end_year - lookback_years + 1
        selected_years = [col for col in df.columns if int(col[:4]) >= start_year]
        df_selected = df[selected_years]

        df_complete = df_selected.dropna()
        df_normalized = df_complete.apply(lambda row: (row - row.min()) / (row.max() - row.min()), axis=1)

        total_change = df_normalized.iloc[:, -1] - df_normalized.iloc[:, 0]

        return df_normalized, df_complete, total_change

    def format_value(value):
        if abs(value) >= 1e9:
            return f'{value/1e9:.2f}B'
        elif abs(value) >= 1e6:
            return f'{value/1e6:.2f}M'
        else:
            return f'{value:.2f}'

    @property
    def dash_app(self):

        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY,  "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css"])

        pivoted = self.accounting_facts

        start_year, end_year = get_data_range(pivoted)
        max_lookback = end_year - start_year + 1

        # Define dark mode styles for dropdowns
        dark_dropdown_style = {
            'backgroundColor': '#333',
            'color': 'white',
            'border': '1px solid #666',
        }

        app.layout = dbc.Container([
            dcc.Store(id='custom-styles', data='''
                .Select-control, .Select-menu-outer, .Select-option {
                    background-color: #333 !important;
                    color: white !important;
                }
                .Select-option:hover, .Select-option.is-focused {
                    background-color: #555 !important;
                }
                .Select-option.is-selected {
                    background-color: #666 !important;
                }
            '''),
            dbc.Card([
                dbc.CardBody([
                    dcc.Slider(
                        id='lookback-slider',
                        min=1,
                        max=max_lookback,
                        step=1,
                        value=max_lookback,
                        marks={i: f'{i}' for i in range(1, max_lookback+1, 5)},
                    ),
                ])
            ], className="mb-4"),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='increasing-metrics'),
                    dcc.Dropdown(
                        id='increasing-dropdown',
                        multi=True,
                        placeholder="Select increasing metrics",
                        style=dark_dropdown_style,
                        clearable=True,
                        optionHeight=35,
                        className='dbc'
                        # className='dark-dropdown'
                    ),
                ], width=6),
                dbc.Col([
                    dcc.Graph(id='decreasing-metrics'),
                    dcc.Dropdown(
                        id='decreasing-dropdown',
                        className='dbc',
                        multi=True,
                        placeholder="Select decreasing metrics",
                        style=dark_dropdown_style,
                        clearable=True,
                        optionHeight=35,
                        # className='dark-dropdown'
                    ),
                ], width=6),
            ]),
        ], fluid=True, style={'backgroundColor': '#222', 'color': 'white'})

        @app.callback(
            [Output('increasing-dropdown', 'options'),
            Output('decreasing-dropdown', 'options'),
            Output('increasing-dropdown', 'value'),
            Output('decreasing-dropdown', 'value')],
            [Input('lookback-slider', 'value')]
        )
        def update_dropdowns(lookback_years):
            _, _, total_change = get_data_and_metrics(pivoted, lookback_years)

            increasing = total_change[total_change > 0].sort_values(ascending=False)
            decreasing = total_change[total_change <= 0].sort_values()

            inc_options = [{'label': metric, 'value': metric} for metric in increasing.index]
            dec_options = [{'label': metric, 'value': metric} for metric in decreasing.index]

            inc_default = increasing.index[:5].tolist()
            dec_default = decreasing.index[:5].tolist()

            return inc_options, dec_options, inc_default, dec_default

        @app.callback(
            [Output('increasing-metrics', 'figure'),
            Output('decreasing-metrics', 'figure')],
            [Input('lookback-slider', 'value'),
            Input('increasing-dropdown', 'value'),
            Input('decreasing-dropdown', 'value')]
        )
        def update_graphs(lookback_years, increasing_metrics, decreasing_metrics):
            df_normalized, df_complete, _ = get_data_and_metrics(pivoted, lookback_years)

            def create_figure(metrics, title):
                fig = go.Figure()

                for metric in metrics:
                    fig.add_trace(go.Scatter(
                        x=df_normalized.columns,
                        y=df_normalized.loc[metric],
                        name=metric,
                        line=dict(width=2),
                        hovertemplate='<b>%{x}</b><br>' + metric + ': <b>%{text}</b><extra></extra>',
                        text=[format_value(val) for val in df_complete.loc[metric]]
                    ))

                fig.update_layout(
                    title=title,
                    template="plotly_dark",
                    hovermode="closest",
                    showlegend=False,
                    plot_bgcolor='#222',
                    paper_bgcolor='#222',
                    font=dict(color='white'),
                    xaxis_title="Date",
                    yaxis_title="Normalized Value",
                    yaxis=dict(range=[0, 1]),
                    margin=dict(l=40, r=40, t=40, b=40),
                    hoverlabel=dict(
                        bgcolor="#444",
                        font_size=12,
                        font_family="Arial",
                        font_color="white",
                        bordercolor="#666",
                        namelength=-1
                    )
                )

                fig.add_hline(y=0.5, line_dash="dot", line_color="gray", opacity=0.5)

                return fig

            fig1 = create_figure(increasing_metrics, f"Top Increasing Metrics (Last {lookback_years} Years)")
            fig2 = create_figure(decreasing_metrics, f"Top Decreasing Metrics (Last {lookback_years} Years)")

            return fig1, fig2

        return app.run(debug=False)


    @property
    def report(self):
        import re
        from IPython.display import HTML, display

        def convert_to_dark_mode(html_content, darkmode=False):
            if not darkmode:
                return html_content

            def invert_color(color):
                # Handle hex colors
                if color.startswith('#'):
                    color = color.lstrip('#')
                    if len(color) == 3:
                        color = ''.join(c*2 for c in color)
                    r, g, b = int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)
                    return f'#{255-r:02x}{255-g:02x}{255-b:02x}'
                # Handle rgb colors
                elif color.startswith('rgb'):
                    r, g, b = map(int, re.findall(r'\d+', color))
                    return f'rgb({255-r}, {255-g}, {255-b})'
                return color

            # Function to modify inline styles
            def modify_inline_style(match):
                style = match.group(1)
                modified_style = re.sub(r'(color:#?\w+|background-color:#?\w+)',
                                        lambda m: m.group(0).replace(m.group(1).split(':')[1],
                                                                    invert_color(m.group(1).split(':')[1])),
                                        style)
                return f'style="{modified_style}"'

            # Modify inline styles
            html_content = re.sub(r'style="([^"]*)"', modify_inline_style, html_content)

            # Add dark mode styles
            dark_mode_styles = '''
            <style>
                .financial-statement {
                    background-color: #1a1a1a !important;
                    color: #e0e0e0 !important;
                }
                .financial-statement table {
                    border-color: #444 !important;
                }
                .financial-statement th {
                    background-color: #2c2c2c !important;
                    color: #ffffff !important;
                }
                .financial-statement tr:nth-child(even) { background-color: #242424 !important; }
                .financial-statement tr:nth-child(odd) { background-color: #1e1e1e !important; }
                .financial-statement .text, .financial-statement .text-4, .financial-statement .text-5, .financial-statement .text-6, .financial-statement .page-heading { color: #ffffff !important; }
                .financial-statement [style*="color"] { color: #e0e0e0 !important; }
                .financial-statement [style*="background-color"] { background-color: transparent !important; }
                .financial-statement .financial-positive { color: #4caf50 !important; }
                .financial-statement .financial-negative { color: #f44336 !important; }
                .financial-statement .highlight { background-color: #3d3d3d !important; color: #ffffff !important; }
                .financial-statement table, .financial-statement th, .financial-statement td {
                    border-color: #ffffff !important;
                }
                .financial-statement td[style*="border-bottom"],
                .financial-statement td[style*="border-top"],
                .financial-statement td[style*="border-left"],
                .financial-statement td[style*="border-right"] {
                    border-color: #ffffff !important;
                }
                .financial-statement td[style*="border"] {
                    border-color: #ffffff !important;
                }
            </style>
            '''

            # Wrap the content in a div with class 'financial-statement'
            html_content = f'<div class="financial-statement">{html_content}</div>'

            # Insert dark mode styles before the wrapped content
            html_content = dark_mode_styles + html_content

            return html_content

        def create_collapsible_html(content):
            return f'''
            <details class="sec-report-details">
                <summary class="sec-report-summary">View SEC Report</summary>
                <div class="sec-report-content">
                    {content}
                </div>
            </details>
            '''

        def display_html(filings, darkmode=False):
            html_content = filings.html()
            converted_html = convert_to_dark_mode(html_content, darkmode)
            collapsible_html = create_collapsible_html(converted_html)
            
            wrapper_html = f'''
            <div class="sec-report {'dark' if darkmode else ''}">
                <style>
                    .sec-report {{ font-family: Arial, sans-serif; }}
                    .sec-report.dark {{ background-color: #1a1a1a; color: #e0e0e0; }}
                    .sec-report-details {{ border: 1px solid #ccc; border-radius: 4px; margin-bottom: 1rem; }}
                    .sec-report-summary {{ 
                        cursor: pointer; 
                        padding: 1rem; 
                        background-color: #f0f0f0; 
                        font-weight: bold;
                        user-select: none;
                    }}
                    .sec-report.dark .sec-report-summary {{ background-color: #333; color: #fff; }}
                    .sec-report-summary:hover {{ background-color: #e0e0e0; }}
                    .sec-report.dark .sec-report-summary:hover {{ background-color: #444; }}
                    .sec-report-content {{ padding: 1rem; }}
                    .sec-report.dark .sec-report-content {{ background-color: #1a1a1a; }}
                </style>
                {collapsible_html}
            </div>
            '''
            
            display(HTML(wrapper_html))

        class ReportDisplay:
            def __init__(self, filing):
                self.filing = filing

            def __call__(self, darkmode=True):
                display_html(self.filing, darkmode)

            def __repr__(self):
                display_html(self.filing, True)  # Default to dark mode when accessed without calling
                return ""

        return ReportDisplay(self)

    from edgar import Company, get_filings
    from datetime import datetime, date as date_class, timedelta
    import functools
    import pandas as pd
    from edgar import Company, get_filings, set_identity

    # Tell the SEC who you are
    set_identity("Josh Stiela josh.stiel@factset.com")


    def create_pivot(facts, report_type):
        # Step 1: Filter for the specified report type
        df = facts[facts['form'] == report_type].copy()

        # Step 2: Create a date column
        if report_type == '10-Q':
            def get_quarter_end(year, quarter):
                if quarter == 'Q1':
                    return f"{year}-03-31"
                elif quarter == 'Q2':
                    return f"{year}-06-30"
                elif quarter == 'Q3':
                    return f"{year}-09-30"
                else:  # Q4
                    return f"{year}-12-31"
            df['date'] = df.apply(lambda row: get_quarter_end(row['fy'], row['fp']), axis=1)
        else:  # '10-K'
            df['date'] = df['fy'].astype(str) + '-12-31'  # Convert 'fy' to string before concatenation

        # Step 3: Sort by filed date and keep the latest entry for each namespace and date
        df['filed'] = pd.to_datetime(df['filed'])

        # Step 4: Create a unique identifier by combining namespace and fact
        df['unique_id'] = df['fact'] + '_' + df['namespace']

        df = df.sort_values('filed').groupby(['unique_id', 'date']).last().reset_index()

        # Step 5: Pivot the dataframe
        pivoted = df.pivot(index='unique_id', columns='date', values='val')

        # Step 6: Sort the columns by date
        pivoted = pivoted.sort_index(axis=1)

        return pivoted

    def process_financial_data(facts, report_type='10-Q'):

        pivoted = create_pivot(facts, report_type)

        # Step 7: Select the most recent 10 years (or all if less than 10)
        end_year = int(pivoted.columns[-1][:4])
        lookback_years = 10
        start_year = end_year - lookback_years + 1
        selected_years = [col for col in pivoted.columns if int(col[:4]) >= start_year]
        df_selected = pivoted[selected_years]
        df_complete = df_selected.dropna()

        return pivoted, df_complete

    def add_lazy_facts(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            filing = func(*args, **kwargs)
            if filing is not None:
                ticker = args[0]  # The first argument is always the ticker

                @property
                def facts_new(self):
                    if not hasattr(self, '_facts_new'):
                        if not hasattr(self, '_company'):
                            self._company = Company(ticker)
                        self._facts_new = self._company.get_facts().to_pandas()
                    return self._facts_new

                @property
                def accounting_facts(self):
                    if not hasattr(self, '_accounting_facts'):
                        self._accounting_facts, _ = process_financial_data(self.facts_new, report_type=self.form)
                    return self._accounting_facts

                @property
                def sampled_facts(self):
                    if not hasattr(self, '_sampled_facts'):
                        _, self._sampled_facts = process_financial_data(self.facts_new, report_type=self.form)
                    return self._sampled_facts

                @property
                def balance_sheet(self):
                    return self.obj().financials.balance_sheet

                @property
                def income_statement(self):
                    return self.obj().financials.income_statement

                @property
                def cash_flow_statement(self):
                    return self.obj().financials.cash_flow_statement

                filing.__class__.facts_new = facts_new
                filing.__class__.accounting_facts = accounting_facts
                filing.__class__.sampled_facts = sampled_facts
                filing.__class__.balance_sheet = balance_sheet
                filing.__class__.income_statement = income_statement
                filing.__class__.cash_flow_statement = cash_flow_statement
                filing.__class__.plot_facts = dash_app  # Add the new method
                filing.__class__.report = report


            return filing
        return wrapper

    def parse_date(date_str):
        formats = [
            "%Y",          # Year only
            "%Y-%m",       # Year and month
            "%Y-%m-%d",    # Full date
            "%Y-Q%q"       # Year and quarter
        ]

        for fmt in formats:
            try:
                if 'Q' in fmt:
                    year, quarter = date_str.split('-Q')
                    return date_class(int(year), (int(quarter) - 1) * 3 + 1, 1)
                parsed_date = datetime.strptime(date_str, fmt).date()
                if fmt == "%Y":
                    return date_class(parsed_date.year, 1, 1)
                elif fmt == "%Y-%m":
                    return date_class(parsed_date.year, parsed_date.month, 1)
                return parsed_date
            except ValueError:
                continue

        raise ValueError(f"Unsupported date format: {date_str}")

    @add_lazy_facts
    def ten(ticker, form="10-K", date_input=None, verbose=False):
        if not isinstance(ticker, str):
            raise ValueError("Ticker must be a string.")

        company = Company(ticker)

        if form not in ["10-K", "10-Q"]:
            raise ValueError("Form must be either '10-K' or '10-Q'.")

        if date_input is None:
            filing = company.get_filings(form=form).latest(1)
            if filing:
                filing.form = form  # Set the form attribute
            return filing

        try:
            if isinstance(date_input, int):
                parsed_date = parse_date(str(date_input))
            elif isinstance(date_input, str):
                parsed_date = parse_date(date_input)
            else:
                raise ValueError("Date should be a year (int or string) or a date string.")

            if verbose:
                print(f"Parsed date: {parsed_date}")

            if isinstance(date_input, (int, str)) and len(str(date_input)) == 4:  # Year only
                start_date = f"{parsed_date.year}-01-01"
                end_date = f"{parsed_date.year}-12-31"
            else:
                start_date = parsed_date.strftime("%Y-%m-%d")
                end_date = (parsed_date + timedelta(days=90)).strftime("%Y-%m-%d")  # Add 3 months

            if verbose:
                print(f"Searching for {form} filings between {start_date} and {end_date}")

            filings = company.get_filings(form=form).filter(date=f"{start_date}:{end_date}")

            if verbose:
                print(f"Number of filings found: {len(filings)}")

            if filings:
                filing = filings[0]
                filing.form = form  # Set the form attribute
                return filing

            if verbose:
                print(f"No {form} filings found in the specified range. Searching for the most recent filing before the start date.")

            # If no filings found in the date range, get the most recent filing before the start date
            all_filings = company.get_filings(form=form)

            if all_filings:
                filing = all_filings[0]
                filing.form = form  # Set the form attribute
                return filing

        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")
        except Exception as e:
            if verbose:
                print(f"An error occurred: {str(e)}")

        if verbose:
            print(f"No {form} filings found for {ticker} with the given criteria.")
        return None
    
    return ten(ticker, form=form, date_input=date_input, verbose=verbose)

# filing = ten("AAPL", form="10-Q", date_input="2023-Q3", verbose=False)