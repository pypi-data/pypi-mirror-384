"""
This package is used to specify the error codes used within C-AD.

Error codes are split among various modules, which are logically grouped into Enums
within this package. 
"""

from .base import CADError
from .rhic_errors import RhicError

__all__ = ["CADError", "RhicError"]
