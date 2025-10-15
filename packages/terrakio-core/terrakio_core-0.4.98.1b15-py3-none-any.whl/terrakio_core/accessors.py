# Standard library imports
import inspect
import time
import weakref
from typing import List, Optional, Union

# Third-party imports
import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr

# Local/relative imports
from .convenience_functions.zonal_stats import cloud_object
from .endpoints.mass_stats import MassStats

@pd.api.extensions.register_dataframe_accessor("geo")
class GeoXarrayAccessor:
    
    def __init__(self, pandas_obj):
        self._obj = pandas_obj
        
        # Only initialize client for cloud_object instances
        if isinstance(pandas_obj, cloud_object):
            self._client = pandas_obj.client
        else:
            self._client = None
        
        chain_state = self._obj.attrs.get('_geo_chain_state', None)
        
        if chain_state:
            self._pending_operations = chain_state.get('pending_operations', [])
            self._operation_sequence_id = chain_state.get('operation_sequence_id', None)
            self._last_operation_time = chain_state.get('last_operation_time', None)
            self._operation_count = chain_state.get('operation_count', 0)
            self._processing_in_progress = chain_state.get('processing_in_progress', False)
        else:
            self._pending_operations = []
            self._operation_sequence_id = None
            self._operation_count = 0
            self._last_operation_time = None
            self._processing_in_progress = False
        
        self._chain_refs = weakref.WeakSet()
        self._validate()

    def _validate(self):
        if isinstance(self._obj, gpd.GeoDataFrame):
            pass
        elif isinstance(self._obj, cloud_object):
            pass
        elif isinstance(self._obj, pd.DataFrame) and hasattr(self._obj, '_has_index_geometry'):
            pass
        elif isinstance(self._obj, pd.DataFrame) and hasattr(self._obj.index, 'names'):
            geometry_level = self._get_geometry_level_name()
            if geometry_level is None:
                raise AttributeError("Can only use .geo accessor with GeoDataFrames or DataFrames with geometry in index")
        else:
            raise AttributeError("Can only use .geo accessor with GeoDataFrames or DataFrames with geometry in index")
        
        self._xarray_columns = []
        self._scalar_columns = []
        
        for col in self._obj.columns:
            if col != 'geometry':
                sample_value = self._obj[col].iloc[0] if len(self._obj) > 0 else None
                
                if isinstance(sample_value, (xr.Dataset, xr.DataArray)):
                    self._xarray_columns.append(col)
                elif isinstance(sample_value, list) and len(sample_value) > 0:
                    if isinstance(sample_value[0], (xr.Dataset, xr.DataArray)):
                        self._xarray_columns.append(col)
                elif isinstance(sample_value, (int, float, np.integer, np.floating)):
                    self._scalar_columns.append(col)
                elif pd.isna(sample_value):
                    self._scalar_columns.append(col)
        
        if not self._xarray_columns and not self._scalar_columns:
            raise AttributeError("No xarray Dataset, DataArray, or aggregated scalar columns found")
    
    def _should_aggregate_by_geometry(self, dim: Optional[Union[str, List[str]]] = None) -> bool:
        if dim is None:
            return False
        
        dims_to_reduce = [dim] if isinstance(dim, str) else dim
        
        if 'time' in dims_to_reduce:
            if hasattr(self._obj.index, 'names') and self._obj.index.names:
                return 'time' in self._obj.index.names
        
        return False
    
    def _get_geometry_level_name(self) -> Optional[str]:
        if hasattr(self._obj.index, 'names') and self._obj.index.names:
            non_time_levels = [name for name in self._obj.index.names if name != 'time']
            if len(non_time_levels) == 1:
                return non_time_levels[0]
            
            for i, name in enumerate(self._obj.index.names):
                if name != 'time':
                    try:
                        sample_value = self._obj.index.get_level_values(i)[0]
                        if hasattr(sample_value, 'geom_type') or hasattr(sample_value, 'bounds'):
                            return name
                    except (IndexError, AttributeError):
                        continue
            
            if non_time_levels:
                return non_time_levels[0]
        
        return None
    
    def _try_convert_to_scalar(self, data):
        if isinstance(data, xr.DataArray) and data.size == 1:
            try:
                return float(data.values)
            except (ValueError, TypeError):
                pass
        elif isinstance(data, xr.Dataset) and len(data.dims) == 0:
            try:
                vars_list = list(data.data_vars.keys())
                if len(vars_list) == 1:
                    var_name = vars_list[0]
                    return float(data[var_name].values)
            except (ValueError, TypeError, KeyError):
                pass
        return data
    
    def _ensure_proper_geodataframe(self, result_data, result_geometries, result_index, geometry_level):
        result_df = pd.DataFrame(result_data)
        result_df['geometry'] = result_geometries
        
        try:
            crs = self._obj.crs
        except AttributeError:
            crs = None
        
        result_gdf = gpd.GeoDataFrame(result_df, geometry='geometry', crs=crs)
        
        if geometry_level:
            result_gdf = result_gdf.set_index(['geometry'])
            result_gdf.index.name = geometry_level
        else:
            result_gdf = result_gdf.set_index(['geometry'])
        
        result_gdf._original_crs = crs
        result_gdf._index_geometry_level = geometry_level
        result_gdf._has_index_geometry = True
        
        return result_gdf
    
    def to_index_geometry(self):
        if not hasattr(self._obj, '_has_index_geometry') or not self._obj._has_index_geometry:
            return self._obj
        
        data_columns = [col for col in self._obj.columns if col != 'geometry']
        result_df = self._obj[data_columns].copy()
        
        result_df._original_crs = getattr(self._obj, 'crs', None)
        result_df._index_geometry_level = getattr(self._obj, '_index_geometry_level', None)
        
        return result_df
    
    def to_column_geometry(self):
        if 'geometry' in self._obj.columns:
            return self._obj
        
        if hasattr(self._obj, '_index_geometry_level'):
            geometry_level = self._obj._index_geometry_level
            geometry_series = self._obj.index.to_series()
            
            result_gdf = gpd.GeoDataFrame(
                self._obj.copy(), 
                geometry=geometry_series,
                crs=getattr(self._obj, '_original_crs', None)
            )
            result_gdf._has_index_geometry = True
            result_gdf._index_geometry_level = geometry_level
            
            return result_gdf
        
        return self._obj
    
    def _get_geometry_level_name(self):
        if hasattr(self._obj.index, 'names'):
            for name in self._obj.index.names:
                if name and 'geometry' in str(name).lower():
                    return name
        return None
    
    def _inspect_call_stack_for_chain_end(self) -> bool:
        try:
            stack = inspect.stack()
            
            for i, frame_info in enumerate(stack[1:8]):
                if frame_info.code_context:
                    line = ''.join(frame_info.code_context).strip()
                    
                    if any(internal in frame_info.filename for internal in 
                        ['pandas', 'numpy', 'site-packages', '<frozen']):
                        continue
                    
                    if '.geo.' in line:
                        geo_count = line.count('.geo.')
                        pending_count = len(self._pending_operations)
                        
                        if pending_count >= geo_count:
                            return True
                        else:
                            return False
            
            return False
            
        except Exception:
            return False
    
    def _schedule_chain_completion_check(self):
        return self._inspect_call_stack_for_chain_end()
    
    def _trigger_processing_immediately(self):
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._sync_generate_and_start_processing)
            try:
                job_result = future.result(timeout=35)
                return job_result
            except concurrent.futures.TimeoutError:
                return None
            except Exception as e:
                return None
            
    def _extract_xarray_object(self, value):
        if isinstance(value, (xr.Dataset, xr.DataArray)):
            return value
        elif isinstance(value, list) and len(value) > 0:
            if isinstance(value[0], (xr.Dataset, xr.DataArray)):
                return value[0]
        
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
            
        return None

    def _get_target_columns(self, columns: Optional[List[str]] = None) -> tuple:
        if columns is None:
            return self._xarray_columns, self._scalar_columns
        
        all_valid_columns = self._xarray_columns + self._scalar_columns
        invalid_columns = [col for col in columns if col not in all_valid_columns]
        if invalid_columns:
            raise ValueError(f"Columns {invalid_columns} are not valid xarray or scalar columns. "
                           f"Available columns: {all_valid_columns}")
        
        target_xarray = [col for col in columns if col in self._xarray_columns]
        target_scalar = [col for col in columns if col in self._scalar_columns]
        
        return target_xarray, target_scalar

    def _apply_spatial_reduction(self, reduction_func: str, spatial_dims: Optional[List[str]], 
                               target_xarray_columns: List[str], **kwargs):
        result_gdf = self._obj.copy()
        
        for col in target_xarray_columns:
            new_data = []
            for idx, row in self._obj.iterrows():
                original_value = row[col]
                xr_data = self._extract_xarray_object(original_value)
                
                if xr_data is not None:
                    try:
                        if hasattr(xr_data, reduction_func):
                            if 'skipna' not in kwargs and reduction_func in ['mean', 'sum', 'std', 'var', 'min', 'max', 'median', 'quantile']:
                                kwargs['skipna'] = True
                            
                            if spatial_dims:
                                available_spatial_dims = [d for d in spatial_dims if d in xr_data.dims]
                                if available_spatial_dims:
                                    reduced_data = getattr(xr_data, reduction_func)(dim=available_spatial_dims, **kwargs)
                                else:
                                    reduced_data = xr_data
                            else:
                                reduced_data = getattr(xr_data, reduction_func)(dim=None, **kwargs)
                            
                            reduced_data = self._try_convert_to_scalar(reduced_data)
                            
                            if isinstance(original_value, list):
                                new_data.append([reduced_data])
                            else:
                                new_data.append(reduced_data)
                        else:
                            raise AttributeError(f"'{type(xr_data).__name__}' object has no attribute '{reduction_func}'")
                    except Exception as e:
                        new_data.append(original_value)
                else:
                    new_data.append(original_value)
            
            result_gdf[col] = new_data
        
        return result_gdf
    
    def _apply_scalar_temporal_aggregation(self, reduction_func: str, target_scalar_columns: List[str], **kwargs):
        geometry_level = self._get_geometry_level_name()
        if geometry_level is None:
            raise ValueError("Could not identify geometry level in MultiIndex")
        
        grouped = self._obj.groupby(level=geometry_level)
        
        result_data = []
        result_geometries = []
        result_index = []
        
        for geometry_key, group in grouped:
            new_row = {}
            
            for col in target_scalar_columns:
                try:
                    if reduction_func == 'mean':
                        agg_value = group[col].mean(skipna=True)
                    elif reduction_func == 'sum':
                        agg_value = group[col].sum(skipna=True)
                    elif reduction_func == 'std':
                        agg_value = group[col].std(skipna=True)
                    elif reduction_func == 'var':
                        agg_value = group[col].var(skipna=True)
                    elif reduction_func == 'min':
                        agg_value = group[col].min(skipna=True)
                    elif reduction_func == 'max':
                        agg_value = group[col].max(skipna=True)
                    elif reduction_func == 'median':
                        agg_value = group[col].median(skipna=True)
                    elif reduction_func == 'count':
                        agg_value = group[col].count()
                    elif reduction_func == 'quantile':
                        q = kwargs.get('q', 0.5)
                        agg_value = group[col].quantile(q, skipna=True)
                    else:
                        agg_value = group[col].mean(skipna=True)
                    
                    new_row[col] = agg_value
                    
                except Exception as e:
                    new_row[col] = np.nan
            
            for col in self._obj.columns:
                if col not in target_scalar_columns and col != 'geometry':
                    new_row[col] = group[col].iloc[0]
            
            result_data.append(new_row)
            result_geometries.append(geometry_key)
            result_index.append(geometry_key)
        
        return self._ensure_proper_geodataframe(result_data, result_geometries, result_index, geometry_level)
    
    def _apply_mixed_aggregation(self, reduction_func: str, temporal_dims: List[str], 
                               spatial_dims: List[str], target_xarray_columns: List[str], 
                               target_scalar_columns: List[str], **kwargs):
        geometry_level = self._get_geometry_level_name()
        if geometry_level is None:
            raise ValueError("Could not identify geometry level in MultiIndex")
        
        if target_xarray_columns != self._xarray_columns:
            target_xarray_columns = self._xarray_columns
        
        grouped = self._obj.groupby(level=geometry_level)
        
        result_data = []
        result_geometries = []
        result_index = []
        
        for geometry_key, group in grouped:
            new_row = {}
            
            for col in target_xarray_columns:
                xarray_objects = []
                valid_time_steps = 0
                total_time_steps = len(group)
                
                for _, row in group.iterrows():
                    xr_data = self._extract_xarray_object(row[col])
                    if xr_data is not None:
                        xarray_objects.append(xr_data)
                        valid_time_steps += 1
                
                if xarray_objects:
                    try:
                        if isinstance(xarray_objects[0], xr.DataArray):
                            time_coords = list(range(len(xarray_objects)))
                            concatenated = xr.concat(xarray_objects, dim='time')
                            concatenated = concatenated.assign_coords(time=time_coords)
                        elif isinstance(xarray_objects[0], xr.Dataset):
                            time_coords = list(range(len(xarray_objects)))
                            concatenated = xr.concat(xarray_objects, dim='time')
                            concatenated = concatenated.assign_coords(time=time_coords)
                        else:
                            raise TypeError(f"Unsupported xarray type: {type(xarray_objects[0])}")
                        
                        if hasattr(concatenated, reduction_func):
                            if 'skipna' not in kwargs and reduction_func in ['mean', 'sum', 'std', 'var', 'min', 'max', 'median', 'quantile']:
                                kwargs['skipna'] = True
                            
                            if temporal_dims:
                                reduced_data = getattr(concatenated, reduction_func)(dim='time', **kwargs)
                            else:
                                reduced_data = concatenated
                            
                            if spatial_dims:
                                available_spatial_dims = [d for d in spatial_dims if d in reduced_data.dims]
                                if available_spatial_dims:
                                    reduced_data = getattr(reduced_data, reduction_func)(dim=available_spatial_dims, **kwargs)
                            
                            all_dims_reduced = (
                                temporal_dims and spatial_dims and 
                                set(temporal_dims + spatial_dims) >= set(reduced_data.dims)
                            )
                            if all_dims_reduced:
                                reduced_data = self._try_convert_to_scalar(reduced_data)
                            
                            original_format = group[col].iloc[0]
                            if isinstance(original_format, list):
                                new_row[col] = [reduced_data]
                            else:
                                new_row[col] = reduced_data
                        else:
                            raise AttributeError(f"'{type(concatenated).__name__}' object has no attribute '{reduction_func}'")
                    
                    except Exception as e:
                        new_row[col] = np.nan
                else:
                    new_row[col] = np.nan
            
            for col in target_scalar_columns:
                new_row[col] = group[col].iloc[0]
            
            for col in self._obj.columns:
                if (col not in target_xarray_columns and 
                    col not in target_scalar_columns and 
                    col != 'geometry'):
                    new_row[col] = group[col].iloc[0]
            
            result_data.append(new_row)
            result_geometries.append(geometry_key)
            result_index.append(geometry_key)
        
        return self._ensure_proper_geodataframe(result_data, result_geometries, result_index, geometry_level)
    
    def _apply_mixed_scalar_xarray_aggregation(self, reduction_func: str, temporal_dims: List[str], 
                                             spatial_dims: List[str], target_xarray_columns: List[str], 
                                             target_scalar_columns: List[str], **kwargs):
        geometry_level = self._get_geometry_level_name()
        if geometry_level is None:
            raise ValueError("Could not identify geometry level in MultiIndex")
        
        grouped = self._obj.groupby(level=geometry_level)
        
        result_data = []
        result_geometries = []
        result_index = []
        
        for geometry_key, group in grouped:
            new_row = {}
            
            for col in target_xarray_columns:
                xarray_objects = []
                
                for _, row in group.iterrows():
                    xr_data = self._extract_xarray_object(row[col])
                    if xr_data is not None:
                        xarray_objects.append(xr_data)
                
                if xarray_objects:
                    try:
                        if isinstance(xarray_objects[0], xr.DataArray):
                            time_coords = list(range(len(xarray_objects)))
                            concatenated = xr.concat(xarray_objects, dim='time')
                            concatenated = concatenated.assign_coords(time=time_coords)
                        elif isinstance(xarray_objects[0], xr.Dataset):
                            time_coords = list(range(len(xarray_objects)))
                            concatenated = xr.concat(xarray_objects, dim='time')
                            concatenated = concatenated.assign_coords(time=time_coords)
                        else:
                            raise TypeError(f"Unsupported xarray type: {type(xarray_objects[0])}")
                        
                        if hasattr(concatenated, reduction_func):
                            if 'skipna' not in kwargs and reduction_func in ['mean', 'sum', 'std', 'var', 'min', 'max', 'median', 'quantile']:
                                kwargs['skipna'] = True
                            
                            if temporal_dims:
                                reduced_data = getattr(concatenated, reduction_func)(dim='time', **kwargs)
                            else:
                                reduced_data = concatenated
                            
                            if spatial_dims:
                                available_spatial_dims = [d for d in spatial_dims if d in reduced_data.dims]
                                if available_spatial_dims:
                                    reduced_data = getattr(reduced_data, reduction_func)(dim=available_spatial_dims, **kwargs)
                            
                            all_dims_reduced = (
                                temporal_dims and spatial_dims and 
                                set(temporal_dims + spatial_dims) >= set(reduced_data.dims)
                            )
                            if all_dims_reduced:
                                reduced_data = self._try_convert_to_scalar(reduced_data)
                            
                            original_format = group[col].iloc[0]
                            if isinstance(original_format, list):
                                new_row[col] = [reduced_data]
                            else:
                                new_row[col] = reduced_data
                        else:
                            raise AttributeError(f"'{type(concatenated).__name__}' object has no attribute '{reduction_func}'")
                    
                    except Exception as e:
                        new_row[col] = np.nan
                else:
                    new_row[col] = np.nan
            
            for col in target_scalar_columns:
                try:
                    if reduction_func == 'mean':
                        agg_value = group[col].mean(skipna=True)
                    elif reduction_func == 'sum':
                        agg_value = group[col].sum(skipna=True)
                    elif reduction_func == 'std':
                        agg_value = group[col].std(skipna=True)
                    elif reduction_func == 'var':
                        agg_value = group[col].var(skipna=True)
                    elif reduction_func == 'min':
                        agg_value = group[col].min(skipna=True)
                    elif reduction_func == 'max':
                        agg_value = group[col].max(skipna=True)
                    elif reduction_func == 'median':
                        agg_value = group[col].median(skipna=True)
                    elif reduction_func == 'count':
                        agg_value = group[col].count()
                    elif reduction_func == 'quantile':
                        q = kwargs.get('q', 0.5)
                        agg_value = group[col].quantile(q, skipna=True)
                    else:
                        agg_value = group[col].mean(skipna=True)
                    
                    new_row[col] = agg_value
                    
                except Exception as e:
                    new_row[col] = np.nan
            
            for col in self._obj.columns:
                if (col not in target_xarray_columns and 
                    col not in target_scalar_columns and 
                    col != 'geometry'):
                    new_row[col] = group[col].iloc[0]
            
            result_data.append(new_row)
            result_geometries.append(geometry_key)
            result_index.append(geometry_key)
        
        return self._ensure_proper_geodataframe(result_data, result_geometries, result_index, geometry_level)
    
    def _apply_temporal_aggregation(self, reduction_func: str, temporal_dims: List[str], 
                                  target_xarray_columns: List[str], target_scalar_columns: List[str], **kwargs):
        geometry_level = self._get_geometry_level_name()
        if geometry_level is None:
            raise ValueError("Could not identify geometry level in MultiIndex")
        
        if target_xarray_columns != self._xarray_columns:
            target_xarray_columns = self._xarray_columns
        
        grouped = self._obj.groupby(level=geometry_level)
        
        result_data = []
        result_geometries = []
        result_index = []
        
        for geometry_key, group in grouped:
            new_row = {}
            
            for col in target_xarray_columns:
                xarray_objects = []
                
                for _, row in group.iterrows():
                    xr_data = self._extract_xarray_object(row[col])
                    if xr_data is not None:
                        xarray_objects.append(xr_data)
                
                if xarray_objects:
                    try:
                        if isinstance(xarray_objects[0], xr.DataArray):
                            time_coords = list(range(len(xarray_objects)))
                            concatenated = xr.concat(xarray_objects, dim='time')
                            concatenated = concatenated.assign_coords(time=time_coords)
                        elif isinstance(xarray_objects[0], xr.Dataset):
                            time_coords = list(range(len(xarray_objects)))
                            concatenated = xr.concat(xarray_objects, dim='time')
                            concatenated = concatenated.assign_coords(time=time_coords)
                        else:
                            raise TypeError(f"Unsupported xarray type: {type(xarray_objects[0])}")
                        
                        if hasattr(concatenated, reduction_func):
                            if 'skipna' not in kwargs and reduction_func in ['mean', 'sum', 'std', 'var', 'min', 'max', 'median', 'quantile']:
                                kwargs['skipna'] = True
                            
                            reduced_data = getattr(concatenated, reduction_func)(dim='time', **kwargs)
                            
                            original_format = group[col].iloc[0]
                            if isinstance(original_format, list):
                                new_row[col] = [reduced_data]
                            else:
                                new_row[col] = reduced_data
                        else:
                            raise AttributeError(f"'{type(concatenated).__name__}' object has no attribute '{reduction_func}'")
                    
                    except Exception as e:
                        new_row[col] = np.nan
                else:
                    new_row[col] = np.nan
            
            for col in target_scalar_columns:
                new_row[col] = group[col].iloc[0]
            
            for col in self._obj.columns:
                if (col not in target_xarray_columns and 
                    col not in target_scalar_columns and 
                    col != 'geometry'):
                    new_row[col] = group[col].iloc[0]
            
            result_data.append(new_row)
            result_geometries.append(geometry_key)
            result_index.append(geometry_key)
        
        return self._ensure_proper_geodataframe(result_data, result_geometries, result_index, geometry_level)
    
    def _apply_spatial_reduction(self, reduction_func: str, spatial_dims: Optional[List[str]], 
                               target_xarray_columns: List[str], **kwargs):
        result_gdf = self._obj.copy()
        
        for col in target_xarray_columns:
            new_data = []
            for idx, row in self._obj.iterrows():
                original_value = row[col]
                xr_data = self._extract_xarray_object(original_value)
                
                if xr_data is not None:
                    try:
                        if hasattr(xr_data, reduction_func):
                            if 'skipna' not in kwargs and reduction_func in ['mean', 'sum', 'std', 'var', 'min', 'max', 'median', 'quantile']:
                                kwargs['skipna'] = True
                            
                            if spatial_dims:
                                available_spatial_dims = [d for d in spatial_dims if d in xr_data.dims]
                                if available_spatial_dims:
                                    reduced_data = getattr(xr_data, reduction_func)(dim=available_spatial_dims, **kwargs)
                                else:
                                    reduced_data = xr_data
                            else:
                                reduced_data = getattr(xr_data, reduction_func)(dim=None, **kwargs)
                            
                            reduced_data = self._try_convert_to_scalar(reduced_data)
                            
                            if isinstance(original_value, list):
                                new_data.append([reduced_data])
                            else:
                                new_data.append(reduced_data)
                        else:
                            raise AttributeError(f"'{type(xr_data).__name__}' object has no attribute '{reduction_func}'")
                    except Exception as e:
                        new_data.append(original_value)
                else:
                    new_data.append(original_value)
            
            result_gdf[col] = new_data
        
        return result_gdf
    
    def _apply_cloud_reduction(self, reduction_func: str, dim: Optional[Union[str, List[str]]] = None, 
                            columns: Optional[List[str]] = None, **kwargs):
        
        if hasattr(self._obj, 'job_id') and self._obj.job_id and self._client:
            import asyncio
            import concurrent.futures
            
            def check_job_status():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self._client.mass_stats.track_job([self._obj.job_id])
                    )
                finally:
                    loop.close()
            
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(check_job_status)
                    track_info = future.result(timeout=10)  # Short timeout for status check
                    
                    job_info = track_info[self._obj.job_id]
                    status = job_info['status']
                    
                    if status in ["Failed", "Cancelled", "Error"]:
                        raise RuntimeError(f"The zonal stats job (job_id: {self._obj.job_id}) has failed, cancelled, or errored. Please check the job status!")
                    
                    elif status != "Completed":
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
                            f"The zonal stats job (job_id: {self._obj.job_id}) is still running. "
                            f"Progress: [{bar}] {percentage:.1f}% ({completed}/{total}). "
                            f"Please come back at a later time!"
                        )
                    
            except concurrent.futures.TimeoutError:
                self._client.logger.warning("Timeout checking job status, proceeding with reduction")
            except Exception as e:
                if "still running" in str(e) or "failed" in str(e).lower():
                    raise  # Re-raise our custom errors
                else:
                    self._client.logger.warning(f"Could not check job status: {e}, proceeding with reduction")
        
        current_time = time.time()
        chain_reset_threshold = 0.01
        
        if (self._last_operation_time is None or 
            current_time - self._last_operation_time > chain_reset_threshold):
            
            if not self._pending_operations:
                self._operation_sequence_id = int(current_time * 1000)
                self._operation_count = 0
        
        self._last_operation_time = current_time
        self._operation_count += 1
        
        params = {"dim": dim, "columns": columns, **kwargs}
        description = f"Apply {reduction_func} over dimension(s): {dim}" if dim else f"Apply {reduction_func} over all dimensions"
        
        operation = {
            "type": reduction_func,
            "description": description,
            "params": params,
            "timestamp": pd.Timestamp.now(),
            "sequence_id": self._operation_sequence_id
        }
        
        self._pending_operations.append(operation)
        
        chain_complete = self._schedule_chain_completion_check()
        
        result = self._obj.copy()
        result.attrs = self._obj.attrs.copy()
        
        if hasattr(self._obj, 'client'):
            object.__setattr__(result, 'client', self._obj.client)
        if hasattr(self._obj, 'job_id'):
            object.__setattr__(result, 'job_id', self._obj.job_id)
        if hasattr(self._obj, 'job_name'):
            object.__setattr__(result, 'job_name', self._obj.job_name)

        if not result.attrs:
            result.attrs = {}
        if chain_complete:
            job_result = self._trigger_processing_immediately()
            # result.attrs['job_id'] = job_result
            return job_result
        
        result.attrs['_geo_chain_state'] = {
            'pending_operations': self._pending_operations,
            'operation_sequence_id': self._operation_sequence_id,
            'last_operation_time': self._last_operation_time,
            'operation_count': self._operation_count,
            'processing_in_progress': getattr(self, '_processing_in_progress', False)
        }
        
        return result

    def _apply_local_reduction(self, reduction_func: str, dim: Optional[Union[str, List[str]]] = None, 
                               columns: Optional[List[str]] = None, **kwargs):
        target_xarray_columns, target_scalar_columns = self._get_target_columns(columns)
        
        if dim is None:
            if target_xarray_columns:
                return self._apply_spatial_reduction(reduction_func, dim, target_xarray_columns, **kwargs)
            else:
                return self._obj.copy()
        
        dims_to_reduce = [dim] if isinstance(dim, str) else dim
        
        temporal_dims = [d for d in dims_to_reduce if d == 'time']
        spatial_dims = [d for d in dims_to_reduce if d != 'time']
        
        has_temporal_agg = (
            temporal_dims and 
            hasattr(self._obj.index, 'names') and 
            self._obj.index.names and 
            'time' in self._obj.index.names
        )
        
        if has_temporal_agg and target_scalar_columns and not target_xarray_columns:
            return self._apply_scalar_temporal_aggregation(reduction_func, target_scalar_columns, **kwargs)
        
        if has_temporal_agg and target_scalar_columns and target_xarray_columns:
            return self._apply_mixed_scalar_xarray_aggregation(reduction_func, temporal_dims, spatial_dims, 
                                                             target_xarray_columns, target_scalar_columns, **kwargs)
        
        if not target_xarray_columns and target_scalar_columns:
            if spatial_dims:
                pass
            return self._obj.copy()
        
        if has_temporal_agg and spatial_dims:
            return self._apply_mixed_aggregation(reduction_func, temporal_dims, spatial_dims, 
                                               target_xarray_columns, target_scalar_columns, **kwargs)
        elif has_temporal_agg:
            return self._apply_temporal_aggregation(reduction_func, temporal_dims, 
                                                  target_xarray_columns, target_scalar_columns, **kwargs)
        else:
            return self._apply_spatial_reduction(reduction_func, spatial_dims, 
                                               target_xarray_columns, **kwargs)
    
    def _apply_reduction(self, reduction_func: str, dim: Optional[Union[str, List[str]]] = None, 
                        columns: Optional[List[str]] = None, **kwargs):
        if isinstance(self._obj, cloud_object):
            return self._apply_cloud_reduction(reduction_func = reduction_func, dim = dim, columns = columns, **kwargs)
        else:
            return self._apply_local_reduction(reduction_func = reduction_func, dim = dim, columns = columns, **kwargs)

    def _sync_generate_and_start_processing(self):
        if not self._pending_operations or getattr(self, '_processing_in_progress', False):
            return None
        
        self._processing_in_progress = True
        
        try:
            sequence_id = self._operation_sequence_id
            script_content = self._generate_post_processing_script()
            client = self._client
            if client:
                mass_stats = MassStats(client)
                
                import asyncio
                import concurrent.futures
                
                def run_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    # we don't actually have the dataset name, currently it is just getting job named zonal stats job
                    try:
                        return loop.run_until_complete(
                            mass_stats.zonal_stats_transform(
                                data_name=self._obj.job_name,
                                output="netcdf",
                                consumer = script_content.encode('utf-8'),
                                overwrite=True,
                            )
                        )
                    finally:
                        loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async)
                    result = future.result(timeout=30)
                    return result
            
            return None

        except Exception as e:
            return None
        finally:
            self._processing_in_progress = False
            self._pending_operations.clear()

    def _generate_post_processing_script(self) -> str:
        script_lines = [
            "import pandas as pd",
            "import xarray as xr",
            "import numpy as np",
            "from io import BytesIO",
            "import tempfile",
            "import os",
            "import traceback",
            "",
            "def consume(filename, file_bytes, metadata):",
        ]
        
        script_lines.extend([
            "    tmp_file = None",
            "    nc_tmp_file = None", 
            "    ds = None",
            "    ",
            "    try:",
            "        with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp_file:",
            "            tmp_file.write(file_bytes)",
            "            tmp_file.flush()",
            "            ds = xr.open_dataset(tmp_file.name, engine='h5netcdf')",
            "        ",
        ])
        
        # Add operations without excessive debugging
        for i, op in enumerate(self._pending_operations):
            op_type = op['type']
            params = op['params']
            dim = params.get('dim')
            
            if dim:
                dim_str = repr(dim)
                script_lines.append(f"        ds = ds.{op_type}(dim={dim_str}, skipna=True)")
            else:
                script_lines.append(f"        ds = ds.{op_type}(skipna=True)")
            script_lines.append("")
        
        script_lines.extend([
            "        # Determine output format based on data structure",
            "        base_filename = os.path.splitext(filename)[0]",
            "        ",
            "        # Check if all data variables are scalar (0-dimensional)",
            "        all_scalar = True",
            "        for var_name in ds.data_vars:",
            "            if ds[var_name].dims:",
            "                all_scalar = False",
            "                break",
            "        ",
            "        if all_scalar:",
            "            # Output as CSV - all variables are scalar",
            "            result_data = {}",
            "            for var_name in ds.data_vars:",
            "                result_data[var_name] = float(ds[var_name].values)",
            "            ",
            "            result_df = pd.DataFrame([result_data])",
            '            output_filename = f"{base_filename}_processed.csv"',
            "            csv_data = result_df.to_csv(index=False).encode()",
            "            ",
            "            if ds is not None:",
            "                ds.close()",
            "            if tmp_file and hasattr(tmp_file, 'name'):",
            "                try:",
            "                    os.unlink(tmp_file.name)",
            "                except:",
            "                    pass",
            "            return output_filename, csv_data",
            "        else:",
            "            # Output as NetCDF - still has dimensions",
            '            output_filename = f"{base_filename}_processed.nc"',
            "            # Use temp file instead of BytesIO to avoid buffer closing issues",
            "            with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as nc_tmp_file:",
            "                ds.to_netcdf(nc_tmp_file.name, format='NETCDF3_64BIT')",
            "            ",
            "            # Read the temp file back as bytes",
            "            with open(nc_tmp_file.name, 'rb') as f:",
            "                netcdf_data = f.read()",
            "            ",
            "            # Clean up temp files",
            "            try:",
            "                os.unlink(nc_tmp_file.name)",
            "            except:",
            "                pass",
            "            ",
            "            if ds is not None:",
            "                ds.close()",
            "            if tmp_file and hasattr(tmp_file, 'name'):",
            "                try:",
            "                    os.unlink(tmp_file.name)",
            "                except:",
            "                    pass",
            "            return output_filename, netcdf_data",
        ])
        
        script_lines.extend([
            "        ",
            "    except Exception as e:",
            "        ",
            "        # Clean up resources",
            "        if ds is not None:",
            "            try:",
            "                ds.close()",
            "            except:",
            "                pass",
            "        ",
            "        if tmp_file and hasattr(tmp_file, 'name'):",
            "            try:",
            "                os.unlink(tmp_file.name)",
            "            except:",
            "                pass",
            "        ",
            "        if nc_tmp_file and hasattr(nc_tmp_file, 'name'):",
            "            try:",
            "                os.unlink(nc_tmp_file.name)",
            "            except:",
            "                pass",
            "        ",
            "        return None, None",
        ])
        
        return "\n".join(script_lines)

    @property
    def job_id(self):
        return self._obj.attrs.get('job_id')
    
    def mean(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        return self._apply_reduction('mean', dim=dim, columns=columns, **kwargs)
    
    def sum(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        return self._apply_reduction('sum', dim=dim, columns=columns, **kwargs)
    
    def max(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        return self._apply_reduction('max', dim=dim, columns=columns, **kwargs)
    
    def min(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        return self._apply_reduction('min', dim=dim, columns=columns, **kwargs)
    
    def std(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        return self._apply_reduction('std', dim=dim, columns=columns, **kwargs)
    
    def var(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        return self._apply_reduction('var', dim=dim, columns=columns, **kwargs)
    
    def median(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        return self._apply_reduction('median', dim=dim, columns=columns, **kwargs)
    
    def count(self, dim: Optional[Union[str, List[str]]] = None, columns: Optional[List[str]] = None, **kwargs):
        return self._apply_reduction('count', dim=dim, columns=columns, **kwargs)