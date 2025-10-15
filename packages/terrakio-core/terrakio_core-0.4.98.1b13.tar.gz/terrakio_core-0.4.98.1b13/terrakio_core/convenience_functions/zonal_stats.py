# Standard library imports
import asyncio
import psutil
import random
import uuid
from io import BytesIO
from typing import Optional

# Third-party library imports
import aiohttp
import geopandas as gpd
import pandas as pd
import pyproj
import xarray as xr
from geopandas import GeoDataFrame
from shapely.geometry import box, mapping, shape
from shapely.ops import transform
import threading
from concurrent.futures import ThreadPoolExecutor

# Local imports
from .geoquries import request_geoquery_list

class cloud_object(gpd.GeoDataFrame):
    """
    This class is a class used for cloud
    """
    def __init__(self, job_id: str, job_name: str, client=None):

        super().__init__({
            'geometry': [], 
            'dataset': []
        })

        self.job_id = job_id
        self.client = client
        self.job_name = job_name

    def __repr__(self):
        return (
            f"<CloudZonalStats job_id='{self.job_id}', job_name='{self.job_name}'>\n"
            f"Call .head(n) to fetch a preview GeoDataFrame when the job completes."
        )

    def _repr_html_(self):
        # Jupyter HTML-friendly representation to avoid auto-rendering an empty DataFrame
        return (
            f"<div style='font-family:system-ui,Segoe UI,Helvetica,Arial,sans-serif'>"
            f"<strong>Cloud Zonal Stats</strong><br/>"
            f"job_id: <code>{self.job_id}</code><br/>"
            f"job_name: <code>{self.job_name}</code><br/>"
            f"<em>Use <code>.head(n)</code> to retrieve a preview once the job is completed.</em>"
            f"</div>"
        )

    def head(self, n = 5):
        """
        Returns the first n files stored in the cloud bucket.
        """
        # Detect if we're inside an existing event loop (e.g., Jupyter)
        in_running_loop = False
        try:
            asyncio.get_running_loop()
            in_running_loop = True
        except RuntimeError:
            in_running_loop = False

        if in_running_loop:
            # Run the async function in a separate thread with its own loop
            def run_async_in_thread():
                new_loop = asyncio.new_event_loop()
                try:
                    return new_loop.run_until_complete(self._head_async(n))
                finally:
                    new_loop.close()
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_async_in_thread)
                return future.result()
        else:
            # No running loop - safe to use asyncio.run
            return asyncio.run(self._head_async(n))
        
    async def _head_async(self, n = 5):
        """
        Returns the first n files stored in the cloud bucket.

        Args:
            n (int): Number of files to return. Default is 5.

        Returns:
            GeoDataFrame: A GeoDataFrame containing the first n files.
        """

        track_info = await self.client.mass_stats.track_job([self.job_id])
        job_info = track_info[self.job_id]
        status = job_info['status']
        
        if status == "Completed":
            payload = {
                "job_name": job_info["name"],
                "file_type": "raw",
                "bucket": job_info["bucket"],
            }
            result = await self.client._terrakio_request("POST", "mass_stats/download_files", json=payload)
            download_urls = result["download_urls"][:n]
            datasets = []

            async with aiohttp.ClientSession() as session:
                for i, url in enumerate(download_urls):
                    try:
                        self.client.logger.info(f"Downloading dataset {i+1}/{len(download_urls)}...")
                        async with session.get(url) as response:
                            if response.status == 200:
                                content = await response.read()
                                dataset = xr.open_dataset(BytesIO(content))
                                datasets.append(dataset)
                                self.client.logger.info(f"Successfully processed dataset {i+1}")
                            else:
                                self.client.logger.warning(f"Failed to download dataset {i+1}: HTTP {response.status}")
                    except Exception as e:
                        self.client.logger.error(f"Error downloading dataset {i+1}: {e}")
                        continue
                if not datasets:
                    self.client.logger.warning("No datasets were successfully downloaded")
                    return gpd.GeoDataFrame({'geometry': [], 'dataset': []})
                try:
                    json_response = await self.client._terrakio_request(
                        "POST", "mass_stats/download_json", 
                        params={"job_name": job_info['name']}
                    )
                    json_url = json_response["download_url"]
                    
                    async with session.get(json_url) as response:
                        if response.status == 200:
                            json_data = await response.json()
                            self.client.logger.info("Successfully downloaded geometry data")
                            
                            geometries = []
                            max_geometries = min(n, len(json_data), len(datasets))
                            
                            for i in range(max_geometries):
                                try:
                                    geom_dict = json_data[i]["request"]["feature"]["geometry"]
                                    shapely_geom = shape(geom_dict)
                                    geometries.append(shapely_geom)
                                except (KeyError, ValueError) as e:
                                    self.client.logger.warning(f"Error parsing geometry {i}: {e}")
                                    continue
                            
                            min_length = min(len(datasets), len(geometries))
                            if min_length == 0:
                                self.client.logger.warning("No matching datasets and geometries found")
                                return gpd.GeoDataFrame({'geometry': [], 'dataset': []})
                            
                            gdf = gpd.GeoDataFrame({
                                'geometry': geometries[:min_length],
                                'dataset': datasets[:min_length]
                            })
                            
                            self.client.logger.info(f"Created GeoDataFrame with {len(gdf)} rows")

                            # Derive id values from json metadata (prefer 'file', fallback to 'group')
                            id_values = []
                            for i in range(min_length):
                                entry = json_data[i] if i < len(json_data) else {}
                                id_candidate = entry.get('file') or entry.get('group') or ''
                                if isinstance(id_candidate, str) and id_candidate.startswith('file_'):
                                    id_val = id_candidate[len('file_'):]
                                elif isinstance(id_candidate, str) and id_candidate.startswith('group_'):
                                    id_val = id_candidate[len('group_'):]
                                else:
                                    id_val = str(id_candidate) if id_candidate else str(i)
                                id_values.append(id_val)

                            # Geometry to id mapping using WKB to avoid precision issues
                            geom_to_id = {geometries[i].wkb: id_values[i] for i in range(min_length)}

                            try:
                                expanded_gdf = expand_on_variables_and_time(gdf)

                                # Attach id as first index level, geometry second, time third if present
                                if hasattr(expanded_gdf.index, 'names') and 'geometry' in expanded_gdf.index.names:
                                    if isinstance(expanded_gdf.index, pd.MultiIndex):
                                        geometry_index = expanded_gdf.index.get_level_values('geometry')
                                    else:
                                        geometry_index = expanded_gdf.index
                                    id_col = [geom_to_id.get(geom.wkb) for geom in geometry_index]
                                    expanded_gdf['id'] = id_col
                                    expanded_gdf = expanded_gdf.reset_index()
                                    if 'time' in expanded_gdf.columns:
                                        expanded_gdf = expanded_gdf.set_index(['id', 'geometry', 'time'])
                                    else:
                                        expanded_gdf = expanded_gdf.set_index(['id', 'geometry'])
                                else:
                                    # geometry exists as a column
                                    id_col = [geom_to_id.get(geom.wkb) for geom in expanded_gdf['geometry']]
                                    expanded_gdf['id'] = id_col
                                    if 'time' in expanded_gdf.columns:
                                        expanded_gdf = expanded_gdf.set_index(['id', 'geometry', 'time'])
                                    else:
                                        expanded_gdf = expanded_gdf.set_index(['id', 'geometry'])

                                return expanded_gdf
                            except NameError:
                                self.client.logger.warning("expand_on_variables_and_time function not found, returning raw GeoDataFrame")
                                # Set id on raw gdf and index appropriately
                                gdf['id'] = id_values
                                return gdf.set_index(['id', 'geometry'])
                                
                        else:
                            self.client.logger.warning(f"Failed to download geometry data: HTTP {response.status}")
                            return gpd.GeoDataFrame({'geometry': [], 'dataset': []})
                                    
                except Exception as e:
                        self.client.logger.error(f"Error downloading geometry data: {e}")
                        return gpd.GeoDataFrame({'geometry': [], 'dataset': []})
        
        elif status in ["Failed", "Cancelled", "Error"]:
            raise RuntimeError(f"The zonal stats job (job_id: {self.job_id}) has failed, cancelled, or errored. Please check the job status!")
        
        else:
            # Job is still running - include progress information
            completed = job_info.get('completed', 0)
            total = job_info.get('total', 1)
            progress = completed / total if total > 0 else 0
            percentage = progress * 100
            
            # Create progress bar
            bar_length = 30  # Shorter bar for error message
            filled_length = int(bar_length * progress)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            raise RuntimeError(
                f"The zonal stats job (job_id: {self.job_id}) is still running. "
                f"Progress: [{bar}] {percentage:.1f}% ({completed}/{total}). "
                f"Please come back at a later time!"
            )
    
