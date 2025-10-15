import pandas as pd
import geopandas as gpd
import xarray as xr
import numpy as np
from typing import Optional, Union, List

@pd.api.extensions.register_dataframe_accessor("geo")
class GeoXarrayAccessor:
    """
    Custom accessor for GeoDataFrames containing xarray datasets or dataarrays.
    Handles both direct xarray objects and lists containing xarray objects.
    Can aggregate across time when time dimension has been expanded into the index.
    """
    
    def __init__(self, pandas_obj):
        self._obj = pandas_obj
        self._validate()
    
    def _validate(self):
        """Validate that the DataFrame has the expected structure."""
        if not isinstance(self._obj, gpd.GeoDataFrame):
            raise AttributeError("Can only use .geo accessor with GeoDataFrames")
        
        # Check for columns with xarray data (including lists containing xarray objects)
        self._xarray_columns = []
        for col in self._obj.columns:
            if col != 'geometry':
                sample_value = self._obj[col].iloc[0] if len(self._obj) > 0 else None
                
                # Check if it's directly an xarray object
                if isinstance(sample_value, (xr.Dataset, xr.DataArray)):
                    self._xarray_columns.append(col)
                # Check if it's a list containing xarray objects
                elif isinstance(sample_value, list) and len(sample_value) > 0:
                    if isinstance(sample_value[0], (xr.Dataset, xr.DataArray)):
                        self._xarray_columns.append(col)
        
        if not self._xarray_columns:
            raise AttributeError("No xarray Dataset or DataArray columns found")
    
    def _extract_xarray_object(self, value):
        """Extract xarray object from various formats (direct object, list, etc.)."""
        if isinstance(value, (xr.Dataset, xr.DataArray)):
            return value
        elif isinstance(value, list) and len(value) > 0:
            if isinstance(value[0], (xr.Dataset, xr.DataArray)):
                return value[0]  # Take the first item from the list
        return None
    
    def _get_target_columns(self, columns: Optional[List[str]] = None) -> List[str]:
        """
        Get the list of columns to operate on.
        
        Args:
            columns: List of column names to operate on. If None, uses all xarray columns.
        
        Returns:
            List of column names to operate on
        """
        if columns is None:
            return self._xarray_columns
        
        # Validate that specified columns exist and contain xarray data
        invalid_columns = [col for col in columns if col not in self._xarray_columns]
        if invalid_columns:
            raise ValueError(f"Columns {invalid_columns} are not valid xarray columns. "
                           f"Available xarray columns: {self._xarray_columns}")
        
        return columns
    
    def _should_aggregate_by_geometry(self, dim: Optional[Union[str, List[str]]] = None) -> bool:
        """
        Determine if we should aggregate by geometry (i.e., time dimension was expanded to index).
        
        Args:
            dim: Dimension(s) being reduced over
            
        Returns:
            True if we should group by geometry and aggregate across time rows
        """
        if dim is None:
            return False
        
        dims_to_reduce = [dim] if isinstance(dim, str) else dim
        
        # Check if 'time' is in the dimensions to reduce and if we have a MultiIndex with time
        if 'time' in dims_to_reduce:
            if hasattr(self._obj.index, 'names') and self._obj.index.names:
                # Check if time is one of the index levels
                return 'time' in self._obj.index.names
        
        return False
    
    def _get_geometry_level_name(self) -> Optional[str]:
        """Get the name of the geometry level in the MultiIndex."""
        if hasattr(self._obj.index, 'names') and self._obj.index.names:
            # Look for the level that's not 'time' - this should be the geometry level
            for name in self._obj.index.names:
                if name != 'time':
                    return name
        return None
    
    def _apply_reduction(self, reduction_func: str, dim: Optional[Union[str, List[str]]] = None, 
                        columns: Optional[List[str]] = None, **kwargs):
        """
        Apply a reduction function to specified xarray datasets/dataarrays in the GeoDataFrame.
        
        Args:
            reduction_func: Name of the xarray reduction method (e.g., 'mean', 'sum', 'std')
            dim: Dimension(s) to reduce over. If None, reduces over all dimensions
            columns: List of column names to operate on. If None, operates on all xarray columns
            **kwargs: Additional arguments to pass to the reduction function
        
        Returns:
            GeoDataFrame with reduced xarray data
        """
        target_columns = self._get_target_columns(columns)
        
        # Check if we need to aggregate by geometry (time dimension expanded to index)
        if self._should_aggregate_by_geometry(dim):
            return self._apply_temporal_aggregation(reduction_func, dim, target_columns, **kwargs)
        else:
            return self._apply_spatial_reduction(reduction_func, dim, target_columns, **kwargs)
    
    def _apply_temporal_aggregation(self, reduction_func: str, dim: Union[str, List[str]], 
                                  target_columns: List[str], **kwargs):
        """
        Apply aggregation across time by grouping by geometry.
        
        Args:
            reduction_func: Name of the reduction method
            dim: Dimension(s) being reduced (should include 'time')
            target_columns: Columns to operate on
            **kwargs: Additional arguments
        
        Returns:
            GeoDataFrame with time-aggregated data
        """
        geometry_level = self._get_geometry_level_name()
        if geometry_level is None:
            raise ValueError("Could not identify geometry level in MultiIndex")
        
        # Check if specific columns were requested for time aggregation
        if target_columns != self._xarray_columns:
            print("Warning: Cannot aggregate time on a single column. Aggregating all xarray columns instead.")
            target_columns = self._xarray_columns
        
        # Group by geometry level
        grouped = self._obj.groupby(level=geometry_level)
        
        result_data = []
        result_geometries = []
        result_index = []
        
        for geometry_key, group in grouped:
            # For each geometry, collect all xarray objects across time
            # The geometry is the group key itself (from the MultiIndex)
            new_row = {}
            
            for col in target_columns:
                xarray_objects = []
                
                # Collect all xarray objects for this geometry across different times
                for _, row in group.iterrows():
                    xr_data = self._extract_xarray_object(row[col])
                    if xr_data is not None:
                        xarray_objects.append(xr_data)
                
                if xarray_objects:
                    try:
                        # Concatenate along a new 'time' dimension
                        if isinstance(xarray_objects[0], xr.DataArray):
                            # Create time coordinate
                            time_coords = list(range(len(xarray_objects)))
                            concatenated = xr.concat(xarray_objects, dim='time')
                            concatenated = concatenated.assign_coords(time=time_coords)
                        elif isinstance(xarray_objects[0], xr.Dataset):
                            time_coords = list(range(len(xarray_objects)))
                            concatenated = xr.concat(xarray_objects, dim='time')
                            concatenated = concatenated.assign_coords(time=time_coords)
                        else:
                            raise TypeError(f"Unsupported xarray type: {type(xarray_objects[0])}")
                        
                        # Apply the reduction function over the time dimension
                        if hasattr(concatenated, reduction_func):
                            if 'skipna' not in kwargs and reduction_func in ['mean', 'sum', 'std', 'var', 'min', 'max', 'median', 'quantile']:
                                kwargs['skipna'] = True
                            
                            reduced_data = getattr(concatenated, reduction_func)(dim='time', **kwargs)
                            
                            # Check if result should be converted to scalar
                            if isinstance(reduced_data, xr.DataArray) and reduced_data.size == 1:
                                try:
                                    scalar_value = float(reduced_data.values)
                                    reduced_data = scalar_value
                                except (ValueError, TypeError):
                                    pass
                            elif isinstance(reduced_data, xr.Dataset) and len(reduced_data.dims) == 0:
                                try:
                                    vars_list = list(reduced_data.data_vars.keys())
                                    if len(vars_list) == 1:
                                        var_name = vars_list[0]
                                        scalar_value = float(reduced_data[var_name].values)
                                        reduced_data = scalar_value
                                except (ValueError, TypeError, KeyError):
                                    pass
                            
                            # Maintain original format (list vs direct)
                            original_format = group[col].iloc[0]
                            if isinstance(original_format, list):
                                new_row[col] = [reduced_data]
                            else:
                                new_row[col] = reduced_data
                        else:
                            raise AttributeError(f"'{type(concatenated).__name__}' object has no attribute '{reduction_func}'")
                    
                    except Exception as e:
                        print(f"Warning: Could not apply {reduction_func} to geometry {geometry_key}, column {col}: {e}")
                        # Keep the first value as fallback
                        new_row[col] = group[col].iloc[0]
                else:
                    # No xarray data found, keep first value
                    new_row[col] = group[col].iloc[0]
            
            result_data.append(new_row)
            result_geometries.append(geometry_key)
            result_index.append(geometry_key)
        
        # Create result GeoDataFrame
        # Create a normal DataFrame with just the data columns
        result_df = pd.DataFrame(result_data, index=result_index)
        
        # Add geometry as a temporary column
        result_df['_temp_geom'] = result_geometries
        
        # Convert to GeoDataFrame using the temporary geometry column
        result_gdf = gpd.GeoDataFrame(result_df, geometry='_temp_geom')
        
        # Drop the temporary geometry column (the geometry is now properly set as the active geometry)
        result_gdf = result_gdf.drop(columns=['_temp_geom'])
        
        result_gdf.index.name = geometry_level
        
        return result_gdf
    
    def _apply_spatial_reduction(self, reduction_func: str, dim: Optional[Union[str, List[str]]], 
                               target_columns: List[str], **kwargs):
        """
        Apply reduction to spatial dimensions within each xarray object.
        
        Args:
            reduction_func: Name of the reduction method
            dim: Spatial dimension(s) to reduce over
            target_columns: Columns to operate on
            **kwargs: Additional arguments
        
        Returns:
            GeoDataFrame with spatially reduced data
        """
        result_gdf = self._obj.copy()
        
        for col in target_columns:
            new_data = []
            for idx, row in self._obj.iterrows():
                original_value = row[col]
                xr_data = self._extract_xarray_object(original_value)
                
                if xr_data is not None:
                    try:
                        # Apply the reduction function
                        if hasattr(xr_data, reduction_func):
                            # Ensure skipna=True is set by default for most reduction functions
                            if 'skipna' not in kwargs and reduction_func in ['mean', 'sum', 'std', 'var', 'min', 'max', 'median', 'quantile']:
                                kwargs['skipna'] = True
                            reduced_data = getattr(xr_data, reduction_func)(dim=dim, **kwargs)
                            
                            # Check if the result is a scalar and convert to float if so
                            if isinstance(reduced_data, xr.DataArray):
                                if reduced_data.size == 1:
                                    try:
                                        scalar_value = float(reduced_data.values)
                                        reduced_data = scalar_value
                                    except (ValueError, TypeError):
                                        pass
                            elif isinstance(reduced_data, xr.Dataset):
                                try:
                                    if len(reduced_data.dims) == 0:
                                        vars_list = list(reduced_data.data_vars.keys())
                                        if len(vars_list) == 1:
                                            var_name = vars_list[0]
                                            scalar_value = float(reduced_data[var_name].values)
                                            reduced_data = scalar_value
                                except (ValueError, TypeError, KeyError):
                                    pass
                            
                            # Keep the same format as original (list vs direct)
                            if isinstance(original_value, list):
                                new_data.append([reduced_data])
                            else:
                                new_data.append(reduced_data)
                        else:
                            raise AttributeError(f"'{type(xr_data).__name__}' object has no attribute '{reduction_func}'")
                    except Exception as e:
                        # If reduction fails, keep original data
                        print(f"Warning: Could not apply {reduction_func} to row {idx}, column {col}: {e}")
                        new_data.append(original_value)
                else:
                    # If it's not xarray data, keep as is
                    new_data.append(original_value)
            
            result_gdf[col] = new_data
        
        return result_gdf
    
    def mean(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        """
        Calculate mean of xarray datasets/dataarrays.
        
        Args:
            dim: Dimension(s) to reduce over. If 'time', aggregates across time rows for each geometry.
                 If spatial dims like 'x', 'y', reduces within each xarray object.
            columns: List of column names to operate on. If None, operates on all xarray columns
            **kwargs: Additional arguments for the reduction function
        """
        return self._apply_reduction('mean', dim=dim, columns=columns, **kwargs)
    
    def sum(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        """
        Calculate sum of xarray datasets/dataarrays.
        
        Args:
            dim: Dimension(s) to reduce over. If 'time', aggregates across time rows for each geometry.
            columns: List of column names to operate on. If None, operates on all xarray columns
            **kwargs: Additional arguments for the reduction function
        """
        return self._apply_reduction('sum', dim=dim, columns=columns, **kwargs)
    
    def std(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        """
        Calculate standard deviation of xarray datasets/dataarrays.
        
        Args:
            dim: Dimension(s) to reduce over. If 'time', aggregates across time rows for each geometry.
            columns: List of column names to operate on. If None, operates on all xarray columns
            **kwargs: Additional arguments for the reduction function
        """
        return self._apply_reduction('std', dim=dim, columns=columns, **kwargs)
    
    def var(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        """
        Calculate variance of xarray datasets/dataarrays.
        
        Args:
            dim: Dimension(s) to reduce over. If 'time', aggregates across time rows for each geometry.
            columns: List of column names to operate on. If None, operates on all xarray columns
            **kwargs: Additional arguments for the reduction function
        """
        return self._apply_reduction('var', dim=dim, columns=columns, **kwargs)
    
    def min(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        """
        Calculate minimum of xarray datasets/dataarrays.
        
        Args:
            dim: Dimension(s) to reduce over. If 'time', aggregates across time rows for each geometry.
            columns: List of column names to operate on. If None, operates on all xarray columns
            **kwargs: Additional arguments for the reduction function
        """
        return self._apply_reduction('min', dim=dim, columns=columns, **kwargs)
    
    def max(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        """
        Calculate maximum of xarray datasets/dataarrays.
        
        Args:
            dim: Dimension(s) to reduce over. If 'time', aggregates across time rows for each geometry.
            columns: List of column names to operate on. If None, operates on all xarray columns
            **kwargs: Additional arguments for the reduction function
        """
        return self._apply_reduction('max', dim=dim, columns=columns, **kwargs)
    
    def median(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        """
        Calculate median of xarray datasets/dataarrays.
        
        Args:
            dim: Dimension(s) to reduce over. If 'time', aggregates across time rows for each geometry.
            columns: List of column names to operate on. If None, operates on all xarray columns
            **kwargs: Additional arguments for the reduction function
        """
        return self._apply_reduction('median', dim=dim, columns=columns, **kwargs)
    
    def quantile(self, q: float, dim: Optional[Union[str, List[str]]] = None, 
                columns: Optional[List[str]] = None, **kwargs):
        """
        Calculate quantile of xarray datasets/dataarrays.
        
        Args:
            q: Quantile to compute (between 0 and 1)
            dim: Dimension(s) to reduce over. If 'time', aggregates across time rows for each geometry.
            columns: List of column names to operate on. If None, operates on all xarray columns
            **kwargs: Additional arguments for the reduction function
        """
        return self._apply_reduction('quantile', dim=dim, columns=columns, q=q, **kwargs)
    
    def count(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        """
        Count non-NaN values in xarray datasets/dataarrays.
        
        Args:
            dim: Dimension(s) to reduce over. If 'time', aggregates across time rows for each geometry.
            columns: List of column names to operate on. If None, operates on all xarray columns
            **kwargs: Additional arguments for the reduction function
        """
        return self._apply_reduction('count', dim=dim, columns=columns, **kwargs)
    
    def to_values(self, columns: Optional[List[str]] = None):
        """
        Extract scalar values from xarray dataarrays and add them as new columns.
        Useful when dataarrays have been reduced to single values.
        
        Args:
            columns: List of column names to operate on. If None, operates on all xarray columns
        
        Returns:
            GeoDataFrame with extracted values as new columns
        """
        result_gdf = self._obj.copy()
        target_columns = self._get_target_columns(columns)
        
        for col in target_columns:
            values_to_add = []
            for idx, row in self._obj.iterrows():
                xr_data = self._extract_xarray_object(row[col])
                if isinstance(xr_data, xr.DataArray):
                    try:
                        if xr_data.size == 1:
                            scalar_value = float(xr_data.values)
                            values_to_add.append(scalar_value)
                        else:
                            values_to_add.append(np.nan)  # Can't convert non-scalar to value
                    except (ValueError, TypeError):
                        values_to_add.append(np.nan)
                else:
                    values_to_add.append(np.nan)
            
            # Add new column with scalar values
            new_col_name = f"{col}_value"
            result_gdf[new_col_name] = values_to_add
        
        return result_gdf
    
    def info(self):
        """Print information about xarray datasets/dataarrays in the GeoDataFrame."""
        print(f"GeoDataFrame shape: {self._obj.shape}")
        print(f"Columns: {list(self._obj.columns)}")
        print(f"Xarray columns: {self._xarray_columns}")
        print(f"Index structure: {self._obj.index.names if hasattr(self._obj.index, 'names') else 'Simple index'}")
        print(f"Geometry column name: {self._obj.geometry.name if hasattr(self._obj.geometry, 'name') else 'No geometry name'}")
        
        if hasattr(self._obj.index, 'names') and 'time' in self._obj.index.names:
            print("Note: Time dimension appears to be expanded into the index.")
            print("Use dim='time' to aggregate across time rows for each geometry.")
        
        for col in self._xarray_columns:
            print(f"\n--- Column: {col} ---")
            sample_data = self._extract_xarray_object(self._obj[col].iloc[0]) if len(self._obj) > 0 else None
            if isinstance(sample_data, xr.Dataset):
                print(f"Type: xarray.Dataset")
                print(f"Variables: {list(sample_data.data_vars.keys())}")
                print(f"Dimensions: {list(sample_data.dims.keys())}")
                print(f"Coordinates: {list(sample_data.coords.keys())}")
            elif isinstance(sample_data, xr.DataArray):
                print(f"Type: xarray.DataArray")
                print(f"Dimensions: {list(sample_data.dims)}")
                print(f"Shape: {sample_data.shape}")
                print(f"Data type: {sample_data.dtype}")