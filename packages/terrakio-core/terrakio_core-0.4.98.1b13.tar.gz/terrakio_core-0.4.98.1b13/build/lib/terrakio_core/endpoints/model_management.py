# Standard library imports
import ast
import json
import textwrap
import time
from io import BytesIO
from typing import Optional, Tuple
import onnxruntime as ort

# Internal imports
from ..helper.decorators import require_api_key

# Optional dependency flags
TORCH_AVAILABLE = False
SKL2ONNX_AVAILABLE = False

# PyTorch imports
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None

# Scikit-learn and ONNX conversion imports
try:
    from sklearn.base import BaseEstimator
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType
    SKL2ONNX_AVAILABLE = True
except ImportError:
    BaseEstimator = None
    convert_sklearn = None
    FloatTensorType = None

class ModelManagement:
    def __init__(self, client):
        self._client = client

    @require_api_key
    async def generate_ai_dataset(
        self,
        name: str,
        aoi_geojson: str,
        expression_x: str,
        filter_x_rate: float,
        filter_y_rate: float,
        samples: int,
        tile_size: int,
        expression_y: str = "skip",
        filter_x: str = "skip",
        filter_y: str = "skip",
        crs: str = "epsg:4326",
        res: float = 0.001,
        region: str = None,
        bucket: str = None,
        start_year: int = None,
        end_year: int = None,
    ) -> dict:
        """
        Generate an AI dataset using specified parameters.

        Args:
            name (str): Name of the dataset to generate
            aoi_geojson (str): Path to GeoJSON file containing area of interest
            expression_x (str): Expression for X variable (e.g. "MSWX.air_temperature@(year=2021, month=1)")
            filter_x (str): Filter for X variable (e.g. "MSWX.air_temperature@(year=2021, month=1)")
            filter_x_rate (float): Filter rate for X variable (e.g. 0.5)
            expression_y (str): Expression for Y variable with {year} placeholder
            filter_y (str): Filter for Y variable (e.g. "MSWX.air_temperature@(year=2021, month=1)")
            filter_y_rate (float): Filter rate for Y variable (e.g. 0.5)
            samples (int): Number of samples to generate
            tile_size (int): Size of tiles in degrees
            crs (str, optional): Coordinate reference system. Defaults to "epsg:4326"
            res (float, optional): Resolution in degrees. Defaults to 0.001
            region (str, optional): Region code. Defaults to None
            bucket (str, optional): Bucket name. Defaults to None
            start_year (int, optional): Start year for data generation. Required if end_year provided
            end_year (int, optional): End year for data generation. Required if start_year provided

        Returns:
            dict: Response from the AI dataset generation API

        Raises:
            APIError: If the API request fails
        """
        # Build config for expressions and filters
        config = {
            "expressions": [{"expr": expression_x, "res": res, "prefix": "x"}],
            "filters": []
        }

        if expression_y != "skip":
            config["expressions"].append({"expr": expression_y, "res": res, "prefix": "y"})

        if filter_x != "skip":
            config["filters"].append({"expr": filter_x, "res": res, "rate": filter_x_rate})
        if filter_y != "skip":
            config["filters"].append({"expr": filter_y, "res": res, "rate": filter_y_rate})

        # Replace year placeholders if start_year is provided
        if start_year is not None:
            expression_x = expression_x.replace("{year}", str(start_year))
            if expression_y != "skip":
                expression_y = expression_y.replace("{year}", str(start_year))
            if filter_x != "skip":
                filter_x = filter_x.replace("{year}", str(start_year))
            if filter_y != "skip":
                filter_y = filter_y.replace("{year}", str(start_year))

        # Load AOI GeoJSON
        with open(aoi_geojson, 'r') as f:
            aoi_data = json.load(f)

        task_response = await self._client.mass_stats.random_sample(
            name=name,
            config=config,
            aoi=aoi_data,
            samples=samples,
            year_range=[start_year, end_year],
            crs=crs,
            tile_size=tile_size,
            res=res,
            region=region,
            output="netcdf",
            server=self._client.url,
            bucket=bucket,
            overwrite=True
        )
        task_id = task_response["task_id"]

        while True:
            result = await self._client.mass_stats.track_job(ids=[task_id])
            status = result[task_id]['status']
            completed = result[task_id].get('completed', 0)
            total = result[task_id].get('total', 1)
            
            progress = completed / total if total > 0 else 0
            bar_length = 50
            filled_length = int(bar_length * progress)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            percentage = progress * 100
            
            self._client.logger.info(f"Job status: {status} [{bar}] {percentage:.1f}% ({completed}/{total})")   

            if status == "Completed":
                self._client.logger.info("Job completed successfully!")
                break
            elif status == "Error":
                self._client.logger.info("Job encountered an error")
                raise Exception(f"Job {task_id} encountered an error")
            
            time.sleep(5)

        task_id = await self._client.mass_stats.start_job(task_id)
        return task_id
    
    @require_api_key
    async def _get_url_for_upload_model_and_script(self, expression: str, model_name: str, script_name: str) -> str:
        """
        Get the url for the upload of the model
        Args:
            expression: The expression to use for the upload(for deciding which bucket to upload to)
            model_name: The name of the model to upload
            script_name: The name of the script to upload
        Returns:
            The url for the upload of the model
        """
        payload = {
            "model_name": model_name,
            "expression": expression,
            "script_name": script_name
        }
        return await self._client._terrakio_request("POST", "models/upload", json=payload)

    async def _upload_model_to_url(self, upload_model_url: str, model: bytes):
        """
        Upload a model to a given URL.
        Args:
            model_url: The url to upload the model to
            model: The model to upload

        Returns:
            The response from the server
        """
        headers = {
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(model))
        }
        response = await self._client._regular_request("PUT", endpoint = upload_model_url, data=model, headers=headers)
        return response
    
    @require_api_key
    async def _upload_script_to_url(self, upload_script_url: str, script_content: str):
        """
            Upload the generated script to the url
            Args:
                url: Url for the upload of the script
                script_content: Content of the script
            returns:
                None
        """
        script_bytes = script_content.encode('utf-8')
        headers = {
            "Content-Type": "text/x-python",
            "Content-Length": str(len(script_bytes))
        }
        response = await self._client._regular_request("PUT", endpoint=upload_script_url, data=script_bytes, headers=headers)
        return response

    @require_api_key
    async def _upload_model_and_script(self, model, model_name: str, script_name: str, input_expression: str, input_shape: Tuple[int, ...] = None, processing_script_path: Optional[str] = None, model_type: Optional[str] = None):
        """
        Upload a model and script to the bucket
        Args:
            model: The model object (PyTorch model or scikit-learn model)
            model_name: Name for the model (without extension)
            script_name: Name for the script (without extension)
            input_expression: Input expression for the dataset
            input_shape: Shape of input data for ONNX conversion (required for PyTorch models)
            processing_script_path: Path to the processing script, if not provided, no processing will be done
            model_type: The type of the model we want to upload
        Raises:
            APIError: If the API request fails
            ValueError: If model type is not supported or input_shape is missing for PyTorch models

        Returns:
            bucket_name: Name of the bucket where the model is stored
        """
        response = await self._get_url_for_upload_model_and_script(expression = input_expression, model_name = model_name, script_name = script_name)
        model_url, script_url, bucket_name = response.get("model_upload_url"), response.get("script_upload_url"), response.get("bucket_name")
        if not model_url or not script_url:
            raise ValueError("No url returned from the server for the upload process")
        try:
            model_in_onnx_bytes, model_type = self._convert_model_to_onnx(model = model, input_shape = input_shape, model_type = model_type)
            if model_type == "neural_network":
                script_content = await self._generate_cnn_script(bucket_name = bucket_name, virtual_dataset_name = model_name, virtual_product_name = script_name, processing_script_path = processing_script_path)
            elif model_type == "random_forest":
                script_content = await self._generate_random_forest_script(bucket_name = bucket_name, virtual_dataset_name = model_name, virtual_product_name = script_name, processing_script_path = processing_script_path)
            else:
                raise ValueError(f"Unsupported model type: {model_type}. Supported types: neural_network, random_forest")
            script_upload_response = await self._upload_script_to_url( upload_script_url = script_url, script_content = script_content)
            if script_upload_response.status not in [200, 201, 204]:
                self._client.logger.error(f"Script upload error: {script_upload_response.text()}")
                raise Exception(f"Failed to upload script: {script_upload_response.text()}")
            model_upload_response = await self._upload_model_to_url(upload_model_url = model_url, model = model_in_onnx_bytes)
            if model_upload_response.status not in [200, 201, 204]:
                self._client.logger.error(f"Model upload error: {model_upload_response.text()}")
                raise Exception(f"Failed to upload model: {model_upload_response.text()}")
        except Exception as e:
            raise Exception(f"Error uploading model: {e}")
        self._client.logger.info(f"Model and Script uploaded successfully to {model_url}")
        return bucket_name

    @require_api_key
    async def upload_and_deploy_model(self, model, virtual_dataset_name: str, virtual_product_name: str, input_expression: str, dates_iso8601: list, input_shape: Tuple[int, ...] = None, processing_script_path: Optional[str] = None, model_type: Optional[str] = None):
        """
        Upload a model to the bucket and deploy it.
        Args:
            model: The model object (PyTorch model or scikit-learn model)
            virtual_dataset_name: Name for the virtual dataset (without extension)
            virtual_product_name: Product name for the inference
            input_expression: Input expression for the dataset
            dates_iso8601: List of dates in ISO8601 format
            input_shape: Shape of input data for ONNX conversion (required for PyTorch models)
            processing_script_path: Path to the processing script, if not provided, no processing will be done
            model_type: The type of the model we want to upload

        Raises:
            APIError: If the API request fails
            ValueError: If model type is not supported or input_shape is missing for PyTorch models
            ImportError: If required libraries (torch or skl2onnx) are not installed

        Returns:
            None
        """
        bucket_name = await self._upload_model_and_script(model=model, model_name=virtual_dataset_name, script_name= virtual_product_name, input_shape=input_shape, input_expression=input_expression, processing_script_path=processing_script_path, model_type= model_type)
        user_info = await self._client.auth.get_user_info()
        uid = user_info["uid"]
        await self._client.datasets.create_dataset(
            name=virtual_dataset_name,
            collection="terrakio-datasets",
            products=[virtual_product_name],
            path=f"gs://{bucket_name}/{uid}/virtual_datasets/{virtual_dataset_name}/inference_scripts",
            input=input_expression,
            dates_iso8601=dates_iso8601,
            padding=0
        )
    
    @require_api_key
    async def _generate_random_forest_script(self, bucket_name: str, virtual_dataset_name: str, virtual_product_name: str, processing_script_path: Optional[str] = None) -> str:
        """
        Generate Python inference script for the Random Forest model.
        
        Args:
            bucket_name: Name of the bucket where the model is stored
            virtual_dataset_name: Name of the virtual dataset and the model
            virtual_product_name: Name of the virtual product
            processing_script_path: Path to the processing script, if not provided, no processing will be done
            
        Returns:
            str: Generated Python script content
        """
        user_info = await self._client.auth.get_user_info()
        uid = user_info["uid"]
        preprocessing_code, postprocessing_code = None, None

        if processing_script_path:
            try:
                preprocessing_code, postprocessing_code = self._parse_processing_script(processing_script_path)
                if preprocessing_code:
                    self._client.logger.info(f"Using custom preprocessing from: {processing_script_path}")
                if postprocessing_code:
                    self._client.logger.info(f"Using custom postprocessing from: {processing_script_path}")
                if not preprocessing_code and not postprocessing_code:
                    self._client.logger.warning(f"No preprocessing or postprocessing functions found in {processing_script_path}")
                    self._client.logger.info("Deployment will continue without custom processing")
            except Exception as e:
                raise ValueError(f"Failed to load processing script: {str(e)}")     
   
        preprocessing_section = ""
        if preprocessing_code and preprocessing_code.strip():
            clean_preprocessing = textwrap.dedent(preprocessing_code)
            preprocessing_section = textwrap.indent(clean_preprocessing, '    ')
        
        postprocessing_section = ""
        if postprocessing_code and postprocessing_code.strip():
            clean_postprocessing = textwrap.dedent(postprocessing_code)
            postprocessing_section = textwrap.indent(clean_postprocessing, '    ')

        script_lines = [
            "import logging",
            "from io import BytesIO",
            "import numpy as np",
            "import pandas as pd",
            "import xarray as xr",
            "from google.cloud import storage",
            "from onnxruntime import InferenceSession",
            "from typing import Tuple",
            "",
            "logging.basicConfig(",
            "    level=logging.INFO",
            ")",
            "",
        ]
        
        if preprocessing_section:
            script_lines.extend([
                "def validate_preprocessing_output(data_arrays):",
                "    \"\"\"",
                "    Validate preprocessing output coordinates and data type.",
                "    ",
                "    Args:",
                "        data_arrays: List of xarray DataArrays from preprocessing",
                "        ",
                "    Returns:",
                "        str: Validation signature symbol",
                "        ",
                "    Raises:",
                "        ValueError: If validation fails",
                "    \"\"\"",
                "    import numpy as np",
                "    ",
                "    if not data_arrays:",
                "        raise ValueError(\"No data arrays provided from preprocessing\")",
                "    ",
                "    reference_shape = None",
                "    ",
                "    for i, data_array in enumerate(data_arrays):",
                "        # Check if it's an xarray DataArray",
                "        if not hasattr(data_array, 'dims') or not hasattr(data_array, 'coords'):",
                "            raise ValueError(f\"Channel {i+1} is not a valid xarray DataArray\")",
                "        ",
                "        # Check coordinates",
                "        if 'time' not in data_array.coords:",
                "            raise ValueError(f\"Channel {i+1} missing time coordinate\")",
                "        ",
                "        spatial_dims = [dim for dim in data_array.dims if dim != 'time']",
                "        if len(spatial_dims) != 2:",
                "            raise ValueError(f\"Channel {i+1} must have exactly 2 spatial dimensions, got {spatial_dims}\")",
                "        ",
                "        for dim in spatial_dims:",
                "            if dim not in data_array.coords:",
                "                raise ValueError(f\"Channel {i+1} missing coordinate: {dim}\")",
                "        ",
                "        # Check shape consistency",
                "        shape = data_array.shape",
                "        if reference_shape is None:",
                "            reference_shape = shape",
                "        else:",
                "            if shape != reference_shape:",
                "                raise ValueError(f\"Channel {i+1} shape {shape} doesn't match reference {reference_shape}\")",
                "    ",
                "    # Generate validation signature",
                "    signature_components = [",
                "        f\"CH{len(data_arrays)}\",  # Channel count",
                "        f\"T{reference_shape[0]}\",  # Time dimension",
                "        f\"S{reference_shape[1]}x{reference_shape[2]}\",  # Spatial dimensions",
                "        f\"DT{data_arrays[0].values.dtype}\",  # Data type",
                "    ]",
                "    ",
                "    signature = \"★PRE_\" + \"_\".join(signature_components) + \"★\"",
                "    ",
                "    return signature",
                "",
            ])
        
        if postprocessing_section:
            script_lines.extend([
                "def validate_postprocessing_output(result_array):",
                "    \"\"\"",
                "    Validate postprocessing output coordinates and data type.",
                "    ",
                "    Args:",
                "        result_array: xarray DataArray from postprocessing",
                "        ",
                "    Returns:",
                "        str: Validation signature symbol",
                "        ",
                "    Raises:",
                "        ValueError: If validation fails",
                "    \"\"\"",
                "    import numpy as np",
                "    ",
                "    # Check if it's an xarray DataArray",
                "    if not hasattr(result_array, 'dims') or not hasattr(result_array, 'coords'):",
                "        raise ValueError(\"Postprocessing output is not a valid xarray DataArray\")",
                "    ",
                "    # Check required coordinates",
                "    if 'time' not in result_array.coords:",
                "        raise ValueError(\"Missing time coordinate\")",
                "    ",
                "    spatial_dims = [dim for dim in result_array.dims if dim != 'time']",
                "    if len(spatial_dims) != 2:",
                "        raise ValueError(f\"Expected 2 spatial dimensions, got {len(spatial_dims)}: {spatial_dims}\")",
                "    ",
                "    for dim in spatial_dims:",
                "        if dim not in result_array.coords:",
                "            raise ValueError(f\"Missing spatial coordinate: {dim}\")",
                "    ",
                "    # Check shape",
                "    shape = result_array.shape",
                "    ",
                "    # Generate validation signature",
                "    signature_components = [",
                "        f\"T{shape[0]}\",  # Time dimension",
                "        f\"S{shape[1]}x{shape[2]}\",  # Spatial dimensions",
                "        f\"DT{result_array.values.dtype}\",  # Data type",
                "    ]",
                "    ",
                "    signature = \"★POST_\" + \"_\".join(signature_components) + \"★\"",
                "    ",
                "    return signature",
                "",
            ])
        
        if preprocessing_section:
            script_lines.extend([
                "def preprocessing(array: Tuple[xr.DataArray, ...]) -> Tuple[xr.DataArray, ...]:",
                preprocessing_section,
                "",
            ])
        
        if postprocessing_section:
            script_lines.extend([
                "def postprocessing(array: xr.DataArray) -> xr.DataArray:",
                postprocessing_section,
                "",
            ])
        
        script_lines.extend([
            "def get_model():",
            f"    logging.info(\"Loading Random Forest model for {virtual_dataset_name}...\")",
            "",
            "    client = storage.Client()",
            f"    bucket = client.get_bucket('{bucket_name}')",
            f"    blob = bucket.blob('{uid}/virtual_datasets/{virtual_dataset_name}/{virtual_dataset_name}.onnx')",
            "",
            "    model = BytesIO()",
            "    blob.download_to_file(model)",
            "    model.seek(0)",
            "",
            "    session = InferenceSession(model.read(), providers=[\"CPUExecutionProvider\"])",
            "    return session",
            "",
            f"def {virtual_product_name}(*bands, model):",
            "    logging.info(\"Start preparing Random Forest data\")",
            "    data_arrays = list(bands)",
            "    ",
            "    if not data_arrays:",
            "        raise ValueError(\"No bands provided\")",
            "    ",
        ])
        
        if preprocessing_section:
            script_lines.extend([
                "    # Apply preprocessing",
                "    data_arrays = preprocessing(tuple(data_arrays))",
                "    data_arrays = list(data_arrays)  # Convert back to list for processing",
                "    ",
                "    # Validate preprocessing output",
                "    preprocessing_signature = validate_preprocessing_output(data_arrays)",
                "    ",
            ])
        
        script_lines.extend([
            "    reference_array = data_arrays[0]",
            "    original_shape = reference_array.shape",
            "    ",
            "    if 'time' in reference_array.dims:",
            "        time_coords = reference_array.coords['time']",
            "        if len(time_coords) == 1:",
            "            output_timestamp = time_coords[0]",
            "        else:",
            "            years = [pd.to_datetime(t).year for t in time_coords.values]",
            "            unique_years = set(years)",
            "            ",
            "            if len(unique_years) == 1:",
            "                year = list(unique_years)[0]",
            "                output_timestamp = pd.Timestamp(f\"{year}-01-01\")",
            "            else:",
            "                latest_year = max(unique_years)",
            "                output_timestamp = pd.Timestamp(f\"{latest_year}-01-01\")",
            "    else:",
            "        output_timestamp = pd.Timestamp(\"1970-01-01\")",
            "",
            "    averaged_bands = []",
            "    for data_array in data_arrays:",
            "        if 'time' in data_array.dims:",
            "            averaged_band = np.mean(data_array.values, axis=0)",
            "        else:",
            "            averaged_band = data_array.values",
            "",
            "        flattened_band = averaged_band.reshape(-1, 1)",
            "        averaged_bands.append(flattened_band)",
            "",
            "    input_data = np.hstack(averaged_bands)",
            "",
            "    output = model.run(None, {\"float_input\": input_data.astype(np.float32)})[0]",
            "",
            "    if len(original_shape) >= 3:",
            "        spatial_shape = original_shape[1:]",
            "    else:",
            "        spatial_shape = original_shape",
            "",
            "    output_reshaped = output.reshape(spatial_shape)",
            "",
            "    output_with_time = np.expand_dims(output_reshaped, axis=0)",
            "",
            "    if 'time' in reference_array.dims:",
            "        spatial_dims = [dim for dim in reference_array.dims if dim != 'time']",
            "        spatial_coords = {dim: reference_array.coords[dim] for dim in spatial_dims if dim in reference_array.coords}",
            "    else:",
            "        spatial_dims = list(reference_array.dims)",
            "        spatial_coords = dict(reference_array.coords)",
            "",
            "    result = xr.DataArray(",
            "        data=output_with_time.astype(np.float32),",
            "        dims=['time'] + list(spatial_dims),",
            "        coords={",
            "            'time': [output_timestamp.values],",
            "            'y': spatial_coords['y'].values,",
            "            'x': spatial_coords['x'].values",
            "        },",
            "        attrs={",
            "            'description': 'Random Forest model prediction',",
            "        }",
            "    )",
        ])
        
        if postprocessing_section:
            script_lines.extend([
                "    # Apply postprocessing",
                "    result = postprocessing(result)",
                "    ",
                "    # Validate postprocessing output",
                "    postprocessing_signature = validate_postprocessing_output(result)",
                "    ",
            ])
        
        script_lines.append("    return result")
        
        return "\n".join(script_lines)

    @require_api_key
    async def _generate_cnn_script(self, bucket_name: str, virtual_dataset_name: str, virtual_product_name: str, processing_script_path: Optional[str] = None) -> str:
        """
        Generate Python inference script for CNN model with time-stacked bands.
        
        Args:
            bucket_name: Name of the bucket where the model is stored
            virtual_dataset_name: Name of the virtual dataset and the model
            virtual_product_name: Name of the virtual product
            processing_script_path: Path to the processing script, if not provided, no processing will be done
        Returns:
            str: Generated Python script content
        """
        user_info = await self._client.auth.get_user_info()
        uid = user_info["uid"]
        preprocessing_code, postprocessing_code = None, None

        if processing_script_path:
            try:
                preprocessing_code, postprocessing_code = self._parse_processing_script(processing_script_path)
                if preprocessing_code:
                    self._client.logger.info(f"Using custom preprocessing from: {processing_script_path}")
                if postprocessing_code:
                    self._client.logger.info(f"Using custom postprocessing from: {processing_script_path}")
                if not preprocessing_code and not postprocessing_code:
                    self._client.logger.warning(f"No preprocessing or postprocessing functions found in {processing_script_path}")
                    self._client.logger.info("Deployment will continue without custom processing")
            except Exception as e:
                raise ValueError(f"Failed to load processing script: {str(e)}")
            
        preprocessing_section = ""
        if preprocessing_code and preprocessing_code.strip():
            clean_preprocessing = textwrap.dedent(preprocessing_code)
            preprocessing_section = textwrap.indent(clean_preprocessing, '    ')
        
        postprocessing_section = ""
        if postprocessing_code and postprocessing_code.strip():
            clean_postprocessing = textwrap.dedent(postprocessing_code)
            postprocessing_section = textwrap.indent(clean_postprocessing, '    ')

        script_lines = [
            "import logging",
            "from io import BytesIO",
            "import numpy as np",
            "import pandas as pd",
            "import xarray as xr",
            "from google.cloud import storage",
            "from onnxruntime import InferenceSession",
            "from typing import Tuple",
            "",
            "logging.basicConfig(",
            "    level=logging.INFO",
            ")",
            "",
        ]
        
        if preprocessing_section:
            script_lines.extend([
                "def validate_preprocessing_output(data_arrays):",
                "    \"\"\"",
                "    Validate preprocessing output coordinates and data type.",
                "    ",
                "    Args:",
                "        data_arrays: List of xarray DataArrays from preprocessing",
                "        ",
                "    Returns:",
                "        str: Validation signature symbol",
                "        ",
                "    Raises:",
                "        ValueError: If validation fails",
                "    \"\"\"",
                "    import numpy as np",
                "    ",
                "    if not data_arrays:",
                "        raise ValueError(\"No data arrays provided from preprocessing\")",
                "    ",
                "    reference_shape = None",
                "    ",
                "    for i, data_array in enumerate(data_arrays):",
                "        # Check if it's an xarray DataArray",
                "        if not hasattr(data_array, 'dims') or not hasattr(data_array, 'coords'):",
                "            raise ValueError(f\"Channel {i+1} is not a valid xarray DataArray\")",
                "        ",
                "        # Check coordinates",
                "        if 'time' not in data_array.coords:",
                "            raise ValueError(f\"Channel {i+1} missing time coordinate\")",
                "        ",
                "        spatial_dims = [dim for dim in data_array.dims if dim != 'time']",
                "        if len(spatial_dims) != 2:",
                "            raise ValueError(f\"Channel {i+1} must have exactly 2 spatial dimensions, got {spatial_dims}\")",
                "        ",
                "        for dim in spatial_dims:",
                "            if dim not in data_array.coords:",
                "                raise ValueError(f\"Channel {i+1} missing coordinate: {dim}\")",
                "        ",
                "        # Check shape consistency",
                "        shape = data_array.shape",
                "        if reference_shape is None:",
                "            reference_shape = shape",
                "        else:",
                "            if shape != reference_shape:",
                "                raise ValueError(f\"Channel {i+1} shape {shape} doesn't match reference {reference_shape}\")",
                "    ",
                "    # Generate validation signature",
                "    signature_components = [",
                "        f\"CH{len(data_arrays)}\",  # Channel count",
                "        f\"T{reference_shape[0]}\",  # Time dimension",
                "        f\"S{reference_shape[1]}x{reference_shape[2]}\",  # Spatial dimensions",
                "        f\"DT{data_arrays[0].values.dtype}\",  # Data type",
                "    ]",
                "    ",
                "    signature = \"★PRE_\" + \"_\".join(signature_components) + \"★\"",
                "    ",
                "    return signature",
                "",
            ])
        
        if postprocessing_section:
            script_lines.extend([
                "def validate_postprocessing_output(result_array):",
                "    \"\"\"",
                "    Validate postprocessing output coordinates and data type.",
                "    ",
                "    Args:",
                "        result_array: xarray DataArray from postprocessing",
                "        ",
                "    Returns:",
                "        str: Validation signature symbol",
                "        ",
                "    Raises:",
                "        ValueError: If validation fails",
                "    \"\"\"",
                "    import numpy as np",
                "    ",
                "    # Check if it's an xarray DataArray",
                "    if not hasattr(result_array, 'dims') or not hasattr(result_array, 'coords'):",
                "        raise ValueError(\"Postprocessing output is not a valid xarray DataArray\")",
                "    ",
                "    # Check required coordinates",
                "    if 'time' not in result_array.coords:",
                "        raise ValueError(\"Missing time coordinate\")",
                "    ",
                "    spatial_dims = [dim for dim in result_array.dims if dim != 'time']",
                "    if len(spatial_dims) != 2:",
                "        raise ValueError(f\"Expected 2 spatial dimensions, got {len(spatial_dims)}: {spatial_dims}\")",
                "    ",
                "    for dim in spatial_dims:",
                "        if dim not in result_array.coords:",
                "            raise ValueError(f\"Missing spatial coordinate: {dim}\")",
                "    ",
                "    # Check shape",
                "    shape = result_array.shape",
                "    ",
                "    # Generate validation signature",
                "    signature_components = [",
                "        f\"T{shape[0]}\",  # Time dimension",
                "        f\"S{shape[1]}x{shape[2]}\",  # Spatial dimensions",
                "        f\"DT{result_array.values.dtype}\",  # Data type",
                "    ]",
                "    ",
                "    signature = \"★POST_\" + \"_\".join(signature_components) + \"★\"",
                "    ",
                "    return signature",
                "",
            ])
        
        if preprocessing_section:
            script_lines.extend([
                "def preprocessing(array: Tuple[xr.DataArray, ...]) -> Tuple[xr.DataArray, ...]:",
                preprocessing_section,
                "",
            ])
        
        if postprocessing_section:
            script_lines.extend([
                "def postprocessing(array: xr.DataArray) -> xr.DataArray:",
                postprocessing_section,
                "",
            ])
        
        script_lines.extend([
            "def get_model():",
            f"    logging.info(\"Loading CNN model for {virtual_dataset_name}...\")",
            "",
            "    client = storage.Client()",
            f"    bucket = client.get_bucket('{bucket_name}')",
            f"    blob = bucket.blob('{uid}/virtual_datasets/{virtual_dataset_name}/{virtual_dataset_name}.onnx')",
            "",
            "    model = BytesIO()",
            "    blob.download_to_file(model)",
            "    model.seek(0)",
            "",
            "    session = InferenceSession(model.read(), providers=[\"CPUExecutionProvider\"])",
            "    return session",
            "",
            f"def {virtual_product_name}(*bands, model):",
            "    logging.info(\"Start preparing CNN data with time-stacked bands\")",
            "    data_arrays = list(bands)",
            "    ",
            "    if not data_arrays:",
            "        raise ValueError(\"No bands provided\")",
            "    ",
        ])
        
        if preprocessing_section:
            script_lines.extend([
                "    # Apply preprocessing",
                "    data_arrays = preprocessing(tuple(data_arrays))",
                "    data_arrays = list(data_arrays)  # Convert back to list for processing",
                "    ",
                "    # Validate preprocessing output",
                "    preprocessing_signature = validate_preprocessing_output(data_arrays)",
                "    ",
            ])
        
        script_lines.extend([
            "    reference_array = data_arrays[0]",
            "    original_shape = reference_array.shape",
            "    ",
            "    # Get time coordinates - all bands should have the same time dimension",
            "    if 'time' not in reference_array.dims:",
            "        raise ValueError(\"Time dimension is required for CNN processing\")",
            "    ",
            "    time_coords = reference_array.coords['time']",
            "    num_timestamps = len(time_coords)",
            "    ",
            "    # Get spatial dimensions",
            "    spatial_dims = [dim for dim in reference_array.dims if dim != 'time']",
            "    height = reference_array.sizes[spatial_dims[0]]  # assuming first spatial dim is height",
            "    width = reference_array.sizes[spatial_dims[1]]   # assuming second spatial dim is width",
            "    ",
            "    # Stack bands across time dimension",
            "    # Result will be: (num_bands * num_timestamps, height, width)",
            "    stacked_channels = []",
            "    ",
            "    for band_idx, data_array in enumerate(data_arrays):",
            "        # Ensure consistent time coordinates across bands",
            "        if not np.array_equal(data_array.coords['time'].values, time_coords.values):",
            "            data_array = data_array.sel(time=time_coords, method='nearest')",
            "        ",
            "        # Extract values and ensure proper ordering (time, height, width)",
            "        band_values = data_array.values",
            "        if band_values.ndim == 3:",
            "            # Reorder dimensions if needed to ensure (time, height, width)",
            "            time_dim_idx = data_array.dims.index('time')",
            "            if time_dim_idx != 0:",
            "                axes_order = [time_dim_idx] + [i for i in range(len(data_array.dims)) if i != time_dim_idx]",
            "                band_values = np.transpose(band_values, axes_order)",
            "        ",
            "        # Add each timestamp of this band to the channel stack",
            "        for t in range(num_timestamps):",
            "            stacked_channels.append(band_values[t])",
            "    ",
            "    # Stack all channels: (num_bands * num_timestamps, height, width)",
            "    input_channels = np.stack(stacked_channels, axis=0)",
            "    total_channels = len(data_arrays) * num_timestamps",
            "    ",
            "    # Add batch dimension: (1, num_channels, height, width)",
            "    input_data = np.expand_dims(input_channels, axis=0).astype(np.float32)",
            "    ",
            "    # Run inference",
            "    output = model.run(None, {\"float_input\": input_data})[0]",
            "    ",
            "    # Handle multi-class CNN output properly",
            "    if output.ndim == 4:",
            "        if output.shape[1] == 1:",
            "            # Single class output (regression or binary classification)",
            "            output_2d = output[0, 0]",
            "        else:",
            "            # Multi-class output - convert logits/probabilities to class predictions",
            "            output_classes = np.argmax(output, axis=1)  # Shape: (1, height, width)",
            "            output_2d = output_classes[0]  # Shape: (height, width)",
            "            ",
            "            # Apply class merging: merge class 6 into class 3",
            "            output_2d = np.where(output_2d == 6, 3, output_2d)",
            "    elif output.ndim == 3:",
            "        # Remove batch dimension",
            "        output_2d = output[0]",
            "    else:",
            "        # Handle other cases",
            "        output_2d = np.squeeze(output)",
            "        if output_2d.ndim != 2:",
            "            raise ValueError(f\"Unexpected output shape after processing: {output_2d.shape}\")",
            "    ",
            "    # Ensure output is 2D",
            "    if output_2d.ndim != 2:",
            "        raise ValueError(f\"Final output must be 2D, got shape: {output_2d.shape}\")",
            "    ",
            "    # Determine output timestamp (use the latest timestamp)",
            "    output_timestamp = time_coords[-1]",
            "    ",
            "    # Get spatial coordinates from reference array",
            "    spatial_coords = {dim: reference_array.coords[dim] for dim in spatial_dims}",
            "    ",
            "    # Create output DataArray with appropriate data type",
            "    # Use int32 for classification, float32 for regression",
            "    is_multiclass = output.ndim == 4 and output.shape[1] > 1",
            "    if is_multiclass:",
            "        # Multi-class classification - use integer type",
            "        output_dtype = np.int32",
            "    else:",
            "        # Single output - use float type",
            "        output_dtype = np.float32",
            "    ",
            "    result = xr.DataArray(",
            "        data=np.expand_dims(output_2d.astype(output_dtype), axis=0),",
            "        dims=['time'] + spatial_dims,",
            "        coords={",
            "            'time': [output_timestamp.values],",
            "            spatial_dims[0]: spatial_coords[spatial_dims[0]].values,",
            "            spatial_dims[1]: spatial_coords[spatial_dims[1]].values",
            "        },",
            "        attrs={",
            "            'description': 'CNN model prediction',",
            "        }",
            "    )",
        ])
        
        if postprocessing_section:
            script_lines.extend([
                "    # Apply postprocessing",
                "    result = postprocessing(result)",
                "    ",
                "    # Validate postprocessing output",
                "    postprocessing_signature = validate_postprocessing_output(result)",
                "    ",
            ])
        
        script_lines.append("    return result")
        
        return "\n".join(script_lines)

    def _parse_processing_script(self, script_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse a Python file and extract preprocessing and postprocessing function bodies.
        
        Args:
            script_path: Path to the Python file containing processing functions
            
        Returns:
            Tuple of (preprocessing_code, postprocessing_code) where each can be None
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Processing script not found: {script_path}")
        except Exception as e:
            raise ValueError(f"Error reading processing script: {e}")
        
        if not script_content.strip():
            self._client.logger.info(f"Processing script {script_path} is empty")
            return None, None
        
        try:
            tree = ast.parse(script_content)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in processing script: {e}")
        
        preprocessing_code = None
        postprocessing_code = None
        
        function_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
                if node.name == 'preprocessing':
                    preprocessing_code = self._extract_function_body(script_content, node)
                elif node.name == 'postprocessing':
                    postprocessing_code = self._extract_function_body(script_content, node)
        
        if not function_names:
            self._client.logger.warning(f"No functions found in processing script: {script_path}")
        else:
            found_functions = [name for name in function_names if name in ['preprocessing', 'postprocessing']]
            if found_functions:
                self._client.logger.info(f"Found processing functions: {found_functions}")
            else:
                self._client.logger.warning(f"No 'preprocessing' or 'postprocessing' functions found in {script_path}. "
                                          f"Available functions: {function_names}")
        
        return preprocessing_code, postprocessing_code

    def _extract_function_body(self, script_content: str, func_node: ast.FunctionDef) -> str:
        """Extract the body of a function from the script content."""
        lines = script_content.split('\n')
        
        start_line = func_node.lineno - 1
        end_line = func_node.end_lineno - 1 if hasattr(func_node, 'end_lineno') else len(lines) - 1
        
        body_lines = []
        for i in range(start_line + 1, end_line + 1):
            if i < len(lines):
                body_lines.append(lines[i])
        
        if not body_lines:
            return ""
        
        body_text = '\n'.join(body_lines)
        cleaned_body = textwrap.dedent(body_text).strip()
        
        if not cleaned_body or cleaned_body in ['pass', 'return', 'return None']:
            return ""
        
        return cleaned_body
    
    def _convert_model_to_onnx(self, model, input_shape: Tuple[int, ...] = None, model_type: Optional[str] = None) -> bytes:
        """
        Convert a model to ONNX format and return as bytes.
        
        Args:
            model: The model object (PyTorch or scikit-learn)
            input_shape: Shape of input data
            model_type: Type of model (neural_network, random_forest), only used for onnx model generation
        Returns:
            bytes: ONNX model as bytes
            
        Raises:
            ValueError: If model type is not supported
            ImportError: If required libraries are not installed
        """
        if isinstance(model, torch.nn.Module):
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch is not installed. Please install it with: pip install torch")
            return self._convert_pytorch_to_onnx(model, input_shape), "neural_network"
        elif isinstance(model, BaseEstimator):
            if not SKL2ONNX_AVAILABLE:
                raise ImportError("skl2onnx is not installed. Please install it with: pip install skl2onnx")
            return self._convert_sklearn_to_onnx(model, input_shape), "random_forest"
        elif isinstance(model, ort.InferenceSession):
            if model_type is None:
                raise ValueError(
                    "For ONNX InferenceSession models, you must specify the 'model_type' parameter. Currently 'nerual network' and 'random forest' are supported."
                    "Example: model_type='random forest' or model_type='neural network'"
                )
            return model.SerializeToString(), model_type
        else:
            model_type = type(model).__name__
            raise ValueError(f"Unsupported model type: {model_type}. Supported types: PyTorch nn.Module, sklearn BaseEstimator")

    def _convert_pytorch_to_onnx(self, model, input_shape: Tuple[int, ...]) -> bytes:
        try:
            model.eval()
            dummy_input = torch.randn(input_shape)
            onnx_buffer = BytesIO()
            
            if len(input_shape) == 4:
                dynamic_axes = {
                    'float_input': {
                        0: 'batch_size',
                        2: 'height',
                        3: 'width'
                    }
                }
                
            elif len(input_shape) == 5:
                dynamic_axes = {
                    'float_input': {
                        0: 'batch_size',
                        3: 'height',
                        4: 'width'
                    }
                }
                
            else:
                dynamic_axes = {
                    'float_input': {
                        0: 'batch_size'
                    }
                }
            
            torch.onnx.export(
                model,
                dummy_input,
                onnx_buffer,
                input_names=['float_input'],
                dynamic_axes=dynamic_axes
            )
            
            return onnx_buffer.getvalue()
        except Exception as e:
            raise ValueError(f"Failed to convert PyTorch model to ONNX: {str(e)}")

    def _convert_sklearn_to_onnx(self, model, input_shape: Tuple[int, ...]) -> bytes:
        """
        Convert scikit-learn model(assume it is a random forest model) to ONNX format.
        
        Args:
            model: The scikit-learn model object
            input_shape: Shape of input data (required)
            
        Returns:
            bytes: ONNX model as bytes
            
        Raises:
            ValueError: If conversion fails
        """
        self._client.logger.info(f"Converting random forest model to ONNX...")
        
        try:
            initial_type = [('float_input', FloatTensorType(input_shape))]
            onnx_model = convert_sklearn(model, initial_types=initial_type)
            return onnx_model.SerializeToString()
        except Exception as e:
            raise ValueError(f"Failed to convert scikit-learn model to ONNX: {str(e)}")

    @require_api_key
    def train_model(
        self, 
        model_name: str, 
        training_dataset: str, 
        task_type: str, 
        model_category: str, 
        architecture: str, 
        region: str, 
        hyperparameters: dict = None
    ) -> dict:
        """
        Train a model using the external model training API.
        
        Args:
            model_name (str): The name of the model to train.
            training_dataset (str): The training dataset identifier.
            task_type (str): The type of ML task (e.g., regression, classification).
            model_category (str): The category of model (e.g., random_forest).
            architecture (str): The model architecture.
            region (str): The region identifier.
            hyperparameters (dict, optional): Additional hyperparameters for training.
            
        Returns:
            dict: The response from the model training API.
            
        Raises:
            APIError: If the API request fails
        """
        payload = {
            "model_name": model_name,
            "training_dataset": training_dataset,
            "task_type": task_type,
            "model_category": model_category,
            "architecture": architecture,
            "region": region,
            "hyperparameters": hyperparameters
        }
        return self._client._terrakio_request("POST", "/train_model", json=payload)