import importlib as il
import logging
from types import FunctionType
from ._errors import *                   # noqa: F401,F403
from ._utils import (
    check_dataframe_types,
    return_read_function,
    check_import_package,
)

logger = logging.getLogger(__name__)


def get_qatar_cars(dataframe_type: str = "pandas") -> FunctionType:
    """
    Load the built‑in *Qatar cars* CSV dataset into a dataframe.

    The Qatar cars dataset is a dataset for teaching, learning, and
    data exploration intended to serve a more contemporary and 
    international audience compared to the `mtcars` dataframe 
    seen in, e.g., `pandas.` Data was originally compiled by Paul
    Musgrave and his students as part of a statistics course for
    International Politics majors at Georgetown University in 2025. 

    Read more in the :ref:`https://github.com/profmusgrave/qatarcars/tree/main`.

    The function is very lightweight: it merely resolves the user’s
    desired dataframe flavour (Pandas or Polars), ensures the
    corresponding package is available, and delegates the actual CSV
    ingestion to the appropriate ``read_csv`` implementation.

    Parameters
    ----------
    dataframe_type : str, default ``"pandas"``
        Short or full name of the dataframe package that should be used
        to read the CSV file.  Accepted values (case‑insensitive) are:

        * ``'pd'`` or ``'pandas'`` → Pandas
        * ``'pl'`` or ``'polars'`` → Polars

        Any other value results in :class:`TypeError` via the
        :data:`df_assert_error` exception defined in ``_errors``.
        The mapping is normalised to the canonical package name
        (`"pandas"` or `"polars"`) which is stored in `df_type`.

    Returns
    -------
    :class:`pandas.DataFrame` or :class:`polars.DataFrame`
        A dataframe containing the *Qatar cars* data.  The concrete type
        depends on the package that was selected by :func:`check_dataframe_types`. 
        Either is of shape (89, 15) the following columns:
        =================   ==============
        origin              a string denoting nation of origin of the car
        make                a string denoting the manufacturer/brand of the car
        model               a string denoting the specific type of the car
        length              a float denoting the car's length (in meters)
        width               a float denoting the car's width (in meters)
        height              a float denoting the car's height (in meters)
        seating             an integer denoting how many seats are within the car
        trunk               an integer denoting the trunk's volume (in liters)
        economy             a float denoting how many liters of fuel is required to travel 100km
        performance         a float denoting how many seconds it takes to accelerate to 100km/h from a dead stop
        mass                a float of the car's mass (in kg)
        horsepower          an integer denoting the car's horsepower
        price               an integer denoting the car's price (QAR)               
        type                a string denoting the body-type of the car
        enginetype          a string denoting the type of fuel/energy used by the engine
        =================   ==============

    Raises
    ------
    :class:`df_assert_error`
        If *dataframe_type* is not one of the supported options.  The
        error message is defined in ``_errors``.

    :class:`ImportError`
        If the requested dataframe package is not installed in the
        current environment.  The function first calls
        :func:`check_import_package`; if it returns ``False`` an
        ``ImportError`` is raised with a short explanatory message.

    :class:`Exception`
        Generic ``Exception`` (the original code only raised a bare
        ``Exception``) when the import check fails.  In a real
        library you would replace this with a more specific exception
        class, e.g. ``RuntimeError``.

    Notes
    -----
    * The function uses :mod:`importlib.resources` to access the CSV
      file that is vendored inside the ``qatarcars.data`` package.
      The file is **not** read into memory twice – the selected
      ``read_csv`` function (Pandas or Polars) receives a file‑like
      path directly.
    * ``df_assert_error`` is imported from ``_errors`` and should
      contain a clear, user‑friendly error message.  The assertion
      line is intentionally written as an ``assert`` so that it can
      be disabled when Python is run with the ``-O`` optimisation
      flag.

    Example
    -------
    >>> from qatarcars import get_qatar_cars
    >>> df = get_qatar_cars("pandas")
    >>> type(df)
    <class 'pandas.core.frame.DataFrame'>
    >>> df.head()
      Origin  make  model  length  ...  type  enginetype
    0  Audi   A3   3 Series Convertible  4.713   ...  Coupe    Petrol

    """
    # --- Resolve user input -------------------------------------------------
    df_type = check_dataframe_types(dataframe_type)

    # Validate mapping – ``check_dataframe_types`` returns the canonical
    # name or ``False``.  The assertion uses the custom error type
    # exported from ``._errors``.
    assert isinstance(df_type, str), df_assert_error

    # --- Ensure the backend package can be imported -------------------------
    if not check_import_package(df_type):
        raise Exception

    # --- Retrieve the backend's ``read_csv`` implementation ----------------
    read_func = return_read_function(df_type)

    # --- Load the packaged CSV ------------------------------------------------
    # ``importlib.resources.path`` gives us a context‑manager
    # that yields a ``pathlib.Path`` pointing to the embedded file.
    with il.resources.path("qatarcars.data", "qatarcars.csv") as csv_path:
        return read_func(csv_path)