def expand_on_time(gdf):
    """
    Expand datasets on time dimension - each time becomes a new row.
    
    Input: GeoDataFrame with 'geometry' and 'dataset' columns (or variable columns)
    Output: GeoDataFrame with time in multi-index and datasets without time coordinate
    """
    rows = []
    
    for idx, row in gdf.iterrows():
        if 'geometry' in gdf.columns:
            geometry = row['geometry']
        elif gdf.index.name == 'geometry':
            geometry = idx
        else:
            raise ValueError(f"Cannot find geometry in columns: {list(gdf.columns)} or index: {gdf.index.name}")
        
        if 'dataset' in gdf.columns:
            dataset = row['dataset']
            
            if 'time' in dataset.dims:
                for time_val in dataset.time.values:
                    time_slice = dataset.sel(time=time_val).drop_vars('time')
                    rows.append({
                        'geometry': geometry,
                        'time': time_val,
                        'dataset': time_slice
                    })
            else:
                rows.append({
                    'geometry': geometry,
                    'dataset': dataset
                })
        else:
            variable_columns = list(gdf.columns)
            
            first_dataset = row[variable_columns[0]]
            if 'time' in first_dataset.dims:
                time_values = first_dataset.time.values
                
                for time_val in time_values:
                    row_data = {'geometry': geometry, 'time': time_val}
                    
                    for var_col in variable_columns:
                        dataset = row[var_col]
                        time_slice = dataset.sel(time=time_val).drop_vars('time')
                        row_data[var_col] = time_slice
                    
                    rows.append(row_data)
            else:
                row_data = {'geometry': geometry}
                for var_col in variable_columns:
                    row_data[var_col] = row[var_col]
                rows.append(row_data)
    
    result_df = pd.DataFrame(rows)
    
    if 'time' in result_df.columns:
        result_gdf = gpd.GeoDataFrame(result_df, geometry='geometry')
        result_gdf = result_gdf.set_index(['geometry', 'time'])
    else:
        result_gdf = gpd.GeoDataFrame(result_df, geometry='geometry')
        result_gdf = result_gdf.set_index(['geometry'])
    
    result_gdf.attrs = gdf.attrs.copy()
    
    return result_gdf

