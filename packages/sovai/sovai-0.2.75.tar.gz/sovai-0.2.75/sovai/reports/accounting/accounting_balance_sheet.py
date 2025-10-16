from datetime import datetime, timedelta
import pandas as pd
from IPython.display import display, HTML
from sovai import data # Assuming sovai and ApiConfig are correctly set up
from sovai.api_config import ApiConfig
import requests

# generate_analyst_commentary function remains largely the same
# Added a verbose flag default to True as in original, and ensured return type consistency
def generate_analyst_commentary(html_output, verbose=True):
    url = f"{ApiConfig.base_url}/llm/generate_commentary_second"
    headers = {
        "Authorization": f"Bearer {ApiConfig.token}",
        "Content-Type": "application/json"
    }
    payload = {"html_output": html_output}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        commentary = result.get("commentary") # This can be a string or None
        
        # if verbose and commentary: # Optional: print only if commentary exists
        #     print(f"Generated commentary: {commentary[:100]}...")
        
        return commentary if commentary else "" # Return empty string if None for safer concatenation
    except requests.RequestException as e:
        if verbose:
            print(f"Request failed LLM commentary: {e}")
        return "" # Return empty string on failure for safer concatenation

def analyze_balance_sheet_changes(ticker="MSFT"):
    today = pd.to_datetime(datetime.now().date())
    df_accounting = data("accounting/weekly", tickers=ticker)
    df_ratios = data("ratios/normal", tickers=ticker)

    df_accounting["other_current_assets"] = (
        df_accounting["current_assets"]
        - df_accounting["cash_equiv_usd"]
        - df_accounting["accounts_receivable"]
        - df_accounting["inventory_amount"]
        - df_accounting["tax_assets"]
        - df_accounting["current_investments"]
    ).clip(lower=0)
    df_accounting["other_non_current_assets"] = (
        df_accounting["non_current_assets"]
        - df_accounting["property_plant_equipment_net"]
        - df_accounting["non_current_investments"]
        - df_accounting["intangible_assets"]
    ).clip(lower=0)
    df_accounting["other_non_current_liabilities"] = (
        df_accounting["non_current_liabilities"] - df_accounting["non_current_debt"]
    ).clip(lower=0)
    df_accounting["other_current_liabilities"] = (
        df_accounting["current_liabilities"]
        - df_accounting["current_debt"]
        - df_accounting["deferred_revenue"]
        - df_accounting["tax_liabilities"]
        - df_accounting["accounts_payable"]
        - df_accounting["bank_deposits"]
    ).clip(lower=0)

    last_quarter_data = df_accounting.loc[ticker].sort_index().iloc[-1]
    last_year_data = df_accounting.loc[ticker].sort_index().iloc[-53]
    two_years_ago_data = df_accounting.loc[ticker].sort_index().iloc[-105]

    last_quarter_ratios = df_ratios.loc[ticker].sort_index().iloc[-1]
    last_year_ratios = df_ratios.loc[ticker].sort_index().iloc[-53]

    items_to_analyze = [
        ("Total Assets", "total_assets"),
        ("Current Assets", "current_assets"),
        ("Cash and Equivalents", "cash_equiv_usd"),
        ("Accounts Receivable", "accounts_receivable"),
        ("Inventory", "inventory_amount"),
        ("Non-Current Assets", "non_current_assets"),
        ("Property, Plant & Equipment", "property_plant_equipment_net"),
        ("Non-Current Investments", "non_current_investments"),
        ("Intangible Assets", "intangible_assets"),
        ("Other Non-Current Assets", "other_non_current_assets"),
        ("Total Equity", "equity_usd"),
        ("Non-Current Liabilities", "non_current_liabilities"),
        ("Non-Current Portion of Total Debt", "non_current_debt"),
        ("Other Non-Current Liabilities", "other_non_current_liabilities"),
        ("Current Liabilities", "current_liabilities"),
        ("Current Debt", "current_debt"),
        ("Deferred Revenue", "deferred_revenue"),
        ("Tax Liabilities", "tax_liabilities"),
        ("Accounts Payable", "accounts_payable"),
    ]

    # Build the HTML content step-by-step. This will be wrapped later.
    report_html_content = f"<h1 class='dark-mode'>Balance Sheet Analysis for {ticker}</h1>"
    report_html_content += (
        f"<p class='dark-mode'><em>Report Date: {today.strftime('%Y-%m-%d')}</em></p>"
    )

    report_html_content += "<table class='dark-mode balance-sheet'>"
    report_html_content += "<tr><th>Item</th><th>Current Value</th><th>Previous Value</th><th>Year-over-Year Change</th></tr>"

    for item, column in items_to_analyze:
        last_quarter_value = last_quarter_data[column]
        last_year_value = last_year_data[column]
        change = last_quarter_value - last_year_value
        
        if last_year_value is not None and last_year_value != 0 and pd.notna(last_year_value):
            percent_change = (change / last_year_value) * 100
        else:
            percent_change = float('nan') 

        if (pd.isna(last_quarter_value) or last_quarter_value == 0) and \
           (pd.isna(last_year_value) or last_year_value == 0):
            continue

        arrow = "▲" if change > 0 else ("▼" if change < 0 else "") 
        color = "green" if change > 0 else ("red" if change < 0 else "#aaaaaa") # Grey for zero/no change text

        percent_change_str = f"{percent_change:.2f}%" if pd.notna(percent_change) else "N/A"
        report_html_content += f"<tr><td>{item}</td><td>${last_quarter_value:,.0f}M</td><td>${last_year_value:,.0f}M</td><td><span style='color:{color}'>{arrow} {percent_change_str}</span></td></tr>"

    report_html_content += "</table>"

    current_ratio = last_quarter_ratios["current_ratio"]
    quick_ratio = last_quarter_ratios["quick_ratio"]
    debt_to_equity = last_quarter_ratios["debt_equity_ratio"]
    
    revenue_growth = float('nan')
    if "total_revenue" in last_year_data and last_year_data["total_revenue"] != 0 and pd.notna(last_year_data["total_revenue"]):
        revenue_growth = (
            (last_quarter_data["total_revenue"] - last_year_data["total_revenue"])
            / last_year_data["total_revenue"]
            * 100
        )
    
    revenue_growth_2y = float('nan')
    if "total_revenue" in two_years_ago_data and two_years_ago_data["total_revenue"] != 0 and pd.notna(two_years_ago_data["total_revenue"]) and \
       "total_revenue" in last_year_data and pd.notna(last_year_data["total_revenue"]): # ensure last_year_data has revenue too
        revenue_growth_2y = (
            (last_year_data["total_revenue"] - two_years_ago_data["total_revenue"])
            / two_years_ago_data["total_revenue"]
            * 100
        )

    working_capital = (
        last_quarter_data["current_assets"] - last_quarter_data["current_liabilities"]
    )
    asset_turnover = last_quarter_ratios["asset_turnover"]
    return_on_equity = last_quarter_ratios["return_on_equity"]

    gross_profit_margin = last_quarter_ratios["gross_profit_margin"]
    operating_profit_margin = last_quarter_ratios["operating_profit_margin"]
    net_profit_margin = last_quarter_ratios["net_profit_margin"]
    earnings_per_share = last_quarter_ratios["earnings_per_share"]
    price_to_earnings = last_quarter_ratios["price_to_earnings"]

    report_html_content += "<div class='financial-metrics dark-mode'>"
    report_html_content += "<h2 class='metrics-heading'>Key Financial Metrics</h2>"
    report_html_content += "<div class='metrics-tables'>"
    report_html_content += "<table>"
    report_html_content += "<tr><th>Metric</th><th>Current</th><th>Previous Year</th></tr>"
    report_html_content += f"<tr><td>Current Ratio</td><td>{current_ratio:.2f}</td><td>{last_year_ratios['current_ratio']:.2f}</td></tr>"
    report_html_content += f"<tr><td>Quick Ratio</td><td>{quick_ratio:.2f}</td><td>{last_year_ratios['quick_ratio']:.2f}</td></tr>"
    report_html_content += f"<tr><td>Debt-to-Equity Ratio</td><td>{debt_to_equity:.2f}</td><td>{last_year_ratios['debt_equity_ratio']:.2f}</td></tr>"
    report_html_content += f"<tr><td>Revenue Growth (YoY)</td><td>{(f'{revenue_growth:.2f}%' if pd.notna(revenue_growth) else 'N/A')}</td><td>{(f'{revenue_growth_2y:.2f}%' if pd.notna(revenue_growth_2y) else 'N/A')}</td></tr>"
    report_html_content += f"<tr><td>Gross Profit Margin</td><td>{gross_profit_margin:.2f}%</td><td>{last_year_ratios['gross_profit_margin']:.2f}%</td></tr>"
    report_html_content += f"<tr><td>Operating Profit Margin</td><td>{operating_profit_margin:.2f}%</td><td>{last_year_ratios['operating_profit_margin']:.2f}%</td></tr>"
    report_html_content += "</table>"
    report_html_content += "<table>"
    report_html_content += "<tr><th>Metric</th><th>Current</th><th>Previous Year</th></tr>"
    report_html_content += f"<tr><td>Net Profit Margin</td><td>{net_profit_margin:.2f}%</td><td>{last_year_ratios['net_profit_margin']:.2f}%</td></tr>"
    report_html_content += f"<tr><td>Earnings Per Share</td><td>${earnings_per_share:.2f}</td><td>${last_year_ratios['earnings_per_share']:.2f}</td></tr>"
    report_html_content += f"<tr><td>Price-to-Earnings Ratio</td><td>{price_to_earnings:.2f}</td><td>{last_year_ratios['price_to_earnings']:.2f}</td></tr>"
    report_html_content += f"<tr><td>Working Capital</td><td>${working_capital:,.0f}M</td><td>${(last_year_data['current_assets'] - last_year_data['current_liabilities']):,.0f}M</td></tr>"
    report_html_content += f"<tr><td>Asset Turnover Ratio</td><td>{asset_turnover:.2f}</td><td>{last_year_ratios['asset_turnover']:.2f}</td></tr>"
    report_html_content += f"<tr><td>Return on Equity (ROE)</td><td>{return_on_equity:.2f}%</td><td>{last_year_ratios['return_on_equity']:.2f}%</td></tr>"
    report_html_content += "</table>"
    report_html_content += "</div>" 
    report_html_content += "</div>" 

    llm_commentary = generate_analyst_commentary(report_html_content)

    report_html_content += "<div class='analyst-commentary dark-mode'>"
    report_html_content += "<h2>Analyst Commentary</h2>"
    if llm_commentary: 
        report_html_content += llm_commentary
    else:
        report_html_content += "<p>Analyst commentary is currently unavailable.</p>"
    report_html_content += "</div>"

    return f"<div id='sovai-bs-report'>{report_html_content}</div>"


