"""
Type hints for the coremail_sdk package
"""
from .client import CoremailClient
from .api import CoremailAPI
from .typings import *

__all__ = [
    "CoremailClient",
    "CoremailAPI",
    "TokenResponse",
    "AuthenticateResponse", 
    "GetAttrsResponse",
    "UserAttributes",
    "CoremailConfig"
]