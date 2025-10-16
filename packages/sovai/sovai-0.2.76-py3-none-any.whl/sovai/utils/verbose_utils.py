# sovai/utils/verbose_utils.py

import logging
from typing import Optional

logger = logging.getLogger(__name__) # Optional: If the class itself needs logging

class VerboseMode:
    """
    Utility class to handle verbose output throughout the application.

    This class provides a consistent interface for controlling debug output
    without cluttering the main code with conditional print statements.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize verbose mode settings.

        Args:
            verbose: Whether to enable verbose output
        """
        self.verbose = verbose

    def log(self, *args, **kwargs) -> None:
        """
        Print information when verbose mode is enabled.

        Args:
            *args: Arguments to print
            **kwargs: Keyword arguments for print function
        """
        if self.verbose:
            # Consider using logger.info or logger.debug instead of print
            # for better logging control, but using print matches original code.
            print(*args, **kwargs)

    def toggle_verbose(self, verbose: Optional[bool] = None) -> None:
        """
        Toggle or set verbose mode.

        Args:
            verbose: If provided, set verbose mode to this value; otherwise toggle
        """
        if verbose is None:
            self.verbose = not self.verbose
        else:
            self.verbose = verbose

# Instantiate the global verbose mode handler here
verbose_mode = VerboseMode()