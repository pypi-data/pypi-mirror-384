# import asyncio
# import concurrent.futures
# import threading
# import functools
# import inspect
# from typing import Optional, Dict, Any, Union
# from geopandas import GeoDataFrame
# from shapely.geometry.base import BaseGeometry as ShapelyGeometry
# from .async_client import AsyncClient
# from typing import TYPE_CHECKING

# # # Add this after your other imports
# # if TYPE_CHECKING:
# #     from .endpoints.dataset_management import DatasetManagement
# #     from .endpoints.user_management import UserManagement
# #     from .endpoints.mass_stats import MassStats
# #     from .endpoints.group_management import GroupManagement
# #     from .endpoints.space_management import SpaceManagement
# #     from .endpoints.model_management import ModelManagement
# #     from .endpoints.auth import AuthClient


# class SyncWrapper:
#     """Generic synchronous wrapper with __dir__ support for runtime autocomplete."""
    
#     def __init__(self, async_obj, sync_client):
#         self._async_obj = async_obj
#         self._sync_client = sync_client
    
#     def __dir__(self):
#         """Return list of attributes for autocomplete in interactive environments."""
#         async_attrs = [attr for attr in dir(self._async_obj) if not attr.startswith('_')]
#         wrapper_attrs = [attr for attr in object.__dir__(self) if not attr.startswith('_')]
#         return list(set(async_attrs + wrapper_attrs))
    
#     def __getattr__(self, name):
#         """Dynamically wrap any method call to convert async to sync."""
#         attr = getattr(self._async_obj, name)
        
#         if callable(attr):
#             @functools.wraps(attr)
#             def sync_wrapper(*args, **kwargs):
#                 result = attr(*args, **kwargs)
#                 if hasattr(result, '__await__'):
#                     return self._sync_client._run_async(result)
#                 return result
#             return sync_wrapper
        
#         return attr


# class SyncClient:
#     """
#     Thread-safe synchronous wrapper for AsyncClient.
#     Uses a persistent event loop in a dedicated thread to avoid event loop conflicts.
#     """

#     # datasets: 'DatasetManagement'
#     # users: 'UserManagement' 
#     # mass_stats: 'MassStats'
#     # groups: 'GroupManagement'
#     # space: 'SpaceManagement'
#     # model: 'ModelManagement'
#     # auth: 'AuthClient'
    
#     def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, verbose: bool = False):
#         self._async_client = AsyncClient(url=url, api_key=api_key, verbose=verbose)
#         self._context_entered = False
#         self._closed = False
        
#         # Thread and event loop management
#         self._loop = None
#         self._thread = None
#         self._loop_ready = None
#         self._loop_exception = None
        
#         # Initialize endpoint managers
#         print("we are here!!!!!!!!!!!!!!!!!")
#         self.datasets = SyncWrapper(self._async_client.datasets, self)
#         self.users = SyncWrapper(self._async_client.users, self)
#         self.mass_stats = SyncWrapper(self._async_client.mass_stats, self)
#         self.groups = SyncWrapper(self._async_client.groups, self)
#         self.space = SyncWrapper(self._async_client.space, self)
#         self.model = SyncWrapper(self._async_client.model, self)
#         self.auth = SyncWrapper(self._async_client.auth, self)
        
#         # Register cleanup
#         import atexit
#         atexit.register(self._cleanup)
    
#     def _ensure_event_loop(self):
#         """Ensure we have a persistent event loop in a dedicated thread."""
#         if self._loop is None or self._loop.is_closed():
#             self._loop_ready = threading.Event()
#             self._loop_exception = None
            
#             def run_loop():
#                 """Run the event loop in a dedicated thread."""
#                 try:
#                     # Create a new event loop for this thread
#                     self._loop = asyncio.new_event_loop()
#                     asyncio.set_event_loop(self._loop)
                    
#                     # Signal that the loop is ready
#                     self._loop_ready.set()
                    
#                     # Run the loop forever (until stopped)
#                     self._loop.run_forever()
#                 except Exception as e:
#                     self._loop_exception = e
#                     self._loop_ready.set()
#                 finally:
#                     # Clean up when the loop stops
#                     if self._loop and not self._loop.is_closed():
#                         self._loop.close()
            
#             # Start the thread
#             self._thread = threading.Thread(target=run_loop, daemon=True)
#             self._thread.start()
            
#             # Wait for the loop to be ready
#             self._loop_ready.wait(timeout=10)
            
#             if self._loop_exception:
#                 raise self._loop_exception
            
#             if not self._loop_ready.is_set():
#                 raise RuntimeError("Event loop failed to start within timeout")
    
#     def _run_async(self, coro):
#         """
#         Run async coroutine using persistent event loop.
#         This is the core method that makes everything work.
#         """
#         # Ensure we have an event loop
#         self._ensure_event_loop()
        
