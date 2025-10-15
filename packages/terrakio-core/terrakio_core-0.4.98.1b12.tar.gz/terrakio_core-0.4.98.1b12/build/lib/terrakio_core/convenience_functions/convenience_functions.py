
import os
import asyncio
import tempfile
import time
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import mapping
from pathlib import Path
from ..exceptions import APIError, ConfigurationError
from ..helper.bounded_taskgroup import BoundedTaskGroup
from ..helper.tiles import tiles
import uuid
import xarray as xr
import random
import psutil
import copy
from shapely.geometry import shape
from shapely.ops import transform
from shapely.geometry import box
import pyproj

import pandas as pd
import geopandas as gpd

from typing import Optional

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

async def request_geoquery_list(
        client,
        quries: list[dict],
        conc: int = 20,
):
    """
    Execute multiple geo queries.
    
    Args:
        client: The Terrakio client instance
        quries: List of dictionaries containing query parameters
        conc: The concurrency level for the requests
        
    Returns:
        List of query results
        
    Raises:
        ValueError: If the queries list is empty
    """
    if not quries:
        raise ValueError("Queries list cannot be empty")
    if conc > 100:
        raise ValueError("Concurrency (conc) is too high. Please set conc to 100 or less.")

    for i, query in enumerate(quries):
        if 'expr' not in query:
            raise ValueError(f"Query at index {i} is missing the required 'expr' key")
        if 'feature' not in query:
            raise ValueError(f"Query at index {i} is missing the required 'feature' key")
        if 'in_crs' not in query:
            raise ValueError(f"Query at index {i} is missing the required 'in_crs' key")
    
    completed_count = 0
    lock = asyncio.Lock()
    async def single_geo_query(query):
        """
        Execute multiple geo queries concurrently.
        
        Args:
            quries: List of dictionaries containing query parameters
        """
        total_number_of_requests = len(quries)
        nonlocal completed_count
        try:
            result = await client.geoquery(**query)
            if isinstance(result, dict) and result.get("error"):
                error_msg = f"Request failed: {result.get('error_message', 'Unknown error')}"
                if result.get('status_code'):
                    error_msg = f"Request failed with status {result['status_code']}: {result.get('error_message', 'Unknown error')}"
                raise APIError(error_msg)
            if isinstance(result, list):
                result = result[0]
                timestamp_number = result['request_count']
                return timestamp_number
            if not isinstance(result, xr.Dataset):
                raise ValueError(f"Expected xarray Dataset, got {type(result)}")
            
            async with lock:
                completed_count += 1
                if completed_count % max(1, total_number_of_requests // 10) == 0:
                    client.logger.info(f"Progress: {completed_count}/{total_number_of_requests} requests processed")
            return result   
        except Exception as e:
            async with lock:
                completed_count += 1
            raise
    
    try:
        async with BoundedTaskGroup(max_concurrency=conc) as tg:
            tasks = [tg.create_task(single_geo_query(quries[idx])) for idx in range(len(quries))]
        all_results = [task.result() for task in tasks]

    except* Exception as eg:
        for e in eg.exceptions:
            if hasattr(e, 'response'):
                raise APIError(f"API request failed: {e.response.text}")
        raise
    client.logger.info("All requests completed!")
     
    if not all_results:
        raise ValueError("No valid results were returned for any geometry")
    if isinstance(all_results, list) and type(all_results[0]) == int:
        return sum(all_results)/len(all_results)
    else:
        geometries = []
        for query in quries:
            feature = query['feature']
            geometry = shape(feature['geometry'])
            geometries.append(geometry)
        result_gdf = gpd.GeoDataFrame({
            'geometry': geometries,
            'dataset': all_results
        })
        return result_gdf

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
    
    # Loop through each row in the GeoDataFrame
    for idx, row in gdf.iterrows():
        # Create the request feature
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
        
        # Determine group name and file name based on id_column
        if id_column is not None and id_column in gdf.columns:
            # Use the value from the specified column as group and file name
            identifier = str(row[id_column])
            group_name = f"group_{identifier}"
            file_name = f"file_{identifier}"
        else:
            # Use the index as group and file name
            group_name = f"group_{idx}"
            file_name = f"file_{idx}"
            
        # Create the complete request entry
        request_entry = {
            "group": group_name,
            "file": file_name,
            "request": request_feature,
        }
        
        # Add the request to our list
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
    # we have the handle mass stats function, we need to have the list of quries, and we need to pass the quries to the mass stats function
    # we have the three different variables
    
    # Check if id_column is provided
    # if id_column is None:
        # Handle case where no ID column is specified
        # this means that the id column is none, so we could just use the default value of 1 2 3 4
    request_json = gdf_to_json(gdf = gdf, expr = expr, in_crs = in_crs, out_crs = out_crs, resolution = resolution, geom_fix = geom_fix, id_column = id_column)
    # we need to call the execute job function
    job_id =await client.mass_stats.execute_job(
        name = "zonal_stats_job",
        output = "netcdf",
        config = {},
        request_json = request_json,
        overwrite = True,
    )
    return job_id
# async def test_regular_async_mass_stats(regular_async_client):
#     """Test mass statistics with regular client async"""
#     start_result = await regular_async_client.mass_stats.execute_job(
#         name="test_regular_mass_stats_test",
#         region="aus",
#         output="csv",
#         config={},
#         request_json = "./test_config.json",
#         manifest_json = "./test_manifest.json",
#         overwrite=True,
#     )
#     assert isinstance(start_result, dict)
#     assert 'task_id' in start_result
        
        # return 
    # else:
    #     # Handle case where ID column is specified
    #     # Verify the column exists in the GeoDataFrame
        
    #     if id_column not in gdf.columns:
    #         raise ValueError(f"ID column '{id_column}' not found in GeoDataFrame columns: {list(gdf.columns)}")
    # pass
    # the second case is that we have an id_column, we need to use the id_column to create the group name

# we have the mass stats as one of the parameters, so that when a user wants a mass 
# for both cases we need to have the list of quries
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
            id_column = id_column
        )
        # if we started the mass stats job, we need to return the job id 
        return mass_stats_id
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
        gdf_with_datasets = expand_on_variables_and_time(gdf_with_datasets)
    return gdf_with_datasets

