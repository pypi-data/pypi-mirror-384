import asyncio
import xarray as xr

import geopandas as gpd
from shapely.geometry import shape

from ..exceptions import APIError
from ..helper.bounded_taskgroup import BoundedTaskGroup

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