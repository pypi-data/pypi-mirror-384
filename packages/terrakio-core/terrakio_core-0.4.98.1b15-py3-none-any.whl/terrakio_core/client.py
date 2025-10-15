from typing import Optional
import logging
import warnings
from terrakio_core.config import read_config_file, DEFAULT_CONFIG_FILE
from abc import abstractmethod
import xarray as xr


class BaseClient():
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger("terrakio")
        if verbose:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)

        self.timeout = 300
        self.retry = 3

        self.session = None

        self.url = url
        self.key = api_key

        config = read_config_file(DEFAULT_CONFIG_FILE, logger=self.logger)
                
        if self.url is None:
            self.url = config.get('url')
                
        if self.key is None:
            self.key = config.get('key')

        self.token = config.get('token')
        
    #     # Apply xarray printing fix to prevent crashes with GeoDataFrames
    #     self._apply_xarray_fix()
    
    # def _apply_xarray_fix(self):
    #     """
    #     Apply xarray printing fix to prevent crashes when GeoDataFrames contain xarray objects.
    #     This fix is applied automatically when the client is initialized.
    #     """
    #     try:
            
    #         # Check if fix is already applied globally
    #         if hasattr(xr.DataArray, '_terrakio_fix_applied'):
    #             if self.verbose:
    #                 self.logger.info("xarray printing fix already applied")
    #             return
            
    #         # Store original methods for potential restoration
    #         if not hasattr(xr.DataArray, '_original_iter'):
    #             xr.DataArray._original_iter = xr.DataArray.__iter__
    #             xr.Dataset._original_iter = xr.Dataset.__iter__
            
    #         # Define safe iteration methods that prevent pandas from iterating
    #         # but leave __repr__ and __str__ untouched for normal xarray printing
    #         def safe_dataarray_iter(self):
    #             # Return infinite iterator that always yields the same safe value
    #             name = getattr(self, 'name', None) or 'unnamed'
    #             shape_str = 'x'.join(map(str, self.shape)) if hasattr(self, 'shape') else 'unknown'
    #             placeholder = f"<DataArray '{name}' {shape_str}>"
    #             while True:
    #                 yield placeholder
            
    #         def safe_dataset_iter(self):
    #             # Return infinite iterator that always yields the same safe value
    #             num_vars = len(self.data_vars) if hasattr(self, 'data_vars') else 0
    #             num_dims = len(self.dims) if hasattr(self, 'dims') else 0
    #             placeholder = f"<Dataset: {num_vars} vars, {num_dims} dims>"
    #             while True:
    #                 yield placeholder
            
    #         # Apply only the iteration fix - leave __repr__ and __str__ untouched
    #         xr.DataArray.__iter__ = safe_dataarray_iter
    #         xr.Dataset.__iter__ = safe_dataset_iter
            
    #         # Mark as applied to avoid duplicate applications
    #         xr.DataArray._terrakio_fix_applied = True
    #         xr.Dataset._terrakio_fix_applied = True
            
    #         if self.verbose:
    #             self.logger.info("xarray iteration fix applied - GeoDataFrames with xarray objects will print safely, direct xarray printing unchanged")
                
    #     except ImportError:
    #         # xarray not installed, skip the fix
    #         if self.verbose:
    #             self.logger.info("xarray not installed, skipping printing fix")
    #     except Exception as e:
    #         # Log warning but don't fail initialization
    #         warning_msg = f"Failed to apply xarray printing fix: {e}"
    #         warnings.warn(warning_msg)
    #         if self.verbose:
    #             self.logger.warning(warning_msg)
    
    # def restore_xarray_printing(self):
    #     """
    #     Restore original xarray printing behavior.
    #     Call this method if you want to see full xarray representations again.
    #     """
    #     try:
    #         import xarray as xr
            
    #         if hasattr(xr.DataArray, '_original_iter'):
    #             xr.DataArray.__iter__ = xr.DataArray._original_iter
    #             xr.Dataset.__iter__ = xr.Dataset._original_iter
                
    #             # Remove the fix markers
    #             if hasattr(xr.DataArray, '_terrakio_fix_applied'):
    #                 delattr(xr.DataArray, '_terrakio_fix_applied')
    #             if hasattr(xr.Dataset, '_terrakio_fix_applied'):
    #                 delattr(xr.Dataset, '_terrakio_fix_applied')
                
    #             if self.verbose:
    #                 self.logger.info("Original xarray iteration behavior restored")
    #         else:
    #             if self.verbose:
    #                 self.logger.info("No xarray fix to restore")
                    
    #     except ImportError:
    #         if self.verbose:
    #             self.logger.info("xarray not available")
    #     except Exception as e:
    #         warning_msg = f"Failed to restore xarray printing: {e}"
    #         warnings.warn(warning_msg)
    #         if self.verbose:
    #             self.logger.warning(warning_msg)
    
    # @abstractmethod
    # def _setup_session(self):
    #     """Initialize the HTTP session - implemented by sync/async clients"""
    #     pass