#         if self._loop.is_closed():
#             raise RuntimeError("Event loop is closed")
        
#         # Create a future to get the result back from the event loop thread
#         future = concurrent.futures.Future()
        
#         async def run_with_context():
#             """Run the coroutine with proper context management."""
#             try:
#                 # Ensure the async client is properly initialized
#                 await self._ensure_context()
                
#                 # Run the actual coroutine
#                 result = await coro
                
#                 # Set the result on the future
#                 future.set_result(result)
#             except Exception as e:
#                 # Set the exception on the future
#                 future.set_exception(e)
        
#         # Schedule the coroutine on the persistent event loop
#         self._loop.call_soon_threadsafe(
#             lambda: asyncio.create_task(run_with_context())
#         )
        
#         # Wait for the result (with timeout to avoid hanging)
#         try:
#             return future.result(timeout=300)  # 5 minute timeout
#         except concurrent.futures.TimeoutError:
#             raise RuntimeError("Async operation timed out after 5 minutes")
    
#     async def _ensure_context(self):
#         """Ensure the async client context is entered."""
#         if not self._context_entered and not self._closed:
#             await self._async_client.__aenter__()
#             self._context_entered = True
    
#     async def _exit_context(self):
#         """Exit the async client context."""
#         if self._context_entered and not self._closed:
#             await self._async_client.__aexit__(None, None, None)
#             self._context_entered = False
    
#     def close(self):
#         """Close the underlying async client session and stop the event loop."""
#         if not self._closed:
#             if self._loop and not self._loop.is_closed():
#                 # Schedule cleanup on the event loop
#                 future = concurrent.futures.Future()
                
#                 async def cleanup():
#                     """Clean up the async client."""
#                     try:
#                         await self._exit_context()
#                         future.set_result(None)
#                     except Exception as e:
#                         future.set_exception(e)
                
#                 # Run cleanup
#                 self._loop.call_soon_threadsafe(
#                     lambda: asyncio.create_task(cleanup())
#                 )
                
#                 # Wait for cleanup to complete
#                 try:
#                     future.result(timeout=10)
#                 except:
#                     pass  # Ignore cleanup errors
                
#                 # Stop the event loop
#                 self._loop.call_soon_threadsafe(self._loop.stop)
                
#                 # Wait for thread to finish
#                 if self._thread and self._thread.is_alive():
#                     self._thread.join(timeout=5)
            
#             self._closed = True
    
#     def _cleanup(self):
#         """Internal cleanup method called by atexit."""
#         if not self._closed:
#             try:
#                 self.close()
#             except Exception:
#                 pass  # Ignore cleanup errors
    
#     def __dir__(self):
#         """Return list of attributes for autocomplete in interactive environments."""
#         default_attrs = [attr for attr in object.__dir__(self) if not attr.startswith('_')]
#         async_client_attrs = [attr for attr in dir(self._async_client) if not attr.startswith('_')]
#         endpoint_attrs = ['datasets', 'users', 'mass_stats', 'groups', 'space', 'model', 'auth']
#         all_attrs = default_attrs + async_client_attrs + endpoint_attrs
#         return list(set(all_attrs))
    
#     # Your existing methods (geoquery, zonal_stats, etc.)
#     def geoquery(
#         self,
#         expr: str,
#         feature: Union[Dict[str, Any], ShapelyGeometry],
#         in_crs: str = "epsg:4326",
#         out_crs: str = "epsg:4326",
#         resolution: int = -1,
#         geom_fix: bool = False,
#         **kwargs
#     ):
#         """Compute WCS query for a single geometry (synchronous version)."""
#         coro = self._async_client.geoquery(
#             expr=expr,
#             feature=feature,
#             in_crs=in_crs,
#             out_crs=out_crs,
#             output="netcdf",
#             resolution=resolution,
#             geom_fix=geom_fix,
#             **kwargs
#         )
#         return self._run_async(coro)

#     def zonal_stats(
#         self,
#         gdf: GeoDataFrame,
#         expr: str,
#         conc: int = 20,
#         inplace: bool = False,
#         in_crs: str = "epsg:4326",
#         out_crs: str = "epsg:4326",
#         resolution: int = -1,
#         geom_fix: bool = False,
#         drop_nan: bool = False,
#         spatial_reduction: str = None,
#         temporal_reduction: str = None,
#         max_memory_mb: int = 500,
#         stream_to_disk: bool = False,
#     ):
#         """Compute zonal statistics for all geometries in a GeoDataFrame (synchronous version)."""
#         coro = self._async_client.zonal_stats(
#             gdf=gdf,
#             expr=expr,
#             conc=conc,
#             inplace=inplace,
#             in_crs=in_crs,
#             out_crs=out_crs,
#             resolution=resolution,
#             geom_fix=geom_fix,
#             drop_nan=drop_nan,
#             spatial_reduction=spatial_reduction,
#             temporal_reduction=temporal_reduction,
#             max_memory_mb=max_memory_mb,
#             stream_to_disk=stream_to_disk
#         )
#         return self._run_async(coro)
    
