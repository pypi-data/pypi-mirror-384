# terrakio_core/__init__.py
"""
Terrakio Core

Core components for Terrakio API clients.
"""

# Suppress ONNX Runtime GPU device discovery warnings - MUST BE FIRST!
import os
os.environ['ORT_LOGGING_LEVEL'] = '3'
__version__ = "0.4.98.1"

from .async_client import AsyncClient
from .sync_client import SyncClient as Client
from . import accessors

__all__ = [
    "AsyncClient", 
    "Client"
]