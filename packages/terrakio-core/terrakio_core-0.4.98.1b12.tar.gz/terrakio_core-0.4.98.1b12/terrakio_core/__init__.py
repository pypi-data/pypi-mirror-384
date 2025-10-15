# terrakio_core/__init__.py
"""
Terrakio Core

Core components for Terrakio API clients.
"""

__version__ = "0.4.98"

from .async_client import AsyncClient
from .sync_client import SyncClient as Client
from . import accessors

# Suppress ONNX Runtime GPU device discovery warnings
import os
os.environ['ORT_LOGGING_LEVEL'] = '3'

__all__ = [
    "AsyncClient", 
    "Client"
]