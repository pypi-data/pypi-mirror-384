

from scipy import stats
import warnings
import logging
import ipywidgets as widgets
import pandas as pd
import numpy as np
from IPython.display import display, HTML
from scipy import stats
import warnings
from sovai import data


# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")


def prepare_data(ticker, variables):
    # Load news data
    df_news = data("news/daily", tickers=[ticker])
    df_news.index = df_news.index.set_levels(
        pd.to_datetime(df_news.index.levels[1]).date,
        level=1
    )
    
    # Load price data
    df_price = data("market/prices", tickers=[ticker], purge_cache=True)
    df_price.index = df_price.index.set_levels(
        pd.to_datetime(df_price.index.levels[1]).date,
        level=1
    )
    
    # Merge news and price data
    df_merged = pd.merge(df_news[variables], 
                         df_price[['closeadj']], 
                         left_index=True, right_index=True, how='left')
    
    # Calculate returns
    df_merged['returns'] = df_merged['closeadj'].pct_change()
    
    # Forward fill and drop NaN values
    df_merged = df_merged.ffill().dropna()
    
    return df_merged


def adf_test(series):
    from statsmodels.tsa.stattools import adfuller

    """Perform Augmented Dickey-Fuller test for stationarity."""
    result = adfuller(series)
    return pd.Series({
        'ADF Statistic': result[0],
        'p-value': result[1],
        'Critical Value (1%)': result[4]['1%'],
        'Critical Value (5%)': result[4]['5%'],
        'Critical Value (10%)': result[4]['10%']
    })

def cointegration_test(series1, series2):

    from statsmodels.tsa.stattools import coint

    """Perform cointegration test between two series."""
    _, p_value, _ = coint(series1, series2)
    return p_value

def interpret_stationarity(p_value):
    """Interpret the results of the stationarity test."""
    if p_value < 0.01:
        return "Highly stationary"
    elif p_value < 0.05:
        return "Stationary"
    elif p_value < 0.1:
        return "Weakly stationary"
    else:
        return "Non-stationary"

def interpret_cointegration(p_value):
    """Interpret the results of the cointegration test."""
    if p_value < 0.01:
        return "Strong cointegration"
    elif p_value < 0.05:
        return "Moderate cointegration"
    elif p_value < 0.1:
        return "Weak cointegration"
    else:
        return "No significant cointegration"

def interpret_vecm_coefficient(coef, p_value):
    """Interpret the VECM coefficients."""
    if p_value < 0.01:
        strength = "strong"
    elif p_value < 0.05:
        strength = "moderate"
    elif p_value < 0.1:
        strength = "weak"
    else:
        return "No significant impact"
    
    direction = "positive" if coef > 0 else "negative"
    return f"{strength.capitalize()} {direction} impact"

def granger_causality(data, variables, max_lags=5):
    from statsmodels.tsa.stattools import  grangercausalitytests

    results = {}
    for v1 in variables:
        for v2 in variables:
            if v1 != v2:
                test_result = grangercausalitytests(data[[v1, v2]], maxlag=max_lags, verbose=False)
                results[f"{v1} -> {v2}"] = {lag: round(test[0]['ssr_ftest'][1], 4) for lag, test in test_result.items()}
    return pd.DataFrame(results).T



# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")


