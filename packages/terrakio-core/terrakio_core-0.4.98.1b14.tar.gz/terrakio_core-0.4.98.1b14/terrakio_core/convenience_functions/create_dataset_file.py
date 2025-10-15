import asyncio
import os
import tempfile
import time
import uuid

from ..helper.tiles import tiles

async def create_dataset_file(
    client,
    aoi: str,
    expression: str,
    output: str,
    download_path: str,
    in_crs: str = "epsg:4326",
    to_crs: str = "epsg:4326",
    res: float = 0.0001,
    region: str = None,
    overwrite: bool = False,
    skip_existing: bool = False,
    non_interactive: bool = True,
    name: str | None = None,
    poll_interval: int = 30,
    max_file_size_mb: int = 5120,
    tile_size: int = 1024,
    mask: bool = True
) -> dict:
    
    if not name:
        name = f"file-gen-{uuid.uuid4().hex[:8]}"
    
    body, reqs, groups = tiles(
        name = name, 
        aoi = aoi, 
        expression = expression,
        output = output,
        tile_size = tile_size,
        crs = in_crs,
        res = res,
        region = region,
        to_crs = to_crs,
        mask = mask,
        overwrite = overwrite,
        skip_existing = skip_existing,
        non_interactive = non_interactive
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tempreq:
        tempreq.write(reqs)
        tempreqname = tempreq.name

    task_id = await client.mass_stats.execute_job(
        name=body["name"],
        region=body["region"],
        output=body["output"],
        config = {},
        overwrite=body["overwrite"],
        skip_existing=body["skip_existing"],
        request_json=tempreqname,
    )

    start_time = time.time()
    status = None
    client.logger.info(f"Tracking data generation job {task_id['task_id']}...")
    while True:
        try:
            taskid = task_id['task_id']
            trackinfo = await client.mass_stats.track_job([taskid])
            status = trackinfo[taskid]['status']
            if status == 'Completed':
                client.logger.info('Data generated successfully!')
                break
            elif status in ['Failed', 'Cancelled', 'Error']:
                raise RuntimeError(f"Job {taskid} failed with status: {status}")
            else:
                elapsed_time = time.time() - start_time
                client.logger.info(f"Job status: {status} - Elapsed time: {elapsed_time:.1f}s")
                await asyncio.sleep(poll_interval)
                
                
        except KeyboardInterrupt:
            client.logger.info(f"\nInterrupted! Job {taskid} is still running in the background.")
            raise
        except Exception as e:
            client.logger.info(f"\nError tracking job: {e}")
            raise

    os.unlink(tempreqname)

    combine_result = await client.mass_stats.combine_tiles(body["name"], body["overwrite"], body["output"], max_file_size_mb=max_file_size_mb)
    combine_task_id = combine_result.get("task_id")

    combine_start_time = time.time()
    client.logger.info(f"Tracking file generation job {combine_task_id}...")
    while True:
        try:
            trackinfo = await client.mass_stats.track_job([combine_task_id])
            if body["output"] == "netcdf":
                download_file_name = trackinfo[combine_task_id]['folder'] + '.nc'
            elif body["output"] == "geotiff":
                download_file_name = trackinfo[combine_task_id]['folder'] + '.tif'
            bucket = trackinfo[combine_task_id]['bucket']
            combine_status = trackinfo[combine_task_id]['status']
            if combine_status == 'Completed':
                client.logger.info('File/s generated successfully!')
                break
            elif combine_status in ['Failed', 'Cancelled', 'Error']:
                raise RuntimeError(f"File generation job {combine_task_id} failed with status: {combine_status}")
            else:
                elapsed_time = time.time() - combine_start_time
                client.logger.info(f"File generation job status: {combine_status} - Elapsed time: {elapsed_time:.1f}s")
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            client.logger.info(f"\nInterrupted! File generation job {combine_task_id} is still running in the background.")
            raise
        except Exception as e:
            client.logger.info(f"\nError tracking file generation job: {e}")
            raise

    if download_path:
        await client.mass_stats.download_file(
            job_name=body["name"],
            bucket=bucket,
            file_type='processed',
            folder='file-gen',
            page_size=100,
            output_path=download_path,
        )
    else:
        path = f"{body['name']}/outputs/merged/{download_file_name}"
        client.logger.info(f"Dataset file/s is available at {path}")

    return {"generation_task_id": task_id, "combine_task_id": combine_task_id}