#     def create_dataset_file(
#         self,
#         aoi: str,
#         expression: str,
#         output: str,
#         in_crs: str = "epsg:4326",
#         res: float = 0.0001,
#         region: str = "aus",
#         to_crs: str = "epsg:4326",
#         overwrite: bool = True,
#         skip_existing: bool = False,
#         non_interactive: bool = True,
#         poll_interval: int = 30,
#         download_path: str = "/home/user/Downloads",
#     ) -> dict:
#         """Create a dataset file using mass stats operations (synchronous version)."""
#         coro = self._async_client.create_dataset_file(
#             aoi=aoi,
#             expression=expression,
#             output=output,
#             in_crs=in_crs,
#             res=res,
#             region=region,
#             to_crs=to_crs,
#             overwrite=overwrite,
#             skip_existing=skip_existing,
#             non_interactive=non_interactive,
#             poll_interval=poll_interval,
#             download_path=download_path,
#         )
#         return self._run_async(coro)
    
#     # Context manager support
#     def __enter__(self):
#         """Context manager entry."""
#         return self
    
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         """Context manager exit."""
#         self.close()
    
#     def __del__(self):
#         """Destructor to ensure session is closed."""
#         if not self._closed:
#             try:
#                 self._cleanup()
#             except Exception:
#                 pass


# import asyncio
# import functools
# import concurrent.futures
# from typing import Optional, Dict, Any, Union
# from geopandas import GeoDataFrame
# from shapely.geometry.base import BaseGeometry as ShapelyGeometry
# from .async_client import AsyncClient


# class SyncWrapper:
#     """
#     Generic synchronous wrapper with __dir__ support for runtime autocomplete.
#     """
    
#     def __init__(self, async_obj, sync_client):
#         self._async_obj = async_obj
#         self._sync_client = sync_client
    
#     def __dir__(self):
#         """
#         Return list of attributes for autocomplete in interactive environments.
#         This enables autocomplete in Jupyter/iPython after instantiation.
#         """
#         async_attrs = [attr for attr in dir(self._async_obj) if not attr.startswith('_')]
        
#         wrapper_attrs = [attr for attr in object.__dir__(self) if not attr.startswith('_')]
        
#         return list(set(async_attrs + wrapper_attrs))
    
#     def __getattr__(self, name):
#         """
#         Dynamically wrap any method call to convert async to sync.
#         """
#         attr = getattr(self._async_obj, name)
        
#         if callable(attr):
#             @functools.wraps(attr)
#             def sync_wrapper(*args, **kwargs):
#                 result = attr(*args, **kwargs)
#                 if hasattr(result, '__await__'):
#                     return self._sync_client._run_async(result)
#                 return result
#             return sync_wrapper
        
#         return attr


# class SyncClient:
#     """
#     Synchronous wrapper with __dir__ support for runtime autocomplete.
#     Works best in interactive environments like Jupyter/iPython.
#     """
    
#     def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, verbose: bool = False):
#         self._async_client = AsyncClient(url=url, api_key=api_key, verbose=verbose)
#         self._context_entered = False
#         self._closed = False
        
#         self.datasets = SyncWrapper(self._async_client.datasets, self)
#         self.users = SyncWrapper(self._async_client.users, self)
#         self.mass_stats = SyncWrapper(self._async_client.mass_stats, self)
#         self.groups = SyncWrapper(self._async_client.groups, self)
#         self.space = SyncWrapper(self._async_client.space, self)
#         self.model = SyncWrapper(self._async_client.model, self)
#         self.auth = SyncWrapper(self._async_client.auth, self)
        
#         import atexit
#         atexit.register(self._cleanup)
    
#     def __dir__(self):
#         """
#         Return list of attributes for autocomplete in interactive environments.
#         This includes all methods from the async client plus the endpoint managers.
#         """
#         default_attrs = [attr for attr in object.__dir__(self) if not attr.startswith('_')]
        
#         async_client_attrs = [attr for attr in dir(self._async_client) if not attr.startswith('_')]
        
#         endpoint_attrs = ['datasets', 'users', 'mass_stats', 'groups', 'space', 'model', 'auth']
        
#         all_attrs = default_attrs + async_client_attrs + endpoint_attrs
        
#         return list(set(all_attrs))
    
