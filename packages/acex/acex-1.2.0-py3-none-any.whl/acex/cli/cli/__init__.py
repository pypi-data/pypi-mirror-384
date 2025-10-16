"""
ACEX CLI module
"""

from .main import app as cli_app
from .commands import *

__all__ = ["cli_app"]
