# read version from installed package
from importlib.metadata import version
__version__ = version("qatarcars")

from qatarcars.cars import get_qatar_cars