#     def geoquery(
#         self,
#         expr: str,
#         feature: Union[Dict[str, Any], ShapelyGeometry],
#         in_crs: str = "epsg:4326",
#         out_crs: str = "epsg:4326",
#         resolution: int = -1,
#         geom_fix: bool = False,
#         **kwargs
#     ):
#         """Compute WCS query for a single geometry (synchronous version)."""
#         coro = self._async_client.geoquery(
#             expr=expr,
#             feature=feature,
#             in_crs=in_crs,
#             out_crs=out_crs,
#             output="netcdf",
#             resolution=resolution,
#             geom_fix=geom_fix,
#             **kwargs
#         )
#         return self._run_async(coro)

#     def zonal_stats(
#             self,
#             gdf: GeoDataFrame,
#             expr: str,
#             conc: int = 20,
#             in_crs: str = "epsg:4326",
#             out_crs: str = "epsg:4326",
#             resolution: int = -1,
#             geom_fix: bool = False,
#             mass_stats: bool = False,
#             id_column: Optional[str] = None,
#     ):
#         """
#         Compute zonal statistics for all geometries in a GeoDataFrame (synchronous version).
        
#         Args:
#             gdf (GeoDataFrame): GeoDataFrame containing geometries
#             expr (str): Terrakio expression to evaluate, can include spatial aggregations
#             conc (int): Number of concurrent requests to make
#             in_crs (str): Input coordinate reference system
#             out_crs (str): Output coordinate reference system
#             resolution (int): Resolution parameter
#             geom_fix (bool): Whether to fix the geometry (default False)
#             mass_stats (bool): Whether to use mass stats for processing (default False)
#             id_column (Optional[str]): Name of the ID column to use (default None)

#         Returns:
#             geopandas.GeoDataFrame: GeoDataFrame with added columns for results

#         Raises:
#             ValueError: If concurrency is too high or if data exceeds memory limit without streaming
#             APIError: If the API request fails
#         """
#         coro = self._async_client.zonal_stats(
#             gdf=gdf,
#             expr=expr,
#             conc=conc,
#             in_crs=in_crs,
#             out_crs=out_crs,
#             resolution=resolution,
#             geom_fix=geom_fix,
#             mass_stats=mass_stats,
#             id_column=id_column,
#         )
#         return self._run_async(coro)
    
#     def create_dataset_file(
#         self,
#         aoi: str,
#         expression: str,
#         output: str,
#         in_crs: str = "epsg:4326",
#         res: float = 0.0001,
#         region: str = "aus",
#         to_crs: str = "epsg:4326",
#         overwrite: bool = True,
#         skip_existing: bool = False,
#         non_interactive: bool = True,
#         poll_interval: int = 30,
#         download_path: str = "/home/user/Downloads",
#     ) -> dict:
#         """Create a dataset file using mass stats operations (synchronous version)."""
#         coro = self._async_client.create_dataset_file(
#             aoi=aoi,
#             expression=expression,
#             output=output,
#             in_crs=in_crs,
#             res=res,
#             region=region,
#             to_crs=to_crs,
#             overwrite=overwrite,
#             skip_existing=skip_existing,
#             non_interactive=non_interactive,
#             poll_interval=poll_interval,
#             download_path=download_path,
#         )
#         return self._run_async(coro)

#     def geo_queries(
#         self,
#         queries: list[dict],
#         conc: int = 20,
#     ):
#         """
#         Execute multiple geo queries concurrently (synchronous version).

#         Args:
#             queries (list[dict]): List of dictionaries containing query parameters.
#                                   Each query must have 'expr', 'feature', and 'in_crs' keys.
#             conc (int): Number of concurrent requests to make (default 20, max 100)

#         Returns:
#             Union[float, geopandas.GeoDataFrame]: 
#                 - float: Average of all results if results are integers
#                 - GeoDataFrame: GeoDataFrame with geometry and dataset columns if results are xarray datasets

#         Raises:
#             ValueError: If queries list is empty, concurrency is too high, or queries are malformed
#             APIError: If the API request fails

#         Example:
#             queries = [
#                 {
#                     'expr': 'WCF.wcf',
#                     'feature': {'type': 'Feature', 'geometry': {...}, 'properties': {}},
#                     'in_crs': 'epsg:4326'
#                 },
#                 {
#                     'expr': 'NDVI.ndvi',
#                     'feature': {'type': 'Feature', 'geometry': {...}, 'properties': {}},
#                     'in_crs': 'epsg:4326'
#                 }
#             ]
#             result = client.geo_queries(queries)
#         """
#         coro = self._async_client.geo_queries(
#             queries=queries,
#             conc=conc,
#         )
#         return self._run_async(coro)

#     async def _ensure_context(self):
#         """Ensure the async client context is entered."""
#         if not self._context_entered and not self._closed:
#             await self._async_client.__aenter__()
#             self._context_entered = True
    
