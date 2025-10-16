"""weathergrabber - Python interface and CLI for weather.com data."""

from .core import main
from .cli import main_cli

__all__ = ["main", "main_cli"]
__version__ = "0.0.8b3"

def get_version():
    return __version__