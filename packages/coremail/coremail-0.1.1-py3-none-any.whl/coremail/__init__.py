"""
Coremail SDK for Python
A library for interacting with Coremail XT API
"""
from .client import CoremailClient
from . import typings

__version__ = "0.1.0"
__all__ = ["CoremailClient", "typings"]