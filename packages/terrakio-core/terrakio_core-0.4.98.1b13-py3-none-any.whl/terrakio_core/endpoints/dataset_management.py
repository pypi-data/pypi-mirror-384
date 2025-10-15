from typing import Any, Dict, List, Optional

from ..exceptions import (
    CommandPermissionError,
    DatasetNotFoundError,
    DatasetPermissionError,
    GetDatasetError,
    ListDatasetsError,
    CreateDatasetError,
    DatasetAlreadyExistsError,
    DeleteDatasetError,
    OverwriteDatasetError,
)
from ..helper.decorators import require_api_key, require_auth, require_token

class DatasetManagement:
    def __init__(self, client):
        self._client = client

    @require_api_key
    async def list_datasets(self, substring: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List datasets, optionally filtering by a substring and collection.
        
        Args:
            substring: Substring to filter by (optional)
            
        Returns:
            List of datasets matching the criteria
        """
        params = {"substring": substring} if substring else None
        response, status = await self._client._terrakio_request("GET", "/datasets", params=params)
        if status != 200:
            raise ListDatasetsError(f"List datasets failed with status {status}", status_code=status)
        return response

    @require_api_key
    async def get_dataset(self, name: str) -> Dict[str, Any]:
        """
        Retrieve dataset info by dataset name.
        
        Args:
            name: The name of the dataset (required)
            
        Returns:
            Dataset information as a dictionary
            
        Raises:
            GetDatasetError: If the API request fails
            DatasetNotFoundError: If the dataset is not found
            DatasetPermissionError: If the user does not have permission to get the dataset
        """
        response, status = await self._client._terrakio_request("GET", f"/datasets/{name}")
        if status != 200:
            if status == 404:
                raise DatasetNotFoundError(f"Dataset {name} not found", status_code = status)
            if status == 403:
                raise DatasetPermissionError(f"You do not have permission to get dataset {name}", status_code = status)
            raise GetDatasetError(f"Get dataset failed with status {status}", status_code = status)
        return response

    @require_api_key
    async def create_dataset(
        self, 
        name: str, 
        products: Optional[List[str]] = None,
        dates_iso8601: Optional[List[str]] = None,
        bucket: Optional[str] = None,
        path: Optional[str] = None,
        data_type: Optional[str] = None,
        no_data: Optional[Any] = None,
        i_max: Optional[int] = None,
        j_max: Optional[int] = None,
        y_size: Optional[int] = None,
        x_size: Optional[int] = None,
        proj4: Optional[str] = None,
        abstract: Optional[str] = None,
        geotransform: Optional[List[float]] = None,
        padding: Optional[Any] = None,
        input: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new dataset.
                            
        Args:
            name: Name of the dataset (required)
            products: List of products
            dates_iso8601: List of dates (will be automatically sorted chronologically)
            bucket: Storage bucket
            path: Storage path
            data_type: Data type
            no_data: No data value
            i_max: Maximum level
            j_max: Maximum level
            y_size: Y size
            x_size: X size
            proj4: Projection string
            abstract: Dataset abstract
            geotransform: Geotransform parameters
            padding: Padding value
                                
        Returns:
            Created dataset information
                                
        Raises:
            APIError: If the API request fails
        """
        payload = {"name": name}
        param_mapping = {
            "products": products,
            "dates_iso8601": dates_iso8601,
            "bucket": bucket,
            "path": path,
            "data_type": data_type,
            "no_data": no_data,
            "i_max": i_max,
            "j_max": j_max,
            "y_size": y_size,
            "x_size": x_size,
            "proj4": proj4,
            "abstract": abstract,
            "geotransform": geotransform,
            "padding": padding,
            "input": input
        }
        for param, value in param_mapping.items():
            if value is not None:
                payload[param] = value
        response, status = await self._client._terrakio_request("POST", "/datasets", json = payload)
        if status != 200:
            if status ==403:
                raise CommandPermissionError(f"You do not have permission to create dataset {name}", status_code = status)
            elif status == 409:
                raise DatasetAlreadyExistsError(f"Dataset {name} already exists", status_code = status)
            raise CreateDatasetError(f"Create dataset failed with status {status}", status_code = status)
        return response
        
    @require_api_key
    async def delete_dataset(self, name: str) -> Dict[str, Any]:
        """
        Delete a dataset by name.
        
        Args:
            name: The name of the dataset (required)
            
        Returns:
            Deleted dataset information
            
        Raises:
            CommandPermissionError: If the user does not have permission to delete the dataset
            DeleteDatasetError: If the API request fails
        """
        response, status = await self._client._terrakio_request("DELETE", f"/datasets/{name}")
        if status != 200:
            if status == 403:
                raise CommandPermissionError(f"You do not have permission to delete dataset {name}", status_code = status)
            raise DeleteDatasetError(f"Delete dataset failed with status {status}", status_code = status)
        return response

    @require_api_key
    def update_dataset(
        self, 
        name: str, 
        append: bool = True, 
        products: Optional[List[str]] = None,
        dates_iso8601: Optional[List[str]] = None,
        bucket: Optional[str] = None,
        path: Optional[str] = None,
        data_type: Optional[str] = None,
        no_data: Optional[Any] = None,
        i_max: Optional[int] = None,
        j_max: Optional[int] = None,
        y_size: Optional[int] = None,
        x_size: Optional[int] = None,
        proj4: Optional[str] = None,
        abstract: Optional[str] = None,
        geotransform: Optional[List[float]] = None,
        padding: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Update an existing dataset.
                            
        Args:
            name: Name of the dataset (required)
            append: Whether to append data or replace (default: True)
            products: List of products
            dates_iso8601: List of dates (will be automatically sorted chronologically)
            bucket: Storage bucket
            path: Storage path
            data_type: Data type
            no_data: No data value
            i_max: Maximum level
            j_max: Maximum level
            y_size: Y size
            x_size: X size
            proj4: Projection string
            abstract: Dataset abstract
            geotransform: Geotransform parameters
            padding: Padding value
                                
        Returns:
            Updated dataset information
                                
        Raises:
            APIError: If the API request fails
        """
        if dates_iso8601 is not None:
            dates_iso8601 = sorted(dates_iso8601)

        params = {"append": str(append).lower()}
        payload = {"name": name}
        param_mapping = {
            "products": products,
            "dates_iso8601": dates_iso8601,
            "bucket": bucket,
            "path": path,
            "data_type": data_type,
            "no_data": no_data,
            "i_max": i_max,
            "j_max": j_max,
            "y_size": y_size,
            "x_size": x_size,
            "proj4": proj4,
            "abstract": abstract,
            "geotransform": geotransform,
            "padding": padding
        }
        for param, value in param_mapping.items():
            if value is not None:
                payload[param] = value
        return self._client._terrakio_request("PATCH", "/datasets", params = params, json = payload)
    
    @require_api_key
    def update_virtual_dataset(
        self, 
        name: str, 
        append: bool = True, 
        products: Optional[List[str]] = None,
        dates_iso8601: Optional[List[str]] = None,
        bucket: Optional[str] = None,
        path: Optional[str] = None,
        data_type: Optional[str] = None,
        no_data: Optional[Any] = None,
        i_max: Optional[int] = None,
        j_max: Optional[int] = None,
        y_size: Optional[int] = None,
        x_size: Optional[int] = None,
        proj4: Optional[str] = None,
        abstract: Optional[str] = None,
        geotransform: Optional[List[float]] = None,
        padding: Optional[Any] = None,
        input: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing dataset.
                            
        Args:
            name: Name of the dataset (required)
            append: Whether to append data or replace (default: True)
            products: List of products
            dates_iso8601: List of dates (will be automatically sorted chronologically)
            bucket: Storage bucket
            path: Storage path
            data_type: Data type
            no_data: No data value
            i_max: Maximum level
            j_max: Maximum level
            y_size: Y size
            x_size: X size
            proj4: Projection string
            abstract: Dataset abstract
            geotransform: Geotransform parameters
            padding: Padding value
            input: The input for the virtual dataset
                                
        Returns:
            Updated dataset information
                                
        Raises:
            APIError: If the API request fails
        """
        # Sort dates_iso8601 chronologically if provided
        if dates_iso8601 is not None:
            dates_iso8601 = sorted(dates_iso8601)

        params = {"append": str(append).lower()}
        payload = {"name": name}
        param_mapping = {
            "products": products,
            "dates_iso8601": dates_iso8601,
            "bucket": bucket,
            "path": path,
            "data_type": data_type,
            "no_data": no_data,
            "i_max": i_max,
            "j_max": j_max,
            "y_size": y_size,
            "x_size": x_size,
            "proj4": proj4,
            "abstract": abstract,
            "geotransform": geotransform,
            "padding": padding,
            "input": input,
        }
        for param, value in param_mapping.items():
            if value is not None:
                payload[param] = value
        return self._client._terrakio_request("PATCH", "/datasets", params = params, json = payload)


    @require_api_key
    async def _get_url_for_upload_inference_script(self, script_path: str) -> str:
        """
        Get the url for the upload of the inference script
        """
        # we have the path, and we just need to get the bucket name
        payload = {
            "script_path": script_path,
        }
        return await self._client._terrakio_request("POST", "models/update_inference_script", json = payload)
    
    @require_api_key
    async def update_virtual_dataset_inference(
        self,
        name: str,
        inference_script_path: str,
        append: bool = True,
    ):
        """
        Update the inference script for a virtual dataset.
        """
        params = {"append": str(append).lower()}
        dataset_info = await self.get_dataset(name)
        print("the current dataset info is: ", dataset_info)
        script_path = dataset_info["path"]
        product_name = dataset_info["products"][0]
        script_path = script_path + f"/{product_name}.py"
        upload_url_dict = await self._get_url_for_upload_inference_script(script_path)
        upload_url = upload_url_dict["script_upload_url"]
        try:
            with open(inference_script_path, "r", encoding="utf-8") as f:
                script_content = f.read()
                script_bytes = script_content.encode('utf-8')
                headers = {
                    "Content-Type": "text/x-python",
                    "Content-Length": str(len(script_bytes))
                }
                response = await self._client._regular_request("PUT", endpoint=upload_url, data=script_bytes, headers=headers)
        except FileNotFoundError:
            raise FileNotFoundError(f"Inference script file not found: {inference_script_path}")
        except Exception as e:
            raise Exception(f"Failed to upload inference script: {str(e)}")
    
    @require_api_key
    async def overwrite_dataset(
        self, 
        name: str, 
        products: Optional[List[str]] = None,
        dates_iso8601: Optional[List[str]] = None,
        bucket: Optional[str] = None,
        path: Optional[str] = None,
        data_type: Optional[str] = None,
        no_data: Optional[Any] = None,
        i_max: Optional[int] = None,
        j_max: Optional[int] = None,
        y_size: Optional[int] = None,
        x_size: Optional[int] = None,
        proj4: Optional[str] = None,
        abstract: Optional[str] = None,
        geotransform: Optional[List[float]] = None,
        padding: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Overwrite a dataset.
                            
        Args:
            name: Name of the dataset (required)
            products: List of products
            dates_iso8601: List of dates (will be automatically sorted chronologically)
            bucket: Storage bucket
            path: Storage path
            data_type: Data type
            no_data: No data value
            i_max: Maximum level
            j_max: Maximum level
            y_size: Y size
            x_size: X size
            proj4: Projection string
            abstract: Dataset abstract
            geotransform: Geotransform parameters
            padding: Padding value
                                
        Returns:
            Overwritten dataset information
                                
        Raises:
            CommandPermissionError: If the user does not have permission to overwrite the dataset
            DatasetNotFoundError: If the dataset is not found
            OverwriteDatasetError: If the API request fails
        """
        payload = {"name": name}
        param_mapping = {
            "products": products,
            "dates_iso8601": dates_iso8601,
            "bucket": bucket,
            "path": path,
            "data_type": data_type,
            "no_data": no_data,
            "i_max": i_max,
            "j_max": j_max,
            "y_size": y_size,
            "x_size": x_size,
            "proj4": proj4,
            "abstract": abstract,
            "geotransform": geotransform,
            "padding": padding
        }
        for param, value in param_mapping.items():
            if value is not None:
                payload[param] = value
        response, status = await self._client._terrakio_request("PUT", "/datasets", json = payload)
        if status != 200:
            if status == 403:
                raise CommandPermissionError(f"You do not have permission to overwrite dataset {name}", status_code = status)
            elif status == 404:
                raise DatasetNotFoundError(f"Dataset {name} not found", status_code = status)
            raise OverwriteDatasetError(f"Failed to overwrite dataset: {response}", status_code = status)
        return response

    @require_api_key
    def download_file_to_path(self, job_name, stage, file_name, output_path):
        if not self.mass_stats:
            from terrakio_core.mass_stats import MassStats
            if not self.url or not self.key:
                raise ConfigurationError("Mass Stats client not initialized. Make sure API URL and key are set.")
            self.mass_stats = MassStats(
                base_url=self.url,
                api_key=self.key,
                verify=self.verify,
                timeout=self.timeout
            )
        taskid = self.mass_stats.get_task_id(job_name, stage).get('task_id')
        trackinfo = self.mass_stats.track_job([taskid])
        bucket = trackinfo[taskid]['bucket']
        return self.mass_stats.download_file(job_name, bucket, file_name, output_path)