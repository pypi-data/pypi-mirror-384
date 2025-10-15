import json
import os
import time
from typing import Dict, Any, Optional, List, Union

import aiohttp
import typer
from dateutil import parser
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from ..exceptions import (
    CancelAllTasksError,
    CancelCollectionTasksError,
    CancelTaskError,
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    CreateCollectionError,
    DeleteCollectionError,
    DownloadFilesError,
    GetCollectionError,
    GetTaskError,
    InvalidCollectionTypeError,
    ListCollectionsError,
    ListTasksError,
    TaskNotFoundError,
    UploadArtifactsError,
    UploadRequestsError,
)
from ..helper.decorators import require_api_key


class MassStats:
    def __init__(self, client):
        self._client = client
        self.console = Console()

    async def track_progress(self, task_id):
        task_info = await self.get_task(task_id=task_id)
        number_of_jobs = task_info["task"]["total"]
        start_time = parser.parse(task_info["task"]["createdAt"])
        
        self.console.print(f"[bold cyan]Tracking task: {task_id}[/bold cyan]")
        
        completed_jobs_info = []
        
        def get_job_description(job_info, include_status=False):
            if not job_info:
                return "No job info"
            
            service = job_info.get("service", "Unknown service")
            desc = service
            
            if include_status:
                status = job_info.get("status", "unknown")
                desc += f" - {status}"
            
            return desc
        
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
        )
        
        with progress:
            last_completed_count = 0
            current_job_task = None
            current_job_description = None
            
            while len(completed_jobs_info) < number_of_jobs:
                task_info = await self.get_task(task_id=task_id)
                completed_number = task_info["task"]["completed"]
                current_job_info = task_info["currentJob"]
                
                if completed_number > last_completed_count:
                    if current_job_task is not None:
                        completed_description = current_job_description.replace(" - pending", "").replace(" - running", "").replace(" - waiting", "")
                        completed_description += " - completed"
                        
                        progress.update(
                            current_job_task,
                            description=f"[{last_completed_count + 1}/{number_of_jobs}] {completed_description}",
                            completed=100
                        )
                        completed_jobs_info.append({
                            "task": current_job_task,
                            "description": completed_description,
                            "job_number": last_completed_count + 1
                        })
                        current_job_task = None
                        current_job_description = None
                    
                    last_completed_count = completed_number
                
                if current_job_info:
                    status = current_job_info["status"]
                    current_job_description = get_job_description(current_job_info, include_status=True)
                    
                    total_value = current_job_info.get("total", 0)
                    completed_value = current_job_info.get("completed", 0)
                    
                    if total_value == -9999:
                        percent = 0
                    elif total_value > 0:
                        percent = int(completed_value / total_value * 100)
                    else:
                        percent = 0
                    
                    if current_job_task is None:
                        current_job_task = progress.add_task(
                            f"[{completed_number + 1}/{number_of_jobs}] {current_job_description}",
                            total=100,
                            start_time=start_time
                        )
                    else:
                        progress.update(
                            current_job_task,
                            description=f"[{completed_number + 1}/{number_of_jobs}] {current_job_description}",
                            completed=percent
                        )
                    
                    if status == "Error":
                        self.console.print("[bold red]Error![/bold red]")
                        raise typer.Exit(code=1)
                    if status == "Cancelled":
                        self.console.print("[bold orange]Cancelled![/bold orange]")
                        raise typer.Exit(code=1)
                    elif status == "Completed":
                        completed_description = current_job_description.replace(" - pending", "").replace(" - running", "").replace(" - waiting", "")
                        completed_description += " - completed"
                        progress.update(
                            current_job_task, 
                            description=f"[{completed_number + 1}/{number_of_jobs}] {completed_description}",
                            completed=100
                        )
                
                if completed_number == number_of_jobs and current_job_info is None:
                    if current_job_task is not None:
                        completed_description = current_job_description.replace(" - pending", "").replace(" - running", "").replace(" - waiting", "")
                        completed_description += " - completed"
                        progress.update(
                            current_job_task,
                            description=f"[{number_of_jobs}/{number_of_jobs}] {completed_description}",
                            completed=100
                        )
                        completed_jobs_info.append({
                            "task": current_job_task,
                            "description": completed_description,
                            "job_number": number_of_jobs
                        })
                    break
                
                time.sleep(10)
        
        self.console.print(f"[bold green]All {number_of_jobs} jobs finished![/bold green]")

    # below are functions related to collection
    @require_api_key
    async def create_collection(
        self, 
        collection: str, 
        bucket: Optional[str] = None, 
        location: Optional[str] = None, 
        collection_type: str = "basic"
    ) -> Dict[str, Any]:
        """
        Create a collection for the current user.

        Args:
            collection: The name of the collection (required)
            bucket: The bucket to use (optional, admin only)
            location: The location to use (optional, admin only)
            collection_type: The type of collection to create (optional, defaults to "basic")
            
        Returns:
            API response as a dictionary containing the collection id
            
        Raises:
            CollectionAlreadyExistsError: If the collection already exists
            InvalidCollectionTypeError: If the collection type is invalid
            CreateCollectionError: If the API request fails due to unknown reasons
        """
        payload = {
            "collection_type": collection_type
        }
        
        if bucket is not None:
            payload["bucket"] = bucket
        
        if location is not None:
            payload["location"] = location
        
        response, status = await self._client._terrakio_request("POST", f"collections/{collection}", json=payload)

        if status != 200:
            if status == 400:
                raise CollectionAlreadyExistsError(f"Collection {collection} already exists", status_code=status)
            if status == 422:
                raise InvalidCollectionTypeError(f"Invalid collection type: {collection_type}", status_code=status)
            raise CreateCollectionError(f"Create collection failed with status {status}", status_code=status)

        return response

    @require_api_key
    async def get_collection(self, collection: str) -> Dict[str, Any]:
        """
        Get a collection by name.

        Args:
            collection: The name of the collection to retrieve(required)
            
        Returns:
            API response as a dictionary containing collection information
            
        Raises:
            CollectionNotFoundError: If the collection is not found
            GetCollectionError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("GET", f"collections/{collection}")

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetCollectionError(f"Get collection failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def list_collections(
        self,
        collection_type: Optional[str] = None,
        limit: Optional[int] = 10,
        page: Optional[int] = 0
    ) -> List[Dict[str, Any]]:
        """
        List collections for the current user.

        Args:
            collection_type: Filter by collection type (optional)
            limit: Number of collections to return (optional, defaults to 10)
            page: Page number (optional, defaults to 0)
            
        Returns:
            API response as a list of dictionaries containing collection information
            
        Raises:
            ListCollectionsError: If the API request fails due to unknown reasons
        """
        params = {}
        
        if collection_type is not None:
            params["collection_type"] = collection_type
        
        if limit is not None:
            params["limit"] = limit
            
        if page is not None:
            params["page"] = page
        
        response, status = await self._client._terrakio_request("GET", "collections", params=params)
        if status != 200:
            raise ListCollectionsError(f"List collections failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def delete_collection(
        self, 
        collection: str, 
        full: Optional[bool] = False, 
        outputs: Optional[list] = [], 
        data: Optional[bool] = False
    ) -> Dict[str, Any]:
        """
        Delete a collection by name.

        Args:
            collection: The name of the collection to delete (required)
            full: Delete the full collection (optional, defaults to False)
            outputs: Specific output folders to delete (optional, defaults to empty list)
            data: Whether to delete raw data (xdata folder) (optional, defaults to False)
            
        Returns:
            API response as a dictionary confirming deletion
            
        Raises:
            CollectionNotFoundError: If the collection is not found
            DeleteCollectionError: If the API request fails due to unknown reasons
        """
        payload = {
            "full": full,
            "outputs": outputs,
            "data": data
        }
        
        response, status = await self._client._terrakio_request("DELETE", f"collections/{collection}", json=payload)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise DeleteCollectionError(f"Delete collection failed with status {status}", status_code=status)

        return response

    # below are functions related to tasks
    @require_api_key
    async def list_tasks(
        self,
        limit: Optional[int] = 10,
        page: Optional[int] = 0
    ) -> List[Dict[str, Any]]:
        """
        List tasks for the current user.

        Args:
            limit: Number of tasks to return (optional, defaults to 10)
            page: Page number (optional, defaults to 0)
        
        Returns:
            API response as a list of dictionaries containing task information
            
        Raises:
            ListTasksError: If the API request fails due to unknown reasons
        """
        params = {
            "limit": limit,
            "page": page
        }
        response, status = await self._client._terrakio_request("GET", "tasks", params=params)

        if status != 200:
            raise ListTasksError(f"List tasks failed with status {status}", status_code=status)

        return response
        
    @require_api_key
    async def get_task(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Get task information by task ID.

        Args:
            task_id: ID of task to track
        
        Returns:
            API response as a dictionary containing task information

        Raises:
            TaskNotFoundError: If the task is not found
            GetTaskError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("GET", f"tasks/info/{task_id}")

        if status != 200:
            if status == 404:
                raise TaskNotFoundError(f"Task {task_id} not found", status_code=status)
            raise GetTaskError(f"Get task failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def cancel_task(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a task by task ID.

        Args:
            task_id: ID of task to cancel

        Returns:
            API response as a dictionary containing task information

        Raises:
            TaskNotFoundError: If the task is not found
            CancelTaskError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("POST", f"tasks/cancel/{task_id}")
        
        if status != 200:
            if status == 404:
                raise TaskNotFoundError(f"Task {task_id} not found", status_code=status)
            raise CancelTaskError(f"Cancel task failed with status {status}", status_code=status)

        return response

    @require_api_key
    async def cancel_collection_tasks(
        self,
        collection: str
    ) -> Dict[str, Any]:
        """
        Cancel all tasks for a collection.

        Args:
            collection: Name of collection

        Returns:
            API response as a dictionary containing task information for the collection

        Raises:
            CollectionNotFoundError: If the collection is not found
            CancelCollectionTasksError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("POST", f"collections/{collection}/cancel")
        
        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise CancelCollectionTasksError(f"Cancel collection tasks failed with status {status}", status_code=status)
    
        return response

    @require_api_key
    async def cancel_all_tasks(
        self
    ) -> Dict[str, Any]:
        """
        Cancel all tasks for the current user.

        Returns:
            API response as a dictionary containing task information for all tasks

        Raises:
            CancelAllTasksError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("POST", "tasks/cancel")

        if status != 200:
            raise CancelAllTasksError(f"Cancel all tasks failed with status {status}", status_code=status)

        return response

    # below are functions related to the web ui and needs to be deleted in the future
    @require_api_key
    async def upload_artifacts(
        self,
        collection: str,
        file_type: str,
        compressed: Optional[bool] = True
    ) -> Dict[str, Any]:
        """
        Retrieve signed url to upload artifact file to a collection.

        Args:
            collection: Name of collection
            file_type: The extension of the file
            compressed: Whether to compress the file using gzip or not (defaults to True)
        
        Returns:
            API response as a dictionary containing the upload URL

        Raises:
            CollectionNotFoundError: If the collection is not found
            UploadArtifactsError: If the API request fails due to unknown reasons
        """
        params = {
            "file_type": file_type,
            "compressed": str(compressed).lower(),
        }

        response, status = await self._client._terrakio_request("GET", f"collections/{collection}/upload", params=params)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise UploadArtifactsError(f"Upload artifacts failed with status {status}", status_code=status)

        return response

    @require_api_key
    async def zonal_stats(
        self,
        collection: str,
        id_property: str,
        column_name: str,
        expr: str,
        resolution: Optional[int] = 1,
        in_crs: Optional[str] = "epsg:4326",
        out_crs: Optional[str] = "epsg:4326"
    ) -> Dict[str, Any]:
        """
        Run zonal stats over uploaded geojson collection.

        Args:
            collection: Name of collection
            id_property: Property key in geojson to use as id
            column_name: Name of new column to add
            expr: Terrak.io expression to evaluate
            resolution: Resolution of request (optional, defaults to 1)
            in_crs: CRS of geojson (optional, defaults to "epsg:4326")
            out_crs: Desired output CRS (optional, defaults to "epsg:4326")

        Returns:
            API response as a dictionary containing task information

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails due to unknown reasons
        """
        payload = {
            "id_property": id_property,
            "column_name": column_name,
            "expr": expr,
            "resolution": resolution,
            "in_crs": in_crs,
            "out_crs": out_crs
        }
        
        response, status = await self._client._terrakio_request("POST", f"collections/{collection}/zonal_stats", json=payload)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Zonal stats failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def zonal_stats_transform(
        self,
        collection: str,
        consumer: str
    ) -> Dict[str, Any]:
        """
        Transform raw data in collection. Creates a new collection.

        Args:
            collection: Name of collection
            consumer: Post processing script (file path or script content)

        Returns:
            API response as a dictionary containing task information

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails due to unknown reasons
        """
        if os.path.isfile(consumer):
            with open(consumer, 'r') as f:
                script_content = f.read()
        else:
            script_content = consumer

        files = {
            'consumer': ('script.py', script_content, 'text/plain')
        }
        
        response, status = await self._client._terrakio_request(
            "POST", 
            f"collections/{collection}/transform", 
            files=files
        )

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Transform failed with status {status}", status_code=status)
        
        return response

    async def _upload_requests(
        self,
        collection: str
    ) -> Dict[str, Any]:
        """
        Retrieve signed url to upload requests for a collection.

        Args:
            collection: Name of collection
        
        Returns:
            API response as a dictionary containing the upload URL

        Raises:
            CollectionNotFoundError: If the collection is not found
            UploadRequestsError: If the API request fails due to unknown reasons
        """
        response, status = await self._client._terrakio_request("GET", f"collections/{collection}/upload/requests")

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise UploadRequestsError(f"Upload requests failed with status {status}", status_code=status)

        return response

    @require_api_key
    async def _upload_file(self, file_path: str, url: str, use_gzip: bool = True):
        """
        Helper method to upload a JSON file to a signed URL.
        
        Args:
            file_path: Path to the JSON file
            url: Signed URL to upload to
            use_gzip: Whether to compress the file with gzip
        """
        try:
            with open(file_path, 'r') as file:
                json_data = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")
        
        return await self._upload_json_data(json_data, url, use_gzip)

    @require_api_key
    async def _upload_json_data(self, json_data, url: str, use_gzip: bool = True):
        """
        Helper method to upload JSON data directly to a signed URL.
        
        Args:
            json_data: JSON data (dict or list) to upload
            url: Signed URL to upload to
            use_gzip: Whether to compress the data with gzip
        """
        if hasattr(json, 'dumps') and 'ignore_nan' in json.dumps.__code__.co_varnames:
            dumps_kwargs = {'ignore_nan': True}
        else:
            dumps_kwargs = {}
        
        if use_gzip:
            import gzip
            body = gzip.compress(json.dumps(json_data, **dumps_kwargs).encode('utf-8'))
            headers = {
                'Content-Type': 'application/json',
                'Content-Encoding': 'gzip'
            }
        else:
            body = json.dumps(json_data, **dumps_kwargs).encode('utf-8')
            headers = {
                'Content-Type': 'application/json'
            }
        
        response = await self._client._regular_request("PUT", url, data=body, headers=headers)
        return response

    @require_api_key
    async def generate_data(
        self,
        collection: str,
        file_path: str,
        output: str,
        skip_existing: Optional[bool] = True,
        force_loc: Optional[bool] = None,
        server: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate data for a collection.

        Args:
            collection: Name of collection
            file_path: Path to the file to upload
            output: Output type (str)
            force_loc: Write data directly to the cloud under this folder
            skip_existing: Skip existing data
            server: Server to use
        
        Returns:
            API response as a dictionary containing task information

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails due to unknown reasons
        """
        
        await self.get_collection(collection = collection)

        upload_urls = await self._upload_requests(
            collection = collection
        )
        
        url = upload_urls['url']

        await self._upload_file(file_path, url)
        
        payload = {"output": output, "skip_existing": skip_existing}
        
        if force_loc is not None:
            payload["force_loc"] = force_loc
        if server is not None:
            payload["server"] = server
        
        response, status = await self._client._terrakio_request("POST", f"collections/{collection}/generate_data", json=payload)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Generate data failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def post_processing(
        self,
        collection: str,
        folder: str,
        consumer: str
    ) -> Dict[str, Any]:
        """
        Run post processing for a collection.

        Args:
            collection: Name of collection
            folder: Folder to store output
            consumer: Path to post processing script

        Returns:
            API response as a dictionary containing task information

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails due to unknown reasons
        """

        await self.get_collection(collection = collection)

        with open(consumer, 'rb') as f:
            form = aiohttp.FormData()
            form.add_field('folder', folder)
            form.add_field(
                'consumer',
                f.read(),
                filename='consumer.py',
                content_type='text/x-python'
            )
        
        response, status = await self._client._terrakio_request(
            "POST",
            f"collections/{collection}/post_process",
            data=form
        )
        
        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Post processing failed with status {status}", status_code=status)
        
        return response

    @require_api_key
    async def training_samples(
        self,
        collection: str,
        aoi: str,
        expression_x: str,
        filter_x: str = "skip",
        filter_x_rate: float = 1,
        expression_y: str = "skip",
        filter_y: str = "skip",
        filter_y_rate: float = 1,
        samples: int = 1000,
        tile_size: float = 256,
        crs: str = "epsg:3577",
        res: float = 10,
        res_y: float = None,
        skip_test: bool = False,
        start_year: int = None,
        end_year: int = None,
        server: str = None,
        extra_filters: list[str] = None,
        extra_filters_rate: list[float] = None,
        extra_filters_res: list[float] = None
    ) -> dict:
        """
        Generate an AI dataset using specified parameters.

        Args:
            collection: The collection name where we save the results
            aoi: Path to GeoJSON file containing area of interest
            expression_x: Expression for X data (features)
            filter_x: Filter expression for X data (default: "skip")
            filter_x_rate: Filter rate for X data (default: 1)
            expression_y: Expression for Y data (labels) (default: "skip")
            filter_y: Filter expression for Y data (default: "skip")
            filter_y_rate: Filter rate for Y data (default: 1)
            samples: Number of samples to generate (default: 1000)
            tile_size: Size of tiles in pixels (default: 256)
            crs: Coordinate reference system (default: "epsg:3577")
            res: Resolution for X data (default: 10)
            res_y: Resolution for Y data, defaults to res if None
            skip_test: Skip expression validation test (default: False)
            start_year: Start year for temporal filtering
            end_year: End year for temporal filtering
            server: Server to use for processing
            extra_filters: Additional filter expressions
            extra_filters_rate: Rates for additional filters
            extra_filters_res: Resolutions for additional filters

        Returns:
            Response containing task_id and collection name

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails
            TypeError: If extra filters have mismatched rate and resolution lists
        """
        expressions = [{"expr": expression_x, "res": res, "prefix": "x"}]
        
        res_y = res_y or res
        
        if expression_y != "skip":
            expressions.append({"expr": expression_y, "res": res_y, "prefix": "y"})
        
        filters = []
        if filter_x != "skip":
            filters.append({"expr": filter_x, "res": res, "rate": filter_x_rate})
        
        if filter_y != "skip":
            filters.append({"expr": filter_y, "res": res_y, "rate": filter_y_rate})
        
        if extra_filters:
            try:
                extra_filters_combined = zip(extra_filters, extra_filters_res, extra_filters_rate, strict=True)
            except TypeError:
                raise TypeError("Extra filters must have matching rate and resolution.")
            
            for expr, filter_res, rate in extra_filters_combined:
                filters.append({"expr": expr, "res": filter_res, "rate": rate})
        
        if start_year is not None:
            for expr_dict in expressions:
                expr_dict["expr"] = expr_dict["expr"].replace("{year}", str(start_year))
            
            for filter_dict in filters:
                filter_dict["expr"] = filter_dict["expr"].replace("{year}", str(start_year))
        
        if not skip_test:
            for expr_dict in expressions:
                test_request = self._client.model._generate_test_request(expr_dict["expr"], crs, -1)
                await self._client._terrakio_request("POST", "geoquery", json=test_request)
            
            for filter_dict in filters:
                test_request = self._client.model._generate_test_request(filter_dict["expr"], crs, -1)
                await self._client._terrakio_request("POST", "geoquery", json=test_request)
        
        with open(aoi, 'r') as f:
            aoi_data = json.load(f)

        await self.get_collection(
            collection = collection,
        )

        payload = {
            "expressions": expressions,
            "filters": filters,
            "aoi": aoi_data,
            "samples": samples,
            "crs": crs,
            "tile_size": tile_size,
            "res": res,
            "output": "nc",
            "year_range": [start_year, end_year],
            "server": server
        }
        
        task_id_dict, status = await self._client._terrakio_request("POST", f"collections/{collection}/training_samples", json=payload)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Training sample failed with status {status}", status_code=status)
        
        task_id = task_id_dict["task_id"]
        
        await self._client.mass_stats.track_progress(task_id)
        
        return {"task_id": task_id, "collection": collection}

    @require_api_key
    async def download_files(
        self,
        collection: str,
        file_type: str,
        page: Optional[int] = 0,
        page_size: Optional[int] = 100,
        folder: Optional[str] = None,
        url: Optional[bool] = True
    ) -> Dict[str, Any]:
        """
        Get list of signed urls to download files in collection, or download the files directly.

        Args:
            collection: Name of collection
            file_type: Type of files to download - must be either 'raw' or 'processed'
            page: Page number (optional, defaults to 0)
            page_size: Number of files to return per page (optional, defaults to 100)
            folder: If processed file type, which folder to download files from (optional)
            url: If True, return signed URLs; if False, download files directly (optional, defaults to True)

        Returns:
            API response as a dictionary containing list of download URLs (if url=True),
            or a dictionary with downloaded file information (if url=False)

        Raises:
            CollectionNotFoundError: If the collection is not found
            DownloadFilesError: If the API request fails due to unknown reasons
            ValueError: If file_type is not 'raw' or 'processed'
        """
        if file_type not in ['raw', 'processed']:
            raise ValueError(f"file_type must be either 'raw' or 'processed', got '{file_type}'")
        
        params = {"file_type": file_type}
        
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if folder is not None:
            params["folder"] = folder

        response, status = await self._client._terrakio_request("GET", f"collections/{collection}/download", params=params)

        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise DownloadFilesError(f"Download files failed with status {status}", status_code=status)
        
        if url:
            return response
        
        downloaded_files = []
        files_to_download = response.get('files', []) if isinstance(response, dict) else []
        
        async with aiohttp.ClientSession() as session:
            for file_info in files_to_download:
                try:
                    file_url = file_info.get('url')
                    filename = file_info.get('file', '')
                    group = file_info.get('group', '')
                    
                    if not file_url:
                        downloaded_files.append({
                            'filename': filename,
                            'group': group,
                            'error': 'No URL provided'
                        })
                        continue
                    
                    async with session.get(file_url) as file_response:
                        if file_response.status == 200:
                            content = await file_response.read()
                            
                            output_dir = folder if folder else "downloads"
                            if group:
                                output_dir = os.path.join(output_dir, group)
                            os.makedirs(output_dir, exist_ok=True)
                            filepath = os.path.join(output_dir, filename)
                            
                            with open(filepath, 'wb') as f:
                                f.write(content)
                            
                            downloaded_files.append({
                                'filename': filename,
                                'group': group,
                                'filepath': filepath,
                                'size': len(content)
                            })
                        else:
                            downloaded_files.append({
                                'filename': filename,
                                'group': group,
                                'error': f"Failed to download: HTTP {file_response.status}"
                            })
                except Exception as e:
                    downloaded_files.append({
                        'filename': file_info.get('file', 'unknown'),
                        'group': file_info.get('group', ''),
                        'error': str(e)
                    })
        
        return {
            'collection': collection,
            'downloaded_files': downloaded_files,
            'total': len(downloaded_files)
        }

    @require_api_key
    async def gen_and_process(
        self,
        collection: str,
        requests_file: Union[str, Any],
        output: str,
        folder: str,
        consumer: Union[str, Any],
        extra: Optional[Dict[str, Any]] = None,
        force_loc: Optional[bool] = False,
        skip_existing: Optional[bool] = True,
        server: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate data and run post-processing in a single task.

        Args:
            collection: Name of collection
            requests_file: Path to JSON file or file object containing request configurations
            output: Output type (str)
            folder: Folder to store output
            consumer: Path to post processing script or file object
            extra: Additional configuration parameters (optional)
            force_loc: Write data directly to the cloud under this folder (optional, defaults to False)
            skip_existing: Skip existing data (optional, defaults to True)
            server: Server to use (optional)

        Returns:
            API response as a dictionary containing task information

        Raises:
            CollectionNotFoundError: If the collection is not found
            GetTaskError: If the API request fails due to unknown reasons
        """
        await self.get_collection(collection = collection)

        upload_urls = await self._upload_requests(collection=collection)
        url = upload_urls['url']
        
        # Handle requests_file - either file path (str) or file object
        if isinstance(requests_file, str):
            await self._upload_file(requests_file, url)
        else:
            # File object - read JSON and upload directly
            json_data = json.load(requests_file)
            await self._upload_json_data(json_data, url)

        # Handle consumer - either file path (str) or file object
        if isinstance(consumer, str):
            with open(consumer, 'rb') as f:
                consumer_content = f.read()
        else:
            # Assume it's a file object
            consumer_content = consumer.read()
        
        form = aiohttp.FormData()
        form.add_field('output', output)
        form.add_field('force_loc', str(force_loc).lower())
        form.add_field('skip_existing', str(skip_existing).lower())
        
        if server is not None:
            form.add_field('server', server)
        
        form.add_field('extra', json.dumps(extra or {}))
        form.add_field('folder', folder)
        form.add_field(
            'consumer',
            consumer_content,
            filename='consumer.py',
            content_type='text/x-python'
        )
        
        response, status = await self._client._terrakio_request(
            "POST",
            f"collections/{collection}/gen_and_process",
            data=form
        )
        
        if status != 200:
            if status == 404:
                raise CollectionNotFoundError(f"Collection {collection} not found", status_code=status)
            raise GetTaskError(f"Gen and process failed with status {status}", status_code=status)

        return response

    @require_api_key
    async def create_pyramids(
        self,
        collection: str,
        name: str,
        levels: int,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create pyramid tiles for a dataset.

        Args:
            collection: Name of collection
            name: Dataset name
            levels: Maximum zoom level for pyramid (e.g., 8)
            config: Full pyramid configuration dictionary containing:
                - name: Dataset name (will override the name parameter)
                - bucket: GCS bucket name (e.g., "terrakio")
                - products: List of product names (e.g., ["air_temp", "prec"])
                - path: Path pattern (e.g., "pyramids/%s_%s_%03d_%03d_%02d.snp")
                - data_type: Data type (e.g., "float32")
                - i_max: Maximum i index
                - j_max: Maximum j index
                - x_size: Tile size in x (e.g., 400)
                - y_size: Tile size in y (e.g., 400)
                - dates_iso8601: List of ISO8601 date strings
                - no_data: No data value (e.g., -9999.0)

        Returns:
            API response with task_id

        Raises:
            GetTaskError: If the API request fails
        """
        await self.get_collection(collection = collection)

        pyramid_request = {
            'collection_name': collection,
            'name': name,
            'max_zoom': levels,
            **config
        }
        
        response, status = await self._client._terrakio_request(
            "POST",
            "tasks/pyramids",
            json=pyramid_request
        )
        
        if status != 200:
            raise GetTaskError(
                f"Pyramid creation failed with status {status}: {response}", 
                status_code=status
            )
        
        task_id = response["task_id"]
        await self.track_progress(task_id)

        return {"task_id": task_id}