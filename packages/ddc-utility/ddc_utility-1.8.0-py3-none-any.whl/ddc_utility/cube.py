
import xarray as xr
import rioxarray # keep this
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer

def open_cube(path: str, storage_options: dict | None = None, group: str = None):

    return xr.open_zarr(
        path,
        storage_options=storage_options,
        group=group,
        consolidated=True
    )

def clip_cube(cube: xr.Dataset, geometry_json: dict) -> xr.Dataset:

    # if 'aoi_mask' in cube:
    #     cube['aoi_mask'] = cube['aoi_mask'].astype('bool')

    cube_crs = cube.rio.crs.to_epsg()

    transformer = Transformer.from_crs(
        "EPSG:4326", f"EPSG:{cube_crs}", always_xy=True)

    projected_geom = transform(
        transformer.transform, shape(geometry_json))

    transformed_geojson_geometry = mapping(projected_geom)

    bounds = projected_geom.bounds

    cube = cube.sel(
        x=slice(bounds[0], bounds[2]), y=slice(bounds[3], bounds[1]))

    return cube.rio.clip([transformed_geojson_geometry], drop=True)