#     async def _exit_context(self):
#         """Exit the async client context."""
#         if self._context_entered and not self._closed:
#             await self._async_client.__aexit__(None, None, None)
#             self._context_entered = False
    
#     def _run_async(self, coro):
#         """
#         Run an async coroutine and return the result synchronously.
#         This version handles both Jupyter notebook environments and regular Python environments.
#         """
#         async def run_with_context():
#             await self._ensure_context()
#             return await coro
        
#         try:
#             # Check if we're in a running event loop (like Jupyter)
#             loop = asyncio.get_running_loop()
            
#             # Method 1: Try using nest_asyncio if available
#             try:
#                 import nest_asyncio
#                 nest_asyncio.apply()
#                 return asyncio.run(run_with_context())
#             except ImportError:
#                 pass
            
#             # Method 2: Use ThreadPoolExecutor to run in a separate thread
#             def run_in_thread():
#                 return asyncio.run(run_with_context())
            
#             with concurrent.futures.ThreadPoolExecutor() as executor:
#                 future = executor.submit(run_in_thread)
#                 return future.result()
                
#         except RuntimeError:
#             # No running loop, safe to use asyncio.run()
#             return asyncio.run(run_with_context())
    
#     def close(self):
#         """Close the underlying async client session."""
#         if not self._closed:
#             async def close_async():
#                 await self._exit_context()
            
#             try:
#                 loop = asyncio.get_running_loop()
                
#                 # Try nest_asyncio first
#                 try:
#                     import nest_asyncio
#                     nest_asyncio.apply()
#                     asyncio.run(close_async())
#                 except ImportError:
#                     # Fall back to ThreadPoolExecutor
#                     def run_in_thread():
#                         return asyncio.run(close_async())
                    
#                     with concurrent.futures.ThreadPoolExecutor() as executor:
#                         future = executor.submit(run_in_thread)
#                         future.result()
                        
#             except RuntimeError:
#                 asyncio.run(close_async())
            
#             self._closed = True
    
#     def _cleanup(self):
#         """Internal cleanup method called by atexit."""
#         if not self._closed:
#             try:
#                 self.close()
#             except Exception:
#                 pass
    
#     def __enter__(self):
#         """Context manager entry."""
#         async def enter_async():
#             await self._ensure_context()
        
#         try:
#             loop = asyncio.get_running_loop()
            
#             # Try nest_asyncio first
#             try:
#                 import nest_asyncio
#                 nest_asyncio.apply()
#                 asyncio.run(enter_async())
#             except ImportError:
#                 # Fall back to ThreadPoolExecutor
#                 def run_in_thread():
#                     return asyncio.run(enter_async())
                
#                 with concurrent.futures.ThreadPoolExecutor() as executor:
#                     future = executor.submit(run_in_thread)
#                     future.result()
                    
#         except RuntimeError:
#             asyncio.run(enter_async())
        
#         return self
    
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         """Context manager exit."""
#         self.close()
    
#     def __del__(self):
#         """Destructor to ensure session is closed."""
#         if not self._closed:
#             try:
#                 self._cleanup()
#             except Exception:
#                 pass


# import asyncio
# import functools
# import concurrent.futures
# from typing import Optional, Dict, Any, Union, TYPE_CHECKING
# from geopandas import GeoDataFrame
# from shapely.geometry.base import BaseGeometry as ShapelyGeometry
# from .async_client import AsyncClient

# # Add type checking imports for better IDE support
# if TYPE_CHECKING:
#     from .endpoints.dataset_management import DatasetManagement
#     from .endpoints.user_management import UserManagement
#     from .endpoints.mass_stats import MassStats
#     from .endpoints.group_management import GroupManagement
#     from .endpoints.space_management import SpaceManagement
#     from .endpoints.model_management import ModelManagement
#     from .endpoints.auth import AuthClient


# class SyncWrapper:
#     """
#     Generic synchronous wrapper with __dir__ support for runtime autocomplete.
#     """
    
#     def __init__(self, async_obj, sync_client):
#         self._async_obj = async_obj
#         self._sync_client = sync_client
    
#     def __dir__(self):
#         """
#         Return list of attributes for autocomplete in interactive environments.
#         This enables autocomplete in Jupyter/iPython after instantiation.
#         """
#         async_attrs = [attr for attr in dir(self._async_obj) if not attr.startswith('_')]
#         wrapper_attrs = [attr for attr in object.__dir__(self) if not attr.startswith('_')]
#         return list(set(async_attrs + wrapper_attrs))
    
#     def __getattr__(self, name):
#         """
#         Dynamically wrap any method call to convert async to sync.
#         """
#         attr = getattr(self._async_obj, name)
        