async def create_dataset_file(
    client,
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
    
    name = f"tiles-{uuid.uuid4().hex[:8]}"
    
    body, reqs, groups = tiles(
        name = name, 
        aoi = aoi, 
        expression = expression,
        output = output,
        tile_size = 128,
        crs = in_crs,
        res = res,
        region = region,
        to_crs = to_crs,
        fully_cover = True,
        overwrite = overwrite,
        skip_existing = skip_existing,
        non_interactive = non_interactive
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tempreq:
        tempreq.write(reqs)
        tempreqname = tempreq.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tempmanifest:
        tempmanifest.write(groups)
        tempmanifestname = tempmanifest.name

    task_id = await client.mass_stats.execute_job(
        name=body["name"],
        region=body["region"],
        output=body["output"],
        config = {},
        overwrite=body["overwrite"],
        skip_existing=body["skip_existing"],
        request_json=tempreqname,
        manifest_json=tempmanifestname,
    )

    start_time = time.time()
    status = None
    
    while True:
        try:
            taskid = task_id['task_id']
            trackinfo = await client.mass_stats.track_job([taskid])
            client.logger.info("the trackinfo is: ", trackinfo)
            status = trackinfo[taskid]['status']
            
            if status == 'Completed':
                client.logger.info('Tiles generated successfully!')
                break
            elif status in ['Failed', 'Cancelled', 'Error']:
                raise RuntimeError(f"Job {taskid} failed with status: {status}")
            else:
                elapsed_time = time.time() - start_time
                client.logger.info(f"Job status: {status} - Elapsed time: {elapsed_time:.1f}s", end='\r')
                
                await asyncio.sleep(poll_interval)
                
                
        except KeyboardInterrupt:
            client.logger.info(f"\nInterrupted! Job {taskid} is still running in the background.")
            raise
        except Exception as e:
            client.logger.info(f"\nError tracking job: {e}")
            raise

    os.unlink(tempreqname)
    os.unlink(tempmanifestname)

    combine_result = await client.mass_stats.combine_tiles(body["name"], body["overwrite"], body["output"])
    combine_task_id = combine_result.get("task_id")

    combine_start_time = time.time()
    while True:
        try:
            trackinfo = await client.mass_stats.track_job([combine_task_id])
            client.logger.info('client create dataset file track info:', trackinfo)
            if body["output"] == "netcdf":
                download_file_name = trackinfo[combine_task_id]['folder'] + '.nc'
            elif body["output"] == "geotiff":
                download_file_name = trackinfo[combine_task_id]['folder'] + '.tif'
            bucket = trackinfo[combine_task_id]['bucket']
            combine_status = trackinfo[combine_task_id]['status']
            if combine_status == 'Completed':
                client.logger.info('Tiles combined successfully!')
                break
            elif combine_status in ['Failed', 'Cancelled', 'Error']:
                raise RuntimeError(f"Combine job {combine_task_id} failed with status: {combine_status}")
            else:
                elapsed_time = time.time() - combine_start_time
                client.logger.info(f"Combine job status: {combine_status} - Elapsed time: {elapsed_time:.1f}s", end='\r')
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            client.logger.info(f"\nInterrupted! Combine job {combine_task_id} is still running in the background.")
            raise
        except Exception as e:
            client.logger.info(f"\nError tracking combine job: {e}")
            raise

    if download_path:
        await client.mass_stats.download_file(
            job_name=body["name"],
            bucket=bucket,
            file_type='processed',
            page_size=10,
            output_path=download_path,
        )
    else:
        path = f"{body['name']}/outputs/merged/{download_file_name}"
        client.logger.info(f"Combined file is available at {path}")

    return {"generation_task_id": task_id, "combine_task_id": combine_task_id}
