"""
Ngawari - A simple and functional toolkit for working with data in VTK.

This package provides utilities for VTK data manipulation, filtering, and processing.
"""

__version__ = "0.1.7"
__author__ = "Fraser M. Callaghan"
__email__ = "callaghan.fm@gmail.com"

# Import main modules
from . import ftk
from . import fIO
from . import vtkfilters

# Make commonly used functions available at package level
from .ftk import *
from .fIO import *
from .vtkfilters import *

__all__ = []
__all__.extend(ftk.__all__ if hasattr(ftk, '__all__') else [])
__all__.extend(fIO.__all__ if hasattr(fIO, '__all__') else [])
__all__.extend(vtkfilters.__all__ if hasattr(vtkfilters, '__all__') else [])
