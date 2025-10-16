
def edgar_search_report(search_query="CFO Resignation"):

    import ipywidgets as widgets
    from IPython.display import display, HTML
    import pandas as pd
    from datetime import datetime
    from edgar_tool.cli import SecEdgarScraperCli as edgar_tool
    import sys
    from io import StringIO
    import base64
    import time
    import subprocess
    import psutil
    import os

    # Create edgar_search_results directory if it doesn't exist
    results_dir = "edgar_search_results"
    os.makedirs(results_dir, exist_ok=True)

    custom_css = """
    <style>
        .widget-label { font-weight: bold; color: #ffd700; }
        .widget-text, .widget-dropdown, .widget-datepicker, .jupyter-button {
            background-color: #2a3b4c !important; color: #ffffff !important;
            border: 1px solid #87ceeb !important; border-radius: 4px !important;
        }
        .jupyter-button {
            background-color: #ffd700 !important; color: #1a2b3c !important;
            font-weight: bold !important;
        }
        .jupyter-button:hover { background-color: #ffeb3b !important; }
        .output_wrapper {
            background-color: #1a2b3c; color: #ffffff;
            padding: 10px; border-radius: 4px;
        }
        .download-link { color: #3498db !important; text-decoration: underline; }
    </style>
    """

    # display(HTML(custom_css))

    # Create widgets
    search_keywords = widgets.Text(description='Search Keywords:', value=search_query, style={'description_width': 'initial'})
    start_date = widgets.DatePicker(description='Start Date:', value=datetime(datetime.now().year, 1, 1), style={'description_width': 'initial'})
    end_date = widgets.DatePicker(description='End Date:', value=datetime(datetime.now().year, 12, 31), style={'description_width': 'initial'})
    filing_type = widgets.Dropdown(
        options=['all', 'all_except_section_16', 'all_annual_quarterly_and_current_reports', 'all_section_16', 'beneficial_ownership_reports', 'exempt_offerings', 'registration_statements', 'filing_review_correspondence', 'sec_orders_and_notices', 'proxy_materials', 'tender_offers_and_going_private_tx', 'trust_indentures'],
        value='all',
        description='Filing Type:',
        style={'description_width': 'initial'}
    )
    company_cik = widgets.Text(description='Company CIK:', style={'description_width': 'initial'})
    filter_by_location = widgets.Dropdown(
        options=['', 'Incorporated in', 'Principal executive offices in'],
        description='Filter by Location:',
        style={'description_width': 'initial'}
    )
    location = widgets.Dropdown(
        options=['', 'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'District of Columbia', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'United States', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'],
        description='Location:',
        style={'description_width': 'initial'}
    )
    max_wait = widgets.IntText(value=20, description='Max Wait (sec):', style={'description_width': 'initial'})

    search_button = widgets.Button(description='Search EDGAR', button_style='warning', icon='search')
    download_button = widgets.Button(description='Download', button_style='info', icon='download', layout=widgets.Layout(display='none'))
    download_link = widgets.HTML()
    output = widgets.Output()

    form = widgets.VBox([
        widgets.HTML("<h2 style='color: #ffd700;'>EDGAR Search Tool</h2>"),
        widgets.HBox([widgets.VBox([search_keywords, start_date, end_date, max_wait]), widgets.VBox([filing_type, company_cik, filter_by_location, location])]),
        widgets.VBox([widgets.HBox([search_button, download_button]), download_link]),
        output
    ])

    csv_output = ""
    csv_content = ""
    search_results = pd.DataFrame()

    def create_download_link(csv_content, filename):
        b64 = base64.b64encode(csv_content.encode()).decode()
        href = f'<a href="data:text/csv;base64,{b64}" download="{filename}" target="_blank" class="download-link">Download CSV File</a>'
        return href

    def download_file(b):
        nonlocal csv_output, csv_content
        if csv_content:
            link = create_download_link(csv_content, csv_output)
            code_snippet = f"""
            <div style='position: relative; margin-top: 10px; margin-bottom: 10px;'>
                <pre style='background-color: #f7f7f7; border: 1px solid #ddd; border-radius: 4px; padding: 10px; margin: 0; overflow: auto;'>
    <code id='codeSnippet' style='color: #333;'>import pandas as pd
    df = pd.read_csv("edgar_search_results/{csv_output}")</code></pre>
            </div>
            """
            download_link.value = f"{link}<br>Click the link above to download the CSV file.<br>{code_snippet}<br>Use the code above to load the data into a pandas DataFrame."
        else:
            with output:
                print("No results to download. Please perform a search first.")

    def run_search(search_kw, start_date, end_date, file_type, cik, csv_output, peo_in, inc_in):
        cmd = [
            sys.executable, "-c",
            f"""
import sys
sys.path.extend({sys.path})
from edgar_tool.cli import SecEdgarScraperCli
SecEdgarScraperCli.text_search(
    {repr(search_kw)},
    start_date={repr(start_date)},
    end_date={repr(end_date)},
    filing_form={repr(file_type)},
    entity_id={repr(cik)},
    output={repr(csv_output)},
    peo_in={repr(peo_in)},
    inc_in={repr(inc_in)}
)
            """
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process

    def kill_proc_tree(pid, including_parent=True):
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        psutil.wait_procs(children, timeout=5)
        if including_parent:
            parent.kill()
            parent.wait(5)

    def make_clickable(url):
        return f'<a href="{url}" target="_blank">Link</a>'

    def search_edgar(b):
        nonlocal csv_output, csv_content, search_results
        with output:
            output.clear_output()
            print("Searching EDGAR...")
            download_button.layout.display = 'none'
            download_link.value = ''
            
            search_kw = '""' if search_keywords.value == "" else search_keywords.value
            file_type = None if filing_type.value == 'all' else filing_type.value
            cik = None if company_cik.value == '' else company_cik.value
            loc = location.value if filter_by_location.value != '' else None
            
            csv_output = f"edgar_search_results_{datetime.now().strftime('%d%m%Y_%H%M%S')}.csv"
            full_csv_path = os.path.join(results_dir, csv_output)
            
            process = run_search(
                search_kw,
                start_date.value.strftime('%Y-%m-%d'),
                end_date.value.strftime('%Y-%m-%d'),
                file_type,
                cik,
                full_csv_path,
                loc if filter_by_location.value == "Principal executive offices in" else None,
                loc if filter_by_location.value == "Incorporated in" else None
            )
            
            start_time = time.time()
            while process.poll() is None:
                if time.time() - start_time > max_wait.value:
                    print(f"Search timed out after {max_wait.value} seconds. Stopping search.")
                    kill_proc_tree(process.pid)
                    break
                time.sleep(0.1)
            
            if process.returncode == 0:
                print("Search complete.")
            elif process.returncode is None:
                print("Search was forcefully terminated.")
            else:
                print(f"Search process ended with return code {process.returncode}")
                stdout, stderr = process.communicate()
                print("Error output:")
                print(stderr.decode())
            
            try:
                with open(full_csv_path, 'r') as file:
                    csv_content = file.read()
                
                search_results = pd.read_csv(StringIO(csv_content))
                
                if 'filing_document_url' in search_results.columns:
                    cols = ['filing_document_url'] + [col for col in search_results.columns if col != 'filing_document_url']
                    search_results = search_results[cols]
                    search_results['filing_document_url'] = search_results['filing_document_url'].apply(make_clickable)
                    
                    display(HTML(search_results.to_html(escape=False, index=False)))
                else:
                    display(search_results)
                
                download_button.layout.display = 'inline-flex'
                
                print(f"Results saved. Click 'Download' to download the file.")
            except FileNotFoundError:
                print(f"\033[33m No results were found or saved. File not found: {full_csv_path}\033[0m")
            except Exception as e:
                print(f"\033[31m Error processing results: {str(e)}\033[0m")

    search_button.on_click(search_edgar)
    download_button.on_click(download_file)

    display(form)

# Usage
# edgar_search_report("'CFO Resignation'")