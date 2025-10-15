from typing import Dict, Any, List, Optional
from ..helper.decorators import require_token, require_api_key, require_auth

class DatasetManagement:
    def __init__(self, client):
        self._client = client


    @require_api_key
    def list_datasets(self, substring: Optional[str] = None, collection: str = "terrakio-datasets") -> List[Dict[str, Any]]:
        """
        List datasets, optionally filtering by a substring and collection.
        
        Args:
            substring: Substring to filter by (optional)
            collection: Dataset collection (default: 'terrakio-datasets')
            
        Returns:
            List of datasets matching the criteria
        """
        params = {"collection": collection}
        if substring:
            params.update({"substring": substring})
        return self._client._terrakio_request("GET", "/datasets", params = params)

    @require_api_key
    def get_dataset(self, name: str, collection: str = "terrakio-datasets") -> Dict[str, Any]:
        """
        Retrieve dataset info by dataset name.
        
        Args:
            name: The name of the dataset (required)
            collection: The dataset collection (default: 'terrakio-datasets')
            
        Returns:
            Dataset information as a dictionary
            
        Raises:
            APIError: If the API request fails
        """
        params = {"collection": collection}
        return self._client._terrakio_request("GET", f"/datasets/{name}", params = params)

    @require_api_key
    async def create_dataset(
        self, 
        name: str, 
        collection: str = "terrakio-datasets",
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
            collection: Dataset collection (default: 'terrakio-datasets')
            products: List of products
            dates_iso8601: List of dates
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
        params = {"collection": collection}
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
        return await self._client._terrakio_request("POST", "/datasets", params = params, json = payload)
    
    @require_api_key
    def update_dataset(
        self, 
        name: str, 
        append: bool = True, 
        collection: str = "terrakio-datasets",
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
            collection: Dataset collection (default: 'terrakio-datasets')
            products: List of products
            dates_iso8601: List of dates
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
        params = {"collection": collection, "append": str(append).lower()}
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
        collection: str = "terrakio-datasets",
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
            collection: Dataset collection (default: 'terrakio-datasets')
            products: List of products
            dates_iso8601: List of dates
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
        params = {"collection": collection, "append": str(append).lower()}
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
    def overwrite_dataset(
        self, 
        name: str, 
        collection: str = "terrakio-datasets",
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
            collection: Dataset collection (default: 'terrakio-datasets')
            products: List of products
            dates_iso8601: List of dates
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
            APIError: If the API request fails
        """
        params = {"collection": collection}
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
        return self._client._terrakio_request("PUT", "/datasets", params = params, json = payload)
    
    @require_api_key
    def delete_dataset(self, name: str, collection: str = "terrakio-datasets") -> Dict[str, Any]:
        """
        Delete a dataset by name.
        
        Args:
            name: The name of the dataset (required)
            collection: The dataset collection (default: 'terrakio-datasets')
            
        Returns:
            Deleted dataset information
            
        Raises:
            APIError: If the API request fails
        """
        params = {"collection": collection}
        return self._client._terrakio_request("DELETE", f"/datasets/{name}", params = params)

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

        # fetch bucket info based on job name and stage

        taskid = self.mass_stats.get_task_id(job_name, stage).get('task_id')
        trackinfo = self.mass_stats.track_job([taskid])
        bucket = trackinfo[taskid]['bucket']
        return self.mass_stats.download_file(job_name, bucket, file_name, output_path)