def expand_on_variables(gdf):
    """
    Expand datasets on variables dimension - each variable becomes a new column.
    
    Input: GeoDataFrame with 'geometry' and 'dataset' columns (or already time-expanded)
    Output: GeoDataFrame with separate column for each variable
    """
    rows = []
    
    for idx, row in gdf.iterrows():
        if 'geometry' in gdf.columns:
            geometry = row['geometry']
        elif hasattr(gdf.index, 'names') and 'geometry' in gdf.index.names:
            if isinstance(idx, tuple):
                geometry_idx = gdf.index.names.index('geometry')
                geometry = idx[geometry_idx]
                time_idx = gdf.index.names.index('time')
                time_val = idx[time_idx]
            else:
                geometry = idx
                time_val = None
        else:
            raise ValueError(f"Cannot find geometry in columns: {list(gdf.columns)} or index: {gdf.index.names}")
        
        if 'dataset' in gdf.columns:
            dataset = row['dataset']
            
            var_names = list(dataset.data_vars.keys())
            
            if len(var_names) <= 1:
                if len(var_names) == 0:
                    continue
            
            if hasattr(gdf.index, 'names') and 'time' in gdf.index.names:
                row_data = {'geometry': geometry, 'time': time_val}
            else:
                row_data = {'geometry': geometry}
            
            for var_name in var_names:
                var_dataset = dataset[[var_name]]
                
                if len(var_dataset.dims) == 0:
                    row_data[var_name] = float(var_dataset[var_name].values)
                else:
                    row_data[var_name] = var_dataset
            
            rows.append(row_data)
        else:
            raise ValueError("Expected 'dataset' column for variable expansion")
    
    result_df = pd.DataFrame(rows)

    if 'time' in result_df.columns:
        result_gdf = gpd.GeoDataFrame(result_df, geometry='geometry')
        result_gdf = result_gdf.set_index(['geometry', 'time'])
    else:
        result_gdf = gpd.GeoDataFrame(result_df, geometry='geometry')
        result_gdf = result_gdf.set_index(['geometry'])
    
    result_gdf.attrs = gdf.attrs.copy()
    
    return result_gdf

