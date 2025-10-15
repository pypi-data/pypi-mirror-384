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
from .exceptions import APIError, NetworkError
from .endpoints.dataset_management import DatasetManagement
from .endpoints.user_management import UserManagement
from .endpoints.mass_stats import MassStats
from .endpoints.group_management import GroupManagement
from .endpoints.space_management import SpaceManagement
from .endpoints.model_management import ModelManagement
from .endpoints.auth import AuthClient
from .convenience_functions.zonal_stats import zonal_stats as _zonal_stats
from .convenience_functions.geoquries import request_geoquery_list as _request_geoquery_list
from .convenience_functions.create_dataset_file import create_dataset_file as _create_dataset_file

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
                'x-api-key': self.key, 
                'Authorization': self.token
            }
            if 'json' in kwargs:
                headers['Content-Type'] = 'application/json'
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
                    content = await response.text()
                    
                    if not response.ok and self._should_retry(response.status, attempt):
                        self.logger.info(f"Request failed (attempt {attempt+1}/{self.retry+1}): {response.status}. Retrying...")
                        continue
                    if response.ok:
                        data = await self._parse_response(response)
                        return data, response.status
                    else:
                        error_data = await response.json()
                        return error_data, response.status
            except aiohttp.ClientError as e:
                last_exception = e
                if attempt < self.retry:
                    self.logger.info(f"Networking error (attempt {attempt+1}/{self.retry+1}): {e}. Retrying...")
                    continue
                else:
                    break

        raise NetworkError(f"Network failure after {self.retry+1} attempts: {last_exception}")
    
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

    async def zonal_stats(self, *args, **kwargs):
        """Proxy to convenience zonal_stats with full argument passthrough."""
        return await _zonal_stats(self, *args, **kwargs)

    async def create_dataset_file(self, *args, **kwargs) -> dict:
        """Proxy to convenience create_dataset_file with full argument passthrough."""
        kwargs.setdefault('download_path', "/home/user/Downloads")
        kwargs.setdefault('region', "aus")
        return await _create_dataset_file(self, *args, **kwargs)

    async def geo_queries(self, *args, **kwargs):
        """Proxy to convenience request_geoquery_list with full argument passthrough."""
        if 'queries' in kwargs:
            kwargs['quries'] = kwargs.pop('queries')
        return await _request_geoquery_list(self, *args, **kwargs)

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