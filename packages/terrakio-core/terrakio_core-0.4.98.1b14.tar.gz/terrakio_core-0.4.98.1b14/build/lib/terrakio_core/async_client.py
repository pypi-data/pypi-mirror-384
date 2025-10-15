import aiohttp
import asyncio
import json
import pandas as pd
import xarray as xr
from io import BytesIO
from typing import Optional, Dict, Any, Union
from geopandas import GeoDataFrame
from shapely.geometry.base import BaseGeometry as ShapelyGeometry
from shapely.geometry import mapping
from .client import BaseClient
from .exceptions import APIError
from .endpoints.dataset_management import DatasetManagement
from .endpoints.user_management import UserManagement
from .endpoints.mass_stats import MassStats
from .endpoints.group_management import GroupManagement
from .endpoints.space_management import SpaceManagement
from .endpoints.model_management import ModelManagement
from .endpoints.auth import AuthClient
from .convenience_functions.convenience_functions import zonal_stats as _zonal_stats, create_dataset_file as _create_dataset_file, request_geoquery_list as _request_geoquery_list

class AsyncClient(BaseClient):
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, verbose: bool = False, session: Optional[aiohttp.ClientSession] = None):
        super().__init__(url, api_key, verbose)
        self.datasets = DatasetManagement(self)
        self.users = UserManagement(self)
        self.mass_stats = MassStats(self)
        self.groups = GroupManagement(self)
        self.space = SpaceManagement(self)
        self.model = ModelManagement(self)
        self.auth = AuthClient(self)
        self._session = session
        self._owns_session = session is None

    async def _terrakio_request(self, method: str, endpoint: str, **kwargs):
        if self.session is None:
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.key,
                'Authorization': self.token
            }
            clean_headers = {k: v for k, v in headers.items() if v is not None}
            async with aiohttp.ClientSession(headers=clean_headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                return await self._make_request_with_retry(session, method, endpoint, **kwargs)
        else:
            return await self._make_request_with_retry(self._session, method, endpoint, **kwargs)

    async def _make_request_with_retry(self, session: aiohttp.ClientSession, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        url = f"{self.url}/{endpoint.lstrip('/')}"    
        last_exception = None
        for attempt in range(self.retry + 1):
            try:
                async with session.request(method, url, **kwargs) as response:
                    if not response.ok and self._should_retry(response.status, attempt):
                        self.logger.info(f"Request failed (attempt {attempt+1}/{self.retry+1}): {response.status}. Retrying...")
                        continue
                    if not response.ok:
                        error_msg = f"API request failed: {response.status} {response.reason}"
                        try:
                            error_data = await response.json()
                            if "detail" in error_data:
                                error_msg += f" - {error_data['detail']}"
                        except:
                            pass
                        raise APIError(error_msg, status_code=response.status)
                    return await self._parse_response(response)
                    
            except aiohttp.ClientError as e:
                last_exception = e
                if attempt < self.retry:
                    self.logger.info(f"Networking error (attempt {attempt+1}/{self.retry+1}): {e}. Retrying...")
                    continue
                else:
                    break
        
        raise APIError(f"Networking error, request failed after {self.retry+1} attempts: {last_exception}", status_code=None)
    
    def _should_retry(self, status_code: int, attempt: int) -> bool:
        """Determine if the request should be retried based on status code."""
        if attempt >= self.retry:
            return False
        elif status_code in [408, 502, 503, 504]:
            return True
        else:
            return False

    async def _parse_response(self, response) -> Any:
        """Parse response based on content type."""
        content_type = response.headers.get('content-type', '').lower()
        content = await response.read()
        if 'json' in content_type:
            return json.loads(content.decode('utf-8'))
        elif 'csv' in content_type:
            return pd.read_csv(BytesIO(content))
        elif 'image/' in content_type:
            return content
        elif 'text' in content_type:
            return content.decode('utf-8')
        else:
            try:
                return xr.open_dataset(BytesIO(content))
            except:
                raise APIError(f"Unknown response format: {content_type}", status_code=response.status)

    async def _regular_request(self, method: str, endpoint: str, **kwargs):
        url = endpoint.lstrip('/')
        
        if self._session is None:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.request(method, url, **kwargs) as response:
                        response.raise_for_status()
                        
                        content = await response.read()
                        
                        return type('Response', (), {
                            'status': response.status,
                            'content': content,
                            'text': lambda: content.decode('utf-8'),
                            'json': lambda: json.loads(content.decode('utf-8'))
                        })()
                except aiohttp.ClientError as e:
                    raise APIError(f"Request failed: {e}")
        else:
            try:
                async with self._session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    content = await response.read()
                    
                    return type('Response', (), {
                        'status': response.status,
                        'content': content,
                        'text': lambda: content.decode('utf-8'),
                        'json': lambda: json.loads(content.decode('utf-8'))
                    })()
            except aiohttp.ClientError as e:
                raise APIError(f"Request failed: {e}")
        
    async def geoquery(
        self,
        expr: str,
        feature: Union[Dict[str, Any], ShapelyGeometry],
        in_crs: str = "epsg:4326",
        out_crs: str = "epsg:4326",
        resolution: int = -1,
        geom_fix: bool = False,
        validated: bool = True,
        **kwargs
    ):
        """
        Compute WCS query for a single geometry.

        Args:
            expr (str): The WCS expression to evaluate
            feature (Union[Dict[str, Any], ShapelyGeometry]): The geographic feature
            in_crs (str): Input coordinate reference system
            out_crs (str): Output coordinate reference system
            resolution (int): Resolution parameter
            geom_fix (bool): Whether to fix the geometry (default False)
            validated (bool): Whether to use validated data (default True)
            **kwargs: Additional parameters to pass to the WCS request
            
        Returns:
            Union[pd.DataFrame, xr.Dataset, bytes]: The response data in the requested format

        Raises:
            APIError: If the API request fails
        """
        if hasattr(feature, 'is_valid'):
            feature = {
                "type": "Feature",
                "geometry": mapping(feature),
                "properties": {}
            }
        payload = {
            "feature": feature,
            "in_crs": in_crs,
            "out_crs": out_crs,
            "output": "netcdf",
            "resolution": resolution,
            "expr": expr,
            "buffer": geom_fix,
            "validated": validated,
            **kwargs
        }
        result = await self._terrakio_request("POST", "geoquery", json=payload)

        return result

    async def zonal_stats(
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
    ):
        """
        Compute zonal statistics for all geometries in a GeoDataFrame.

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
        return await _zonal_stats(
            client=self,
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

    async def create_dataset_file(
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
        """
        Create a dataset file using mass stats operations.

        Args:
            aoi (str): Area of interest
            expression (str): Terrakio expression to evaluate
            output (str): Output format
            in_crs (str): Input coordinate reference system (default "epsg:4326")
            res (float): Resolution (default 0.0001)
            region (str): Region (default "aus")
            to_crs (str): Target coordinate reference system (default "epsg:4326")
            overwrite (bool): Whether to overwrite existing files (default True)
            skip_existing (bool): Whether to skip existing files (default False)
            non_interactive (bool): Whether to run non-interactively (default True)
            poll_interval (int): Polling interval in seconds (default 30)
            download_path (str): Download path (default "/home/user/Downloads")

        Returns:
            dict: Dictionary containing generation_task_id and combine_task_id

        Raises:
            ConfigurationError: If mass stats client is not properly configured
            RuntimeError: If job fails
        """
        return await _create_dataset_file(
            client=self,
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

    async def geo_queries(
        self,
        queries: list[dict],
        conc: int = 20,
    ):
        """
        Execute multiple geo queries concurrently.

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
            result = await client.geo_queries(queries)
        """
        return await _request_geoquery_list(
            client=self,
            quries=queries,  # Note: keeping original parameter name for compatibility
            conc=conc,
        )

    async def __aenter__(self):
        if self._session is None:
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.key,
                'Authorization': self.token
            }
            clean_headers = {k: v for k, v in headers.items() if v is not None}
            self._session = aiohttp.ClientSession(
                headers=clean_headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._owns_session and self._session:
            await self._session.close()
            self._session = None

    async def close(self):
        if self._owns_session and self._session:
            await self._session.close()
            self._session = None