# UPDATED custom_css
custom_css = """
<style>
    /* Base styles for the report container */
    #sovai-bs-report {
        font-family: Arial, sans-serif;
        line-height: 1.6;
        padding: 20px;
        color: #fff; /* Default text color for the report (bright white) */
        background-color: #000; 
    }

    #sovai-bs-report .dark-mode {
        color: #fff;
        background-color: #000;
    }

    #sovai-bs-report h1.dark-mode {
        color: #4fc3f7;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 10px;
    }

    #sovai-bs-report h2 { 
        color: #4fc3f7;
        font-size: 22px;
        font-weight: bold;
        margin-top: 30px;
        margin-bottom: 15px;
        padding-bottom: 5px;
        border-bottom: 1px solid #616161;
    }

    #sovai-bs-report p.dark-mode {
        font-size: 16px;
        margin-bottom: 10px;
    }
    
    #sovai-bs-report table.dark-mode,
    #sovai-bs-report table { 
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }

    /* General table cell styling */
    #sovai-bs-report th, 
    #sovai-bs-report td {
        padding: 10px;
        text-align: left;
        border-bottom: 1px solid #616161;
    }

    /* General table header styling - UPDATED */
    #sovai-bs-report th {
        background-color: #212121; /* Dark gray background for headers */
        font-weight: bold;
        color: #ffffff; /* Explicitly white text for ALL headers */
    }

    /* Balance Sheet specific styles */
    #sovai-bs-report .balance-sheet {
        border: 1px solid #616161;
        border-radius: 5px;
    }

    /* NEW: Style for 'Current Value' and 'Previous Value' cells in the balance sheet */
    /* NEW: Style for all cells in the balance sheet */
    #sovai-bs-report .balance-sheet td:nth-child(1),
    #sovai-bs-report .balance-sheet td:nth-child(2),
    #sovai-bs-report .balance-sheet td:nth-child(3) {
    color: #555555; /* Dark gray for all value cells */
    }
    /* Note: The fourth td (YoY change) has an inline span style for its color. */
    /* Note: The first td (Item name) will use the default #fff from #sovai-bs-report. */
    /* The fourth td (YoY change) has an inline span style for its color. */

    /* Financial Metrics section styles */
    #sovai-bs-report .financial-metrics {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 30px;
        border: 1px solid #616161;
        border-radius: 5px;
        padding: 20px;
    }

    #sovai-bs-report .metrics-heading { 
        text-align: center;
        margin-bottom: 20px;
    }

    #sovai-bs-report .metrics-tables {
        display: flex;
        justify-content: space-between;
        width: 100%;
    }

    #sovai-bs-report .metrics-tables table {
        width: 48%; 
    }
    /* Headers in .metrics-tables th will now correctly use white text due to the general #sovai-bs-report th update */

    #sovai-bs-report .analyst-commentary.dark-mode {
        background-color: #212121;
        padding: 20px;
        border-radius: 5px;
        margin-top: 30px;
        border: 1px solid #616161;
    }

    #sovai-bs-report .analyst-commentary.dark-mode p {
        margin-bottom: 15px;
    }
</style>
"""

def jupyter_html_assets(ticker="AAPL"):
    analysis_html = analyze_balance_sheet_changes(ticker=ticker)
    # Make sure ApiConfig.base_url and ApiConfig.token are set before calling this
    # Example (replace with your actual config loading):
    # class ApiConfig:
    #    base_url = "YOUR_API_BASE_URL"
    #    token = "YOUR_API_TOKEN"
    return display(HTML(custom_css + analysis_html))