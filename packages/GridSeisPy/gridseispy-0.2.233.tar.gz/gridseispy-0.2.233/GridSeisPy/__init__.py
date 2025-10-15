"""
SeisPy is a Python library for seismic data processing.
"""

__version__ = "0.2.233"

from .seis_data import SeisData
from .horiz import Horiz
from .mapping import TraceField, BinField, CVDFile, Trace


"""
       py -m build
       py -m twine check dist/*
       py -m twine upload --non-interactive -r pypi dist/*
"""