#         if callable(attr):
#             @functools.wraps(attr)
#             def sync_wrapper(*args, **kwargs):
#                 result = attr(*args, **kwargs)
#                 if hasattr(result, '__await__'):
#                     return self._sync_client._run_async(result)
#                 return result
#             return sync_wrapper
        
#         return attr


# class SyncClient:
#     """
#     Synchronous wrapper with __dir__ support for runtime autocomplete.
#     Works best in interactive environments like Jupyter/iPython.
#     """
    
#     # Add explicit type annotations for endpoint managers
#     datasets: 'DatasetManagement'
#     users: 'UserManagement' 
#     mass_stats: 'MassStats'
#     groups: 'GroupManagement'
#     space: 'SpaceManagement'
#     model: 'ModelManagement'
#     auth: 'AuthClient'
    
#     def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, verbose: bool = False):
#         self._async_client = AsyncClient(url=url, api_key=api_key, verbose=verbose)
#         self._context_entered = False
#         self._closed = False
        
#         # Initialize endpoint managers with proper typing
#         self.datasets = SyncWrapper(self._async_client.datasets, self)
#         self.users = SyncWrapper(self._async_client.users, self)
#         self.mass_stats = SyncWrapper(self._async_client.mass_stats, self)
#         self.groups = SyncWrapper(self._async_client.groups, self)
#         self.space = SyncWrapper(self._async_client.space, self)
#         self.model = SyncWrapper(self._async_client.model, self)
#         self.auth = SyncWrapper(self._async_client.auth, self)
        
#         import atexit
#         atexit.register(self._cleanup)
    
#     def __dir__(self):
#         """
#         Return list of attributes for autocomplete in interactive environments.
#         This includes all methods from the async client plus the endpoint managers.
#         """
#         default_attrs = [attr for attr in object.__dir__(self) if not attr.startswith('_')]
#         async_client_attrs = [attr for attr in dir(self._async_client) if not attr.startswith('_')]
#         endpoint_attrs = ['datasets', 'users', 'mass_stats', 'groups', 'space', 'model', 'auth']
#         all_attrs = default_attrs + async_client_attrs + endpoint_attrs
#         return list(set(all_attrs))
    
#     def geoquery(
#         self,
#         expr: str,
#         feature: Union[Dict[str, Any], ShapelyGeometry],
#         in_crs: str = "epsg:4326",
#         out_crs: str = "epsg:4326",
#         resolution: int = -1,
#         geom_fix: bool = False,
#         **kwargs
#     ):
#         """Compute WCS query for a single geometry (synchronous version)."""
#         coro = self._async_client.geoquery(
#             expr=expr,
#             feature=feature,
#             in_crs=in_crs,
#             out_crs=out_crs,
#             output="netcdf",
#             resolution=resolution,
#             geom_fix=geom_fix,
#             **kwargs
#         )
#         return self._run_async(coro)

#     def zonal_stats(
#             self,
#             gdf: GeoDataFrame,
#             expr: str,
#             conc: int = 20,
#             in_crs: str = "epsg:4326",
#             out_crs: str = "epsg:4326",
#             resolution: int = -1,
#             geom_fix: bool = False,
#             mass_stats: bool = False,
#             id_column: Optional[str] = None,
#     ) -> GeoDataFrame:
#         """
#         Compute zonal statistics for all geometries in a GeoDataFrame (synchronous version).
        
#         Args:
#             gdf (GeoDataFrame): GeoDataFrame containing geometries
#             expr (str): Terrakio expression to evaluate, can include spatial aggregations
#             conc (int): Number of concurrent requests to make
#             in_crs (str): Input coordinate reference system
#             out_crs (str): Output coordinate reference system
#             resolution (int): Resolution parameter
#             geom_fix (bool): Whether to fix the geometry (default False)
#             mass_stats (bool): Whether to use mass stats for processing (default False)
#             id_column (Optional[str]): Name of the ID column to use (default None)

#         Returns:
#             geopandas.GeoDataFrame: GeoDataFrame with added columns for results

#         Raises:
#             ValueError: If concurrency is too high or if data exceeds memory limit without streaming
#             APIError: If the API request fails
#         """
#         coro = self._async_client.zonal_stats(
#             gdf=gdf,
#             expr=expr,
#             conc=conc,
#             in_crs=in_crs,
#             out_crs=out_crs,
#             resolution=resolution,
#             geom_fix=geom_fix,
#             mass_stats=mass_stats,
#             id_column=id_column,
#         )
#         return self._run_async(coro)
    
