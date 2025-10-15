from .tools.sec.sec_edgar_search import edgar_search_report

from .tools.sec.sec_10_k_8_k_filings import large_filing_module

from .tools.sec.llm_code_generator import generate_sovai_code

from .tools.sec.graphs import analyze_10k_graph

import pandas as pd


def sec_search(search="CFO Resgination"):

    return edgar_search_report(search)




def sec_filing(ticker="AAPL", form="10-Q", date_input="2023-Q3", verbose=False):

    return large_filing_module(ticker, form=form, date_input=date_input, verbose=verbose)



def code(prompt="get bankruptcy data for Tesla", verbose=False, run=False):

    return generate_sovai_code(prompt, verbose=verbose, run=run)


from typing import Optional, Union

def sec_graph(
    ticker: str = "AAPL", 
    date: str = "2024-Q3", 
    verbose: bool = False, 
    ontology_type: str = "causal", 
    oai_model: str = "gpt-4o-mini", 
    batch: bool = True, 
    batch_size: int = 10, 
    sentiment_filter: Optional[Union[float, bool]] = None,  # Can be a float or a boolean for flexibility
    output_dir: str = "./docs", 
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Generate a knowledge graph from 10-K SEC filings for a given ticker using the specified ontology type.

    Parameters:
    - ticker (str): Ticker symbol (e.g., AAPL for Apple Inc.)
    - date (str): Filing date or quarter (default: "2024-Q3").
    - verbose (bool): Whether to print detailed logs.
    - ontology_type (str): The ontology type to use for analysis. Choose from:
      - "connection", "causal", "temporal", "stakeholder", "innovation", "esg", "sentiment"
    - oai_model (str): OpenAI model to use (default: "gpt-4o-mini").
    - batch (bool): Whether to process documents in batches.
    - batch_size (int): Number of documents to process in a batch (default: 10).
    - sentiment_filter (Optional[Union[float, bool]]): Filter by sentiment scores or leave as None for no filter.
    - output_dir (str): Directory to save graph outputs (default: "./docs").
    - use_cache (bool): Whether to use cached results to speed up analysis.

    Returns:
    - pd.DataFrame: DataFrame representing the generated graph with nodes and relationships.
    """

    # Ensure ontology type is valid
    ontology = ["connection", "causal", "temporal", "stakeholder", "innovation", "esg", "sentiment"]
    
    if ontology_type not in ontology:
        raise ValueError(f"Invalid ontology type: {ontology_type}. Must be one of: {ontology}")

    return analyze_10k_graph(
        ticker=ticker, 
        date=date, 
        section_select=True, 
        ontology_type=ontology_type, 
        oai_model=oai_model, 
        batch=batch, 
        batch_size=batch_size, 
        sentiment_filter=sentiment_filter, 
        output_dir=output_dir, 
        use_cache=use_cache, 
        verbose=verbose
    )
