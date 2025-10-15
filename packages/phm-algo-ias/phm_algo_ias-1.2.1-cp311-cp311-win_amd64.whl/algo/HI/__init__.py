__version__ = "0.0.2"
from . import HI
from .HI import *

__all__ = ["HI"]
__all__ += HI.__all__
# print("pythonds was called")