#     def create_dataset_file(
#         self,
#         aoi: str,
#         expression: str,
#         output: str,
#         in_crs: str = "epsg:4326",
#         res: float = 0.0001,
#         region: str = "aus",
#         to_crs: str = "epsg:4326",
#         overwrite: bool = True,
#         skip_existing: bool = False,
#         non_interactive: bool = True,
#         poll_interval: int = 30,
#         download_path: str = "/home/user/Downloads",
#     ) -> dict:
#         """Create a dataset file using mass stats operations (synchronous version)."""
#         coro = self._async_client.create_dataset_file(
#             aoi=aoi,
#             expression=expression,
#             output=output,
#             in_crs=in_crs,
#             res=res,
#             region=region,
#             to_crs=to_crs,
#             overwrite=overwrite,
#             skip_existing=skip_existing,
#             non_interactive=non_interactive,
#             poll_interval=poll_interval,
#             download_path=download_path,
#         )
#         return self._run_async(coro)

#     def geo_queries(
#         self,
#         queries: list[dict],
#         conc: int = 20,
#     ) -> Union[float, GeoDataFrame]:
#         """
#         Execute multiple geo queries concurrently (synchronous version).

#         Args:
#             queries (list[dict]): List of dictionaries containing query parameters.
#                                   Each query must have 'expr', 'feature', and 'in_crs' keys.
#             conc (int): Number of concurrent requests to make (default 20, max 100)

#         Returns:
#             Union[float, geopandas.GeoDataFrame]: 
#                 - float: Average of all results if results are integers
#                 - GeoDataFrame: GeoDataFrame with geometry and dataset columns if results are xarray datasets

#         Raises:
#             ValueError: If queries list is empty, concurrency is too high, or queries are malformed
#             APIError: If the API request fails

#         Example:
#             queries = [
#                 {
#                     'expr': 'WCF.wcf',
#                     'feature': {'type': 'Feature', 'geometry': {...}, 'properties': {}},
#                     'in_crs': 'epsg:4326'
#                 },
#                 {
#                     'expr': 'NDVI.ndvi',
#                     'feature': {'type': 'Feature', 'geometry': {...}, 'properties': {}},
#                     'in_crs': 'epsg:4326'
#                 }
#             ]
#             result = client.geo_queries(queries)
#         """
#         coro = self._async_client.geo_queries(
#             queries=queries,
#             conc=conc,
#         )
#         return self._run_async(coro)

#     async def _ensure_context(self) -> None:
#         """Ensure the async client context is entered."""
#         if not self._context_entered and not self._closed:
#             await self._async_client.__aenter__()
#             self._context_entered = True
    
#     async def _exit_context(self) -> None:
#         """Exit the async client context."""
#         if self._context_entered and not self._closed:
#             await self._async_client.__aexit__(None, None, None)
#             self._context_entered = False
    
#     def _run_async(self, coro):
#         """
#         Run an async coroutine and return the result synchronously.
#         This version handles both Jupyter notebook environments and regular Python environments.
#         """
#         async def run_with_context():
#             await self._ensure_context()
#             return await coro
        
#         try:
#             # Check if we're in a running event loop (like Jupyter)
#             loop = asyncio.get_running_loop()
            
#             # Method 1: Try using nest_asyncio if available
#             try:
#                 import nest_asyncio
#                 nest_asyncio.apply()
#                 return asyncio.run(run_with_context())
#             except ImportError:
#                 pass
            
#             # Method 2: Use ThreadPoolExecutor to run in a separate thread
#             def run_in_thread():
#                 return asyncio.run(run_with_context())
            
#             with concurrent.futures.ThreadPoolExecutor() as executor:
#                 future = executor.submit(run_in_thread)
#                 return future.result()
                
#         except RuntimeError:
#             # No running loop, safe to use asyncio.run()
#             return asyncio.run(run_with_context())
    
#     def close(self) -> None:
#         """Close the underlying async client session."""
#         if not self._closed:
#             async def close_async():
#                 await self._exit_context()
            
#             try:
#                 loop = asyncio.get_running_loop()
                
#                 # Try nest_asyncio first
#                 try:
#                     import nest_asyncio
#                     nest_asyncio.apply()
#                     asyncio.run(close_async())
#                 except ImportError:
#                     # Fall back to ThreadPoolExecutor
#                     def run_in_thread():
#                         return asyncio.run(close_async())
                    
#                     with concurrent.futures.ThreadPoolExecutor() as executor:
#                         future = executor.submit(run_in_thread)
#                         future.result()
                        
#             except RuntimeError:
#                 asyncio.run(close_async())
            
#             self._closed = True
    
#     def _cleanup(self) -> None:
#         """Internal cleanup method called by atexit."""
#         if not self._closed:
#             try:
#                 self.close()
#             except Exception:
#                 pass
    
#     def __enter__(self) -> 'SyncClient':
#         """Context manager entry."""
#         async def enter_async():
#             await self._ensure_context()
        
#         try:
#             loop = asyncio.get_running_loop()
            