def expand_on_variables_and_time(gdf):
    """
    Convenience function to expand on both variables and time.
    Automatically detects which expansions are possible.
    """
    try:
        expanded_on_time = expand_on_time(gdf)
    except Exception as e:
        expanded_on_time = gdf
    
    try:
        expanded_on_variables_and_time = expand_on_variables(expanded_on_time)
        return expanded_on_variables_and_time
    except Exception as e:
        return expanded_on_time
    
def estimate_geometry_size_ratio(queries: list):
    """Calculate size ratios for all geometries relative to the first geometry using bounding box area."""
    
    areas = []
    
    for query in queries:
        geom = shape(query["feature"]["geometry"])
        in_crs = query["in_crs"]
        
        if in_crs and in_crs != 'EPSG:3857':
            transformer = pyproj.Transformer.from_crs(in_crs, 'EPSG:3857', always_xy=True)
            transformed_geom = transform(transformer.transform, geom)
            bbox = box(*transformed_geom.bounds)
            area = bbox.area
        else:
            bbox = box(*geom.bounds)
            area = bbox.area
        
        areas.append(area)    
    base_area = areas[0]
    
    if base_area == 0:
        non_zero_areas = [area for area in areas if area > 0]
        base_area = non_zero_areas[0] if non_zero_areas else 1.0
    
    ratios = []
    for area in areas:
        if area == 0:
            ratios.append(0.1)
        else:
            ratios.append(area / base_area)
    
    return ratios

async def estimate_query_size(
    client,
    quries: list[dict],
):
    first_query = quries[0]

    first_query_dataset = await client.geoquery(**first_query)
    ratios = estimate_geometry_size_ratio(quries)
    total_size_mb = 0
    for i in range(len(ratios)):
        total_size_mb += first_query_dataset.nbytes * ratios[i] / (1024**2)
    return total_size_mb

async def estimate_timestamp_number(
        client,
        quries: list[dict],
):
    if len(quries) <= 3:
        return quries
    sampled_queries = [query.copy() for query in random.sample(quries, 3)]
    for query in sampled_queries:
        query['debug'] = 'grpc'
    result = await request_geoquery_list(client = client, quries = sampled_queries, conc = 5)
    total_estimated_number_of_timestamps = result * len(quries)
    return total_estimated_number_of_timestamps


def get_available_memory_mb():
    """
    Get available system memory in MB
    
    Returns:
        float: Available memory in MB
    """
    memory = psutil.virtual_memory()
    available_mb = memory.available / (1024 * 1024)
    return round(available_mb, 2)

async def local_or_remote(
        client,
        quries: list[dict],
):
    if len(quries) > 1000:
        return {
            "local_or_remote": "remote",
            "reason": "The number of the requests is too large(>1000), please set the mass_stats parameter to True",
        }
    elif await estimate_timestamp_number(client = client, quries = quries) > 25000:
        return {
            "local_or_remote": "remote",
            "reason": "The time taking for making these requests is too long, please set the mass_stats parameter to True",
        }
    elif await estimate_query_size(client = client, quries = quries) > get_available_memory_mb():
        return {
            "local_or_remote": "remote",
            "reason": "The size of the dataset is too large, please set the mass_stats parameter to True",
        }
    else:
        return {
            "local_or_remote": "local",
            "reason": "The number of the requests is not too large, and the time taking for making these requests is not too long, and the size of the dataset is not too large",
        }
    
def gdf_to_json(
    gdf: GeoDataFrame,
    expr: str,
    in_crs: str = "epsg:4326",
    out_crs: str = "epsg:4326",
    resolution: int = -1,
    geom_fix: bool = False,
    id_column: Optional[str] = None,
):
    """
    Convert a GeoDataFrame to a list of JSON requests for mass_stats processing.
    
    Args:
        gdf: GeoDataFrame containing geometries and optional metadata
        expr: Expression to evaluate
        in_crs: Input coordinate reference system
        out_crs: Output coordinate reference system
        resolution: Resolution parameter
        geom_fix: Whether to fix geometry issues
        id_column: Optional column name to use for group and file names
        
    Returns:
        list: List of dictionaries formatted for mass_stats requests
    """
    mass_stats_requests = []
    
    for idx, row in gdf.iterrows():
        request_feature = {
            "expr": expr,
            "feature": {
                "type": "Feature",
                "geometry": mapping(gdf.geometry.iloc[idx]),
                "properties": {}
            },
            "in_crs": in_crs,
            "out_crs": out_crs,
            "resolution": resolution,
            "geom_fix": geom_fix,
        }
        
        if id_column is not None and id_column in gdf.columns:
            identifier = str(row[id_column])
            group_name = f"group_{identifier}"
            file_name = f"file_{identifier}"
        else:
            group_name = f"group_{idx}"
            file_name = f"file_{idx}"
            
        request_entry = {
            "group": group_name,
            "file": file_name,
            "request": request_feature,
        }
        
        mass_stats_requests.append(request_entry)
        
    return mass_stats_requests

