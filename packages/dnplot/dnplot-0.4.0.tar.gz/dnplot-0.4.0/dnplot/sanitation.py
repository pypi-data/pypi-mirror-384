import xarray as xr
import pandas as pd
import numpy as np

def force_to_ds(ds):
    """Takes a dict, dnora ModelRun and gets the 'waveseries' object's xr.Dataset.
    If a geo-skeleton is given, then that dataset is returned.
    If a dataset is given, it is returned."""
    if not ds:
        return None
    ds = ds.get('waveseries') or ds
    if not isinstance(ds,xr.Dataset):
        ds = ds.ds()
    return ds

def get_units(ds, var:str) -> str:
    """Takes the units from a xr.Dataset"""
    return getattr(ds.get(var), 'units', '')

def get_varname(ds, var: str) -> str:
    """Gets a long_name, standard_name or short_name from a dataset"""
    return (
        getattr(ds.get(var), 'long_name', None) or
        getattr(ds.get(var), 'standard_name', None) or
        getattr(ds.get(var), 'short_name', var)
    )

def xarray_to_dataframe(ds) -> pd.DataFrame:
    
    df = ds.to_dataframe()
    df = df.reset_index()
    col_drop = ["lon", "lat", "inds"]
    df = df.drop(col_drop, axis="columns")
    df.set_index("time", inplace=True)
    df = df.resample("h").asfreq()
    df = df.reset_index()
    return df


def get_one_point_merged_dataframe(xmodel_all, ymodel_all, inds_x, inds_y):
    xmodel = xmodel_all.sel(inds=inds_x)
    xdf = xarray_to_dataframe(xmodel)
    if ymodel_all is not None:
        ymodel = ymodel_all.sel(inds=inds_y)
    else:
        ymodel = None
    
    if ymodel is not None:
        ydf = xarray_to_dataframe(ymodel)
        xdf = xdf.set_index("time").add_suffix(f" {xmodel.name}").reset_index()
        ydf = ydf.set_index("time").add_suffix(f" {ymodel.name}").reset_index()
        df =  pd.merge(xdf,ydf,on="time")
    else:
        ydf = xdf
        df = xdf

    return xdf, ydf, df

def cut_ds_to_one_point(ds, lon, lat) -> xr.Dataset:
    if ds is None:
        return ds
    if lon is not None and lat is not None:
        distances = np.sqrt((ds["lon"] - lon)**2 + (ds["lat"] - lat)**2)
        nearest_index = distances.argmin().item()
        ds = ds.isel(inds=nearest_index)

    if ds.lon.size > 1 or ds.lat.size > 1:
        raise ValueError(f"Please provide data with only one point, or give the specification for a point with keywords 'lon=..., lat=...'. Now lon={ds.lon.values}, lat={ds.lat.values}.")    

    return ds

