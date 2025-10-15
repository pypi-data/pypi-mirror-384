"""
Main SovAI SDK Tool Kit package
"""
from .api_config import read_key, save_key, ApiConfig
from .basic_auth import basic_auth
from .token_auth import token_auth
from .utils.file_management import update_data_files # Keep update_data_files import
from .api_config import read_key, ApiConfig



import warnings
warnings.filterwarnings("ignore")
update_data_files()

try:
    read_key(".env")
except FileNotFoundError:
    pass

try:
    from importlib.metadata import version
    __version__ = version("sovai")
except:
    __version__ = "0.2.49"  # Fallback to current version in pyproject.toml


# Lazy loading for core modules
_data_module = None

def data(*args, **kwargs):
    """Lazy-loaded access to the data function."""
    global _data_module
    if _data_module is None:
        from .get_data import data as _loaded_data
        _data_module = _loaded_data
    return _data_module(*args, **kwargs)


# Lazy loading for full installation modules
HAS_FULL_INSTALL = False
_plot_module = None
_report_module = None
_compute_module = None
_nowcast_module = None
_extension_module = None
_sec_search_module = None
_sec_filing_module = None
_code_module = None
_sec_graph_module = None

try:
    # Attempt to import a module from the full installation to check if it's installed
    # This import is just to check for ImportError, the actual function is lazy-loaded below
    from .get_plots import plot as _ # Use _ to indicate this import is just for the check
    HAS_FULL_INSTALL = True

    def plot(*args, **kwargs):
        """Lazy-loaded access to the plot function."""
        global _plot_module
        if _plot_module is None:
            from .get_plots import plot as _loaded_plot
            _plot_module = _loaded_plot
        return _plot_module(*args, **kwargs)

    def report(*args, **kwargs):
        """Lazy-loaded access to the report function."""
        global _report_module
        if _report_module is None:
            from .get_reports import report as _loaded_report
            _report_module = _loaded_report
        return _report_module(*args, **kwargs)

    def compute(*args, **kwargs):
        """Lazy-loaded access to the compute function."""
        global _compute_module
        if _compute_module is None:
            from .get_compute import compute as _loaded_compute
            _compute_module = _loaded_compute
        return _compute_module(*args, **kwargs)

    def nowcast(*args, **kwargs):
        """Lazy-loaded access to the nowcast function."""
        global _nowcast_module
        if _nowcast_module is None:
            from .studies.nowcasting import nowcast as _loaded_nowcast
            _nowcast_module = _loaded_nowcast
        return _nowcast_module(*args, **kwargs)

    # extension is likely a class, so the lazy loader needs to return the class itself
    def extension(*args, **kwargs):
        """Lazy-loaded access to the CustomDataFrame extension class."""
        global _extension_module
        if _extension_module is None:
            from .extensions.pandas_extensions import CustomDataFrame as _loaded_extension
            _extension_module = _loaded_extension
        # If called with args/kwargs, assume it's being instantiated
        if args or kwargs:
             return _extension_module(*args, **kwargs)
        # Otherwise, return the class itself (e.g., for type checking or accessing class methods)
        return _extension_module


    def sec_search(*args, **kwargs):
        """Lazy-loaded access to the sec_search function."""
        global _sec_search_module
        if _sec_search_module is None:
            from .get_tools import sec_search as _loaded_sec_search
            _sec_search_module = _loaded_sec_search
        return _sec_search_module(*args, **kwargs)

    def sec_filing(*args, **kwargs):
        """Lazy-loaded access to the sec_filing function."""
        global _sec_filing_module
        if _sec_filing_module is None:
            from .get_tools import sec_filing as _loaded_sec_filing
            _sec_filing_module = _loaded_sec_filing
        return _sec_filing_module(*args, **kwargs)

    def code(*args, **kwargs):
        """Lazy-loaded access to the code function."""
        global _code_module
        if _code_module is None:
            from .get_tools import code as _loaded_code
            _code_module = _loaded_code
        return _code_module(*args, **kwargs)

    def sec_graph(*args, **kwargs):
        """Lazy-loaded access to the sec_graph function."""
        global _sec_graph_module
        if _sec_graph_module is None:
            from .get_tools import sec_graph as _loaded_sec_graph
            _sec_graph_module = _loaded_sec_graph
        return _sec_graph_module(*args, **kwargs)


except ImportError as e:
    print("this is the lean installation, for full use sovai[full]")
    # print(f"ImportError: {e}")
    HAS_FULL_INSTALL = False

    # Define dummy functions/objects for lean installation to avoid AttributeErrors
    def plot(*args, **kwargs):
        raise ImportError("Plotting requires the full installation. Install with 'pip install sovai[full]'")
    def report(*args, **kwargs):
        raise ImportError("Reporting requires the full installation. Install with 'pip install sovai[full]'")
    def compute(*args, **kwargs):
        raise ImportError("Compute requires the full installation. Install with 'pip install sovai[full]'")
    def nowcast(*args, **kwargs):
        raise ImportError("Nowcasting requires the full installation. Install with 'pip install sovai[full]'")
    def extension(*args, **kwargs):
         raise ImportError("Extensions require the full installation. Install with 'pip install sovai[full]'")
    def sec_search(*args, **kwargs):
        raise ImportError("SEC tools require the full installation. Install with 'pip install sovai[full]'")
    def sec_filing(*args, **kwargs):
        raise ImportError("SEC tools require the full installation. Install with 'pip install sovai[full]'")
    def code(*args, **kwargs):
        raise ImportError("SEC tools require the full installation. Install with 'pip install sovai[full]'")
    def sec_graph(*args, **kwargs):
        raise ImportError("SEC tools require the full installation. Install with 'pip install sovai[full]'")


__all__ = [
    'read_key', 'save_key', 'ApiConfig', 'basic_auth', 'token_auth',
    'update_data_files', # Keep update_data_files in __all__
    'data', # Add data to __all__
]

# Add full installation lazy-loaded attributes to __all__ if available
if HAS_FULL_INSTALL:
    __all__ += [
        'plot', 'report', 'compute', 'nowcast', 'extension',
        'sec_search', 'sec_filing', 'code', 'sec_graph'
    ]