def generate_dynamic_report(df_merged, ticker, variables):
    """Generate a comprehensive econometric analysis report."""
    report = [f"<h1>Dynamic Econometric Analysis Report: {ticker} Stock and News Sentiment</h1>"]
    
    all_variables = variables + ['returns']
    
    # 1. Stationarity Analysis
    report.append("<h2>1. Stationarity Analysis</h2>")
    stationarity_results = pd.DataFrame({var: adf_test(df_merged[var]) for var in all_variables}).T
    stationarity_results['Interpretation'] = stationarity_results['p-value'].apply(interpret_stationarity)
    report.append(stationarity_results.to_html())
    
    stationarity_implications = []
    for variable in all_variables:
        interp = stationarity_results.loc[variable, 'Interpretation']
        if "stationary" in interp.lower():
            stationarity_implications.append(f"{variable.capitalize()} is {interp.lower()}, suggesting that shocks to {variable.lower()} are likely temporary.")
        else:
            stationarity_implications.append(f"{variable.capitalize()} is {interp.lower()}, indicating potential long-term trends or structural changes.")
    
    report.append("<p><strong>Implications:</strong></p><ul>")
    report.extend([f"<li>{imp}</li>" for imp in stationarity_implications])
    report.append("</ul>")

    # 2. Cointegration Analysis
    report.append("<h2>2. Cointegration Analysis</h2>")
    report.append("<p>Cointegration analysis examines long-term equilibrium relationships between variables. Unlike Granger causality, which focuses on short-term predictive relationships, cointegration identifies variables that move together over time, even if they may deviate in the short term.</p>")
    
    cointegration_results = pd.DataFrame({
        'Variables': [f"{var.capitalize()} and Returns" for var in variables],
        'p-value': [cointegration_test(df_merged[var], df_merged['returns']) for var in variables]
    })
    cointegration_results['Interpretation'] = cointegration_results['p-value'].apply(interpret_cointegration)
    report.append(cointegration_results.to_html(index=False))
    
    coint_implications = []
    for _, row in cointegration_results.iterrows():
        if "cointegration" in row['Interpretation'].lower():
            coint_implications.append(f"There is {row['Interpretation'].lower()} between {row['Variables'].lower()}, suggesting a potential long-term equilibrium relationship.")
        else:
            coint_implications.append(f"No significant long-term relationship detected between {row['Variables'].lower()}.")
    
    report.append("<p><strong>Implications:</strong></p><ul>")
    report.extend([f"<li>{imp}</li>" for imp in coint_implications])
    report.append("</ul>")

    # 3. Granger Causality Analysis
    report.append("<h2>3. Granger Causality Analysis</h2>")
    report.append("<p>Granger causality tests whether one time series is useful in forecasting another. Unlike cointegration, which looks at long-term relationships, Granger causality focuses on short-term predictive power. It helps identify which variables might be leading indicators for others.</p>")
    
    granger_results = granger_causality(df_merged, all_variables)
    granger_results.columns = [f"Lag {i}" for i in range(1, 6)]
    report.append(granger_results.to_html())
    
    granger_implications = []
    for relation, p_values in granger_results.iterrows():
        significant_lags = [lag for lag, p_value in p_values.items() if p_value < 0.05]
        if significant_lags:
            granger_implications.append(f"{relation} shows Granger causality at lags: {', '.join(map(str, significant_lags))}.")
        else:
            granger_implications.append(f"No significant Granger causality found for {relation}.")
    
    report.append("<p><strong>Implications:</strong></p><ul>")
    report.extend([f"<li>{imp}</li>" for imp in granger_implications])
    report.append("</ul>")

    # 4. Vector Error Correction Model (VECM) Analysis
    report.append("<h2>4. Vector Error Correction Model (VECM) Analysis</h2>")
    report.append("<p>VECM combines short-term dynamics with long-term equilibrium relationships. It's particularly useful when variables are cointegrated, as it can model both short-term adjustments and long-term convergence to equilibrium.</p>")
    
    try:
        from statsmodels.tsa.vector_ar.vecm import VECM

        max_lags = 10  # Increase the number of lags considered
        logger.info(f"Fitting VECM model with {max_lags} lags")
        model = VECM(df_merged[all_variables], deterministic='co', k_ar_diff=max_lags)
        results = model.fit()
        
        logger.info(f"VECM model fitted successfully. Shape of gamma: {results.gamma.shape}")
        logger.info(f"Shape of alpha: {results.alpha.shape}")
        logger.info(f"Number of lags: {results.k_ar}")
        
        vecm_results = []
        
        n_variables = len(all_variables)
        n_lags = results.k_ar - 1  # Subtract 1 because k_ar includes the current period
        
        for i in range(n_lags):
            for j, var in enumerate(all_variables):
                if i * n_variables + j < results.gamma.shape[0]:
                    coef = results.gamma[i * n_variables + j, -1]
                    std_err = results.stderr_gamma[i * n_variables + j, -1]
                    t_stat = coef / std_err
                    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=results.nobs-1))
                    
                    vecm_results.append({
                        'Variable': f"L{i+1}.{var}",
                        'Coefficient': coef,
                        'Standard Error': std_err,
                        'p-value': p_value,
                        'Interpretation': interpret_vecm_coefficient(coef, p_value)
                    })
        
        # Add Error Correction Term
        ec_term_coef = results.alpha[-1, 0]
        ec_term_std_err = results.stderr_alpha[-1, 0]
        ec_term_t_stat = ec_term_coef / ec_term_std_err
        ec_term_p_value = 2 * (1 - stats.t.cdf(abs(ec_term_t_stat), df=results.nobs-1))
        
        vecm_results.append({
            'Variable': 'Error Correction Term',
            'Coefficient': ec_term_coef,
            'Standard Error': ec_term_std_err,
            'p-value': ec_term_p_value,
            'Interpretation': interpret_vecm_coefficient(ec_term_coef, ec_term_p_value)
        })
        
        vecm_results_df = pd.DataFrame(vecm_results)
        
        report.append("<h3>VECM Results:</h3>")
        report.append(vecm_results_df.to_html(index=False))
        
        significant_results = vecm_results_df[vecm_results_df['p-value'] < 0.05].sort_values('p-value')
        
        if not significant_results.empty:
            report.append("<h3>Significant VECM Coefficients:</h3>")
            report.append(significant_results.to_html(index=False))
        else:
            report.append("<p>No significant coefficients found at the 5% level.</p>")
        
        vecm_implications = []
        for _, row in vecm_results_df.iterrows():
            if row['p-value'] < 0.05:
                if row['Variable'] != 'Error Correction Term':
                    vecm_implications.append(f"{row['Variable']} has a {row['Interpretation'].lower()} on returns in the short term.")
                else:
                    if row['Coefficient'] > 0:
                        vecm_implications.append("The significant positive error correction term suggests that returns adjust quickly to maintain the long-term equilibrium.")
                    else:
                        vecm_implications.append("The significant negative error correction term suggests that the system may be unstable or diverging from equilibrium.")
        
        if not vecm_implications:
            vecm_implications.append("No significant short-term relationships were found in the VECM analysis, but the Error Correction Term is significant.")
        
        report.append("<p><strong>Implications:</strong></p><ul>")
        report.extend([f"<li>{imp}</li>" for imp in vecm_implications])
        report.append("</ul>")
        
        report.append(f"<p>We fitted a VECM with {n_lags} lags. The table above shows all the coefficients from the VECM analysis, highlighting which past values have an influence on current returns. The Error Correction Term indicates the speed at which the system returns to equilibrium after a deviation.</p>")
        
        if n_lags < max_lags:
            report.append("<p><strong>Note:</strong> The model selected fewer lags than requested. This suggests that additional lags did not significantly improve the model's fit to the data.</p>")
        
        logger.info(f"VECM analysis completed successfully with {n_lags} lags.")
    
    except Exception as e:
        logger.error(f"Error in VECM analysis: {str(e)}", exc_info=True)
        report.append(f"<p>An error occurred during the VECM analysis: {str(e)}</p>")
        vecm_results_df = pd.DataFrame()

    # 5. Investment Strategy Implications
    report.append("<h2>5. Investment Strategy Implications</h2>")
    strategies = []
    
    if "Strong cointegration" in cointegration_results['Interpretation'].values:
        strategies.append(f"Consider long-term trading strategies that exploit the cointegration relationship between news sentiment variables and {ticker} stock returns.")
    
    significant_granger = granger_results.apply(lambda row: any(p < 0.05 for p in row), axis=1)
    if significant_granger.any():
        strategies.append("Develop short-term trading strategies based on the Granger causality results, focusing on the most significant lags for prediction.")
    
    if not vecm_results_df.empty and any(vecm_results_df['p-value'] < 0.05):
        strategies.append(f"Implement trading strategies based on the significant VECM coefficients, particularly focusing on the lags of {' and '.join(variables)} that show strong impacts on returns.")
    
    if all(stationarity_results['Interpretation'].str.contains('stationary')):
        strategies.append("Consider mean-reversion strategies, as all variables tend to revert to their means over time.")
    
    report.append("<ul>")
    report.extend([f"<li>{strategy}</li>" for strategy in strategies])
    report.append("</ul>")
    
    # 6. Risk Management Considerations
    report.append("<h2>6. Risk Management Considerations</h2>")
    risk_factors = []
    
    if any(stationarity_results['Interpretation'].str.contains('Non-stationary')):
        risk_factors.append("The presence of non-stationary variables indicates potential long-term trends or structural changes. Regularly reassess your models to account for these evolving dynamics.")
    
    if "Strong cointegration" in cointegration_results['Interpretation'].values:
        risk_factors.append("While cointegration suggests a long-term relationship, be aware that short-term deviations can occur. Implement stop-loss mechanisms to protect against unexpected divergences.")
    
    if not vecm_results_df.empty and any(vecm_results_df['p-value'] < 0.05):
        risk_factors.append(f"The significant VECM coefficients indicate that {' and '.join(variables)} can impact returns. Develop robust news monitoring systems to quickly identify and respond to significant sentiment shifts.")
    
    report.append("<ul>")
    report.extend([f"<li>{factor}</li>" for factor in risk_factors])
    report.append("</ul>")

    # 7. Conclusion
    report.append("<h2>7. Conclusion</h2>")
    report.append(f"<p>This dynamic analysis reveals a complex relationship between news sentiment variables and {ticker} stock returns. The key findings are:</p>")
    
    key_findings = []
    key_findings.extend(stationarity_implications)
    key_findings.extend(coint_implications)
    key_findings.extend(granger_implications)
    key_findings.extend(vecm_implications if 'vecm_implications' in locals() else [])
    
    report.append("<ul>")
    report.extend([f"<li>{finding}</li>" for finding in key_findings])
    report.append("</ul>")
    
    report.append(f"<p>These insights provide a data-driven foundation for developing sophisticated trading strategies and risk management approaches. The analysis of different lags reveals the dynamic nature of the relationships between {' and '.join(variables)} and {ticker} stock returns. It's crucial to continually reassess these relationships as market dynamics evolve.</p>")

    return "\n".join(report)