async def handle_mass_stats(
    client,
    gdf: GeoDataFrame,
    expr: str,
    in_crs: str = "epsg:4326",
    out_crs: str = "epsg:4326",
    resolution: int = -1,
    geom_fix: bool = False,
    id_column: Optional[str] = None,
):
    request_json = gdf_to_json(gdf=gdf, expr=expr, in_crs=in_crs, out_crs=out_crs, 
                              resolution=resolution, geom_fix=geom_fix, id_column=id_column)
    
    job_response = await client.mass_stats.execute_job(
        name=f"zonal-stats-{str(uuid.uuid4())[:6]}",
        output="netcdf",
        config={},
        request_json=request_json,
        overwrite=True,
    )
    
    # Extract the actual task ID from the response
    if isinstance(job_response, dict) and 'task_id' in job_response:
        return job_response['task_id']  # Return just the string ID
    else:
        return job_response  # In case it's already just the ID


async def zonal_stats(
    client,
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
    """Compute zonal statistics for all geometries in a GeoDataFrame."""
    if mass_stats:
        mass_stats_id = await handle_mass_stats(
            client = client,
            gdf = gdf,
            expr = expr,
            in_crs = in_crs,
            out_crs = out_crs,
            resolution = resolution,
            geom_fix = geom_fix,
            id_column = id_column,
        )
        job_name = await client.mass_stats.track_job([mass_stats_id])
        job_name = job_name[mass_stats_id]["name"]
        cloud_files_object = cloud_object(job_id = mass_stats_id, job_name = job_name, client = client)

        return cloud_files_object
    
    quries = []
    for i in range(len(gdf)):
        quries.append({
            "expr": expr,
            "feature": {
                "type": "Feature",
                "geometry": mapping(gdf.geometry.iloc[i]),
                "properties": {}
            },
            "in_crs": in_crs,
            "out_crs": out_crs,
            "resolution": resolution,
            "geom_fix": geom_fix,
        })

    local_or_remote_result = await local_or_remote(client= client, quries = quries)
    if local_or_remote_result["local_or_remote"] == "remote":
        raise ValueError(local_or_remote_result["reason"])
    else:
        gdf_with_datasets = await request_geoquery_list(client = client, quries = quries, conc = conc)
        gdf_with_datasets.attrs["cloud_metadata"] = {
            "is_cloud_backed": False,
        } 
        gdf_with_datasets = expand_on_variables_and_time(gdf_with_datasets)
        
        # If an id_column is provided, attach it to the result and include in the index
        if id_column is not None and id_column in gdf.columns:
            # Build a mapping from input geometries to id values (use WKB for robust equality)
            geometry_to_id = {geom.wkb: id_val for geom, id_val in zip(gdf.geometry, gdf[id_column])}

            # Determine geometry values in the result (index may be geometry or (geometry, time))
            if hasattr(gdf_with_datasets.index, 'names') and 'geometry' in gdf_with_datasets.index.names:
                if isinstance(gdf_with_datasets.index, pd.MultiIndex):
                    geometry_index = gdf_with_datasets.index.get_level_values('geometry')
                else:
                    geometry_index = gdf_with_datasets.index
                id_values = [geometry_to_id.get(geom.wkb) for geom in geometry_index]
                gdf_with_datasets[id_column] = id_values
                # Reset index to control index composition precisely, then set to desired levels
                gdf_with_datasets = gdf_with_datasets.reset_index()
                if 'time' in gdf_with_datasets.columns:
                    gdf_with_datasets = gdf_with_datasets.set_index([id_column, 'geometry', 'time'])
                else:
                    gdf_with_datasets = gdf_with_datasets.set_index([id_column, 'geometry'])
            else:
                # geometry exists as a column
                id_values = [geometry_to_id.get(geom.wkb) for geom in gdf_with_datasets['geometry']]
                gdf_with_datasets[id_column] = id_values
                if 'time' in gdf_with_datasets.columns:
                    gdf_with_datasets = gdf_with_datasets.set_index([id_column, 'geometry', 'time'])
                else:
                    gdf_with_datasets = gdf_with_datasets.set_index([id_column, 'geometry'])
    return gdf_with_datasets

