import asyncio
import concurrent.futures
import threading
import functools
import inspect
from typing import Optional, Dict, Any, Union, TYPE_CHECKING
from geopandas import GeoDataFrame
from shapely.geometry.base import BaseGeometry as ShapelyGeometry
from .async_client import AsyncClient

# Add type checking imports for better IDE support
if TYPE_CHECKING:
    from .endpoints.dataset_management import DatasetManagement
    from .endpoints.user_management import UserManagement
    from .endpoints.mass_stats import MassStats
    from .endpoints.group_management import GroupManagement
    from .endpoints.space_management import SpaceManagement
    from .endpoints.model_management import ModelManagement
    from .endpoints.auth import AuthClient


class SyncWrapper:
    """Generic synchronous wrapper with __dir__ support for runtime autocomplete."""
    
    def __init__(self, async_obj, sync_client):
        self._async_obj = async_obj
        self._sync_client = sync_client
    
    def __dir__(self):
        """Return list of attributes for autocomplete in interactive environments."""
        async_attrs = [attr for attr in dir(self._async_obj) if not attr.startswith('_')]
        wrapper_attrs = [attr for attr in object.__dir__(self) if not attr.startswith('_')]
        return list(set(async_attrs + wrapper_attrs))
    
    def __getattr__(self, name):
        """Dynamically wrap any method call to convert async to sync."""
        attr = getattr(self._async_obj, name)
        
        if callable(attr):
            @functools.wraps(attr)
            def sync_wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                if hasattr(result, '__await__'):
                    return self._sync_client._run_async(result)
                return result
            return sync_wrapper
        
        return attr


