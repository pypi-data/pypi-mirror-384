
import xarray as xr


def open_cube(path: str, storage_options: dict | None = None, group: str = None):

    return xr.open_zarr(
        path,
        storage_options=storage_options,
        group=group,
        consolidated=True
    )
