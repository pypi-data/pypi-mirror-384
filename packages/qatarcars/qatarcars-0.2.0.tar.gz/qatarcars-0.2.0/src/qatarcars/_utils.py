"""
Data‑package helpers for importing packages and normalising dataframe flavours.

The module contains a small set of utility functions that

* map short user input (e.g. ``'pd'``) to a canonical dataframe package name
  (`pandas` or `polars`);
* obtain a reference to the package’s ``read_csv`` routine once the package
  is known to be importable; and
* perform a quick check/installation of a package – importing it if it is
  already installed, otherwise printing a user‑friendly error message.

These helpers are intentionally lightweight: they operate on the *module*
level (`sys.modules`) instead of importing the heavy packages directly
(`import pandas as pd` etc.).  This keeps import times low and allows
the functions to be re‑used by both the library itself and downstream
code such as command‑line tools or notebooks.
"""

import importlib as il
import sys
import logging
from types import FunctionType
from typing import Union
from colorama import Fore, Style

# Local imports ---------------------------------------------------------------
from ._errors import *  # noqa: F401,F403

# ----------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------

def check_dataframe_types(dataframe_type: str) -> Union[bool, str]:
    """
    Validate a user‑supplied dataframe type.

    The function accepts a string that represents a dataframe package.  The
    following abbreviations are recognised:

    * ``'pd'`` or ``'pandas'``   → ``'pandas'``
    * ``'pl'`` or ``'polars'``   → ``'polars'``

    Parameters
    ----------
    dataframe_type : str
        The value supplied by the user.  Matching is performed
        case‑insensitively.

    Returns
    -------
    bool | str
        ``True`` is returned when the supplied type is recognised – the
        returned value is a canonical package name (`'pandas'` or
        `'polars'`).  If the input is invalid, ``False`` is returned.

    Examples
    --------
    >>> check_dataframe_types('pd')
    'pandas'
    >>> check_dataframe_types('UNKNOWN')
    False

    """
    acceptable_dict = {
        'pd': 'pandas',
        'pandas': 'pandas',
        'pl': 'polars',
        'polars': 'polars',
    }
    key = dataframe_type.lower()
    if key in acceptable_dict:
        logger.info('User input an appropriate dataframe type')
        return acceptable_dict[key]
    return False

# ---------------------------------------------------------------------------

def return_read_function(pkg: str) -> FunctionType:
    """
    Return the CSV‑reading function for a given package.

    The function expects that *pkg* is already present in :data:`sys.modules`.
    Supported packages are currently only ``pandas`` and ``polars`` – both
    expose a top‑level ``read_csv`` routine.

    Parameters
    ----------
    pkg : str
        The package name as it appears in :data:`sys.modules` (e.g.
        ``'pandas'`` or ``'polars'``).

    Returns
    -------
    FunctionType
        Reference to the package’s ``read_csv`` callable.

    Raises
    ------
    KeyError
        If *pkg* has not been imported yet (i.e. missing from
        ``sys.modules``).
    ValueError
        If *pkg* is recognised but does not provide a ``read_csv`` attribute
        – this should not normally happen for the supported packages.

    Examples
    --------
    >>> import pandas as pd
    >>> fn = return_read_function('pandas')
    >>> callable(fn)
    True
    >>> import polars as pl
    >>> fn = return_read_function('polars')
    >>> callable(fn)
    True
    """
    module = sys.modules[pkg]          # may raise KeyError if pkg not loaded

    if pkg in ['polars', 'pandas']:
        read_fn = module.read_csv
        if not callable(read_fn):
            raise ValueError(f"The module '{pkg}' does not provide a "
                             "callable `read_csv` function.")
        return read_fn

    # Defensive guard – future‑proofing if new packages are added
    raise ValueError(f"Unsupported package '{pkg}'. "
                     "Supported packages: 'pandas', 'polars'.")

# ---------------------------------------------------------------------------

def check_import_package(pkg: str) -> bool:
    """
    Ensure a package is available in the running interpreter.

    * If the package is already imported (present in :data:`sys.modules`),
      the function merely acknowledges this state.
    * Otherwise it checks whether the package can be found via
      :func:`importlib.util.find_spec`; if found it loads the module,
      inserts it into :data:`sys.modules` and reports success.
    * If the package is not installed at all, a brief error message is
      printed to the console and ``False`` is returned.

    Parameters
    ----------
    pkg : str
        The dotted name of the package to check.

    Returns
    -------
    bool
        ``True`` when the package could be imported (either already
        imported or freshly loaded), ``False`` otherwise.

    Examples
    --------
    >>> check_import_package('pandas')
    True      # will return False if Pandas is not installed on the system

    See Also
    --------
    :mod:`importlib` – the underlying module used for dynamic import.
    """
    if pkg in sys.modules:
        logger.info(f"Package {pkg} is already imported")
        return True

    spec = il.util.find_spec(pkg)
    if spec is not None:
        logger.info(f"Package {pkg} is already installed.")
        mod = il.util.module_from_spec(spec)
        sys.modules[pkg] = mod
        spec.loader.exec_module(mod)  # type: ignore[assignment]
        logger.info(f"Package {pkg} successfully imported")
        return True

    # Package not found on the system
    print(Fore.RED + f"Package '{pkg}' is not installed!" + Style.RESET_ALL)
    print("Try to find it using installers such as conda, uv, or pip.")
    return False