class SyncClient:
    """
    Thread-safe synchronous wrapper for AsyncClient.
    Uses a persistent event loop in a dedicated thread to avoid event loop conflicts.
    """

    # Add explicit type annotations for endpoint managers
    datasets: 'DatasetManagement'
    users: 'UserManagement' 
    mass_stats: 'MassStats'
    groups: 'GroupManagement'
    space: 'SpaceManagement'
    model: 'ModelManagement'
    auth: 'AuthClient'
    
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, verbose: bool = False):
        self._async_client = AsyncClient(url=url, api_key=api_key, verbose=verbose)
        self._context_entered = False
        self._closed = False
        
        # Thread and event loop management
        self._loop = None
        self._thread = None
        self._loop_ready = None
        self._loop_exception = None
        
        # Initialize endpoint managers with proper typing

        self.datasets = SyncWrapper(self._async_client.datasets, self)
        self.users = SyncWrapper(self._async_client.users, self)
        self.mass_stats = SyncWrapper(self._async_client.mass_stats, self)
        self.groups = SyncWrapper(self._async_client.groups, self)
        self.space = SyncWrapper(self._async_client.space, self)
        self.model = SyncWrapper(self._async_client.model, self)
        self.auth = SyncWrapper(self._async_client.auth, self)
        
        import atexit
        atexit.register(self._cleanup)
    
    def _ensure_event_loop(self) -> None:
        """Ensure we have a persistent event loop in a dedicated thread."""
        if self._loop is None or self._loop.is_closed():
            self._loop_ready = threading.Event()
            self._loop_exception = None
            
            def run_loop():
                """Run the event loop in a dedicated thread."""
                try:
                    # Create a new event loop for this thread
                    self._loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._loop)
                    
                    # Signal that the loop is ready
                    self._loop_ready.set()
                    
                    # Run the loop forever (until stopped)
                    self._loop.run_forever()
                except Exception as e:
                    self._loop_exception = e
                    self._loop_ready.set()
                finally:
                    # Clean up when the loop stops
                    if self._loop and not self._loop.is_closed():
                        self._loop.close()
            
            # Start the thread
            self._thread = threading.Thread(target=run_loop, daemon=True)
            self._thread.start()
            
            # Wait for the loop to be ready
            self._loop_ready.wait(timeout=10)
            
            if self._loop_exception:
                raise self._loop_exception
            
            if not self._loop_ready.is_set():
                raise RuntimeError("Event loop failed to start within timeout")
    
    def _run_async(self, coro):
        """
        Run async coroutine using persistent event loop.
        This is the core method that makes everything work.
        """
        # Ensure we have an event loop
        self._ensure_event_loop()
        
        if self._loop.is_closed():
            raise RuntimeError("Event loop is closed")
        
        # Create a future to get the result back from the event loop thread
        future = concurrent.futures.Future()
        
        async def run_with_context():
            """Run the coroutine with proper context management."""
            try:
                # Ensure the async client is properly initialized
                await self._ensure_context()
                
                # Run the actual coroutine
                result = await coro
                
                # Set the result on the future
                future.set_result(result)
            except Exception as e:
                # Set the exception on the future
                future.set_exception(e)
        
        # Schedule the coroutine on the persistent event loop
        self._loop.call_soon_threadsafe(
            lambda: asyncio.create_task(run_with_context())
        )

        return future.result()
    
    async def _ensure_context(self) -> None:
        """Ensure the async client context is entered."""
        if not self._context_entered and not self._closed:
            await self._async_client.__aenter__()
            self._context_entered = True
    
    async def _exit_context(self) -> None:
        """Exit the async client context."""
        if self._context_entered and not self._closed:
            await self._async_client.__aexit__(None, None, None)
            self._context_entered = False
    
    def close(self) -> None:
        """Close the underlying async client session and stop the event loop."""
        if not self._closed:
            if self._loop and not self._loop.is_closed():
                # Schedule cleanup on the event loop
                future = concurrent.futures.Future()
                
                async def cleanup():
                    """Clean up the async client."""
                    try:
                        await self._exit_context()
                        future.set_result(None)
                    except Exception as e:
                        future.set_exception(e)
                
                # Run cleanup
                self._loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(cleanup())
                )
                
                # Wait for cleanup to complete
                try:
                    future.result(timeout=10)
                except:
                    pass  # Ignore cleanup errors
                
                # Stop the event loop
                self._loop.call_soon_threadsafe(self._loop.stop)
                
                # Wait for thread to finish
                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=5)
            
            self._closed = True
    
    def _cleanup(self) -> None:
        """Internal cleanup method called by atexit."""
        if not self._closed:
            try:
                self.close()
            except Exception:
                pass  # Ignore cleanup errors
    
    def __dir__(self):
        """Return list of attributes for autocomplete in interactive environments."""
        default_attrs = [attr for attr in object.__dir__(self) if not attr.startswith('_')]
        async_client_attrs = [attr for attr in dir(self._async_client) if not attr.startswith('_')]
        endpoint_attrs = ['datasets', 'users', 'mass_stats', 'groups', 'space', 'model', 'auth']
        all_attrs = default_attrs + async_client_attrs + endpoint_attrs
        return list(set(all_attrs))
    
    # Your existing methods with proper type annotations
    def geoquery(
        self,
        expr: str,
        feature: Union[Dict[str, Any], ShapelyGeometry],
        in_crs: str = "epsg:4326",
        out_crs: str = "epsg:4326",
        resolution: int = -1,
        geom_fix: bool = False,
        **kwargs
    ):
        """Compute WCS query for a single geometry (synchronous version)."""
        coro = self._async_client.geoquery(
            expr=expr,
            feature=feature,
            in_crs=in_crs,
            out_crs=out_crs,
            output="netcdf",
            resolution=resolution,
            geom_fix=geom_fix,
            **kwargs
        )
        return self._run_async(coro)

    def zonal_stats(self, *args, **kwargs) -> GeoDataFrame:
        """Proxy to async zonal_stats with full argument passthrough (sync wrapper)."""
        coro = self._async_client.zonal_stats(*args, **kwargs)
        return self._run_async(coro)
    
    def create_dataset_file(self, *args, **kwargs) -> dict:
        """Proxy to async create_dataset_file with full argument passthrough (sync wrapper)."""
        coro = self._async_client.create_dataset_file(*args, **kwargs)
        return self._run_async(coro)


    def geo_queries(self, *args, **kwargs) -> Union[float, GeoDataFrame]:
        """Proxy to async geo_queries with full argument passthrough (sync wrapper)."""
        coro = self._async_client.geo_queries(*args, **kwargs)
        return self._run_async(coro)
    
    # Context manager support
    def __enter__(self) -> 'SyncClient':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
    
    def __del__(self) -> None:
        """Destructor to ensure session is closed."""
        if not self._closed:
            try:
                self._cleanup()
            except Exception:
                pass