#             # Try nest_asyncio first
#             try:
#                 import nest_asyncio
#                 nest_asyncio.apply()
#                 asyncio.run(enter_async())
#             except ImportError:
#                 # Fall back to ThreadPoolExecutor
#                 def run_in_thread():
#                     return asyncio.run(enter_async())
                
#                 with concurrent.futures.ThreadPoolExecutor() as executor:
#                     future = executor.submit(run_in_thread)
#                     future.result()
                    
#         except RuntimeError:
#             asyncio.run(enter_async())
        
#         return self
    
#     def __exit__(self, exc_type, exc_val, exc_tb) -> None:
#         """Context manager exit."""
#         self.close()
    
#     def __del__(self) -> None:
#         """Destructor to ensure session is closed."""
#         if not self._closed:
#             try:
#                 self._cleanup()
#             except Exception:
#                 pass

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
        
        # Register cleanup
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
        
        # Wait for the result (with timeout to avoid hanging)
        try:
            return future.result(timeout=300)  # 5 minute timeout
        except concurrent.futures.TimeoutError:
            raise RuntimeError("Async operation timed out after 5 minutes")
    
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

    def zonal_stats(
        self,
        gdf: GeoDataFrame,
        expr: str,
        conc: int = 20,
        in_crs: str = "epsg:4326",
        out_crs: str = "epsg:4326",
        resolution: int = -1,
        geom_fix: bool = False,
        mass_stats: bool = False,
        id_column: Optional[str] = None,
    ) -> GeoDataFrame:
        """
        Compute zonal statistics for all geometries in a GeoDataFrame (synchronous version).
        
        Args:
            gdf (GeoDataFrame): GeoDataFrame containing geometries
            expr (str): Terrakio expression to evaluate, can include spatial aggregations
            conc (int): Number of concurrent requests to make
            in_crs (str): Input coordinate reference system
            out_crs (str): Output coordinate reference system
            resolution (int): Resolution parameter
            geom_fix (bool): Whether to fix the geometry (default False)
            mass_stats (bool): Whether to use mass stats for processing (default False)
            id_column (Optional[str]): Name of the ID column to use (default None)

        Returns:
            geopandas.GeoDataFrame: GeoDataFrame with added columns for results

        Raises:
            ValueError: If concurrency is too high or if data exceeds memory limit without streaming
            APIError: If the API request fails
        """
        coro = self._async_client.zonal_stats(
            gdf=gdf,
            expr=expr,
            conc=conc,
            in_crs=in_crs,
            out_crs=out_crs,
            resolution=resolution,
            geom_fix=geom_fix,
            mass_stats=mass_stats,
            id_column=id_column,
        )
        return self._run_async(coro)
    
    def create_dataset_file(
        self,
        aoi: str,
        expression: str,
        output: str,
        in_crs: str = "epsg:4326",
        res: float = 0.0001,
        region: str = "aus",
        to_crs: str = "epsg:4326",
        overwrite: bool = True,
        skip_existing: bool = False,
        non_interactive: bool = True,
        poll_interval: int = 30,
        download_path: str = "/home/user/Downloads",
    ) -> dict:
        """Create a dataset file using mass stats operations (synchronous version)."""
        coro = self._async_client.create_dataset_file(
            aoi=aoi,
            expression=expression,
            output=output,
            in_crs=in_crs,
            res=res,
            region=region,
            to_crs=to_crs,
            overwrite=overwrite,
            skip_existing=skip_existing,
            non_interactive=non_interactive,
            poll_interval=poll_interval,
            download_path=download_path,
        )
        return self._run_async(coro)

    def geo_queries(
        self,
        queries: list[dict],
        conc: int = 20,
    ) -> Union[float, GeoDataFrame]:
        """
        Execute multiple geo queries concurrently (synchronous version).

        Args:
            queries (list[dict]): List of dictionaries containing query parameters.
                                  Each query must have 'expr', 'feature', and 'in_crs' keys.
            conc (int): Number of concurrent requests to make (default 20, max 100)

        Returns:
            Union[float, geopandas.GeoDataFrame]: 
                - float: Average of all results if results are integers
                - GeoDataFrame: GeoDataFrame with geometry and dataset columns if results are xarray datasets

        Raises:
            ValueError: If queries list is empty, concurrency is too high, or queries are malformed
            APIError: If the API request fails

        Example:
            queries = [
                {
                    'expr': 'WCF.wcf',
                    'feature': {'type': 'Feature', 'geometry': {...}, 'properties': {}},
                    'in_crs': 'epsg:4326'
                },
                {
                    'expr': 'NDVI.ndvi',
                    'feature': {'type': 'Feature', 'geometry': {...}, 'properties': {}},
                    'in_crs': 'epsg:4326'
                }
            ]
            result = client.geo_queries(queries)
        """
        coro = self._async_client.geo_queries(
            queries=queries,
            conc=conc,
        )
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