from IPython.display import display, HTML, clear_output
import ipywidgets as widgets

def create_interactive_report(ticker="NVDA"):
    # Create input widgets
    ticker_input = widgets.Text(value=ticker, description='Ticker:')
    available_variables = list(data("news/daily", tickers=[ticker]).columns)
    variable1_dropdown = widgets.Dropdown(options=available_variables, value='sentiment', description='Variable 1:')
    variable2_dropdown = widgets.Dropdown(options=available_variables, value='tone', description='Variable 2:')
    
    calculate_button = widgets.Button(description="Calculate", button_style='primary')
    toggle_button = widgets.Button(description="Toggle Report", button_style='info')
    output = widgets.Output()
    report_output = widgets.Output()

    def on_calculate_click(b):
        with output:
            clear_output()
            print("Processing... This may take a few moments.")
            
            ticker = ticker_input.value
            var1 = variable1_dropdown.value
            var2 = variable2_dropdown.value
            
            variables = [var1, var2]
            df_merged = prepare_data(ticker, variables)
            report_html = generate_dynamic_report(df_merged, ticker, variables)
            
            clear_output()
            with report_output:
                clear_output()
                display(HTML(report_html))
            toggle_button.disabled = False

    calculate_button.on_click(on_calculate_click)

    def on_toggle_click(b):
        if report_output.layout.display == 'none':
            report_output.layout.display = ''
            toggle_button.description = "Hide Report"
        else:
            report_output.layout.display = 'none'
            toggle_button.description = "Show Report"

    toggle_button.on_click(on_toggle_click)
    toggle_button.disabled = True  # Initially disabled until a report is generated

    # Display the widgets and the output
    display(widgets.VBox([
        widgets.HBox([ticker_input, variable1_dropdown, variable2_dropdown]),
        widgets.HBox([calculate_button, toggle_button]),
        output,
        report_output
    ]))

# Call this function to create the interactive report
# create_interactive_report(ticker="NVDA")
# # Assuming df_merged is already created and contains the necessary data
# report_html = generate_dynamic_report(df_merged, ticker, variables)
# display(HTML(report_html))
# # Assuming df_merged is already created and contains the necessary data
