import os
import json
import platform
import time
import datetime
import functools
from abc import ABC, abstractmethod

from importlib.metadata import version
from enum import Enum

import pandas as pd
import requests
import xarray as xr
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon

from pydantic import SecretStr

from ddc_utility.auth import OAuth2BearerHandler
from ddc_utility.constants import (DEFAULT_AOI_BUCKET, DEFAULT_DDC_BUCKET,
                                   DEFAULT_DDC_HOST)
from ddc_utility.cube import open_cube, clip_cube
from ddc_utility.errors import (BadRequest, DdcClientError, DdcException,
                                DdcRequestError, Forbidden, HTTPException,
                                NotFound, ServerError, TooManyRequests,
                                Unauthorized)
from ddc_utility.utils import Geometry, TimeRange, AccesToken
from ddc_utility.logger import log

try:
    package_version = version("ddc-utility")
except Exception:
    package_version = ""

class ReturnType(Enum):
    DICT = "dict"
    DATAFRAME = "dataframe"

output_data_type_map = {
    ReturnType.DATAFRAME: ReturnType.DATAFRAME,
    ReturnType.DICT: ReturnType.DICT,
    1: ReturnType.DATAFRAME,
    2: ReturnType.DICT
}

def authorize_request(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if self._auth is None or self._auth.is_expired():
            self._set_auth()

        return method(self, *args, **kwargs)
    return wrapper


def authorize_s3_access(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        now = round(time.time())

        if self._aws_s3 is None or (self._aws_session_exp - now < 60):
            temp_cred = self.fetch_temporary_credentials()
            self._aws_s3 = {
                "key": temp_cred["access_key"],
                "secret": temp_cred["secret_key"],
                "token": temp_cred["session_token"]
            }
            if temp_cred["endpoint"] is not None:
                self._aws_s3["client_kwargs"] = {
                    "endpoint_url": temp_cred["endpoint"]
                }
            self._aws_session_exp = temp_cred["expires_at"]

        return method(self, *args, **kwargs)
    return wrapper

class BaseClient(ABC):
    
    def __init__(
            self,
            host: str | None = None,
            wait_on_rate_limit: bool = False
            ) -> None:

        self.host = host
        self.wait_on_rate_limit = wait_on_rate_limit

        self._auth = None
        self._session = requests.Session()
        self._user_agent = (
            f"Python/{platform.python_version()} "
            f"Requests/{requests.__version__} "
            f"ddc_cube/{package_version}"
        )

        self._aws_s3 = None
        self._aws_session_exp = 0

    @abstractmethod
    def _set_auth(self):
        pass

    def request(
        self,
        method: str,
        route: str,
        params: dict | None = None,
        data: dict | None = None,
        content_type: str | None = None,
        accept: str | None = None
        ) -> requests.Response:

        headers = {
            "User-Agent": self._user_agent
        }
        if content_type is not None:
            headers["Content-Type"] = content_type
        if accept is not None:
            headers["Accept"] = accept

        url = self.host + route

        log.debug(
            f"\nMaking API request: {method} {url}\n"
            f"Parameters: {params}\n"
            f"Headers: {headers}"
        )

        with self._session.request(
                method, url, params=params, data=data, headers=headers, auth=self._auth) as response:

            log.debug(
                "\nReceived API response: "
                f"{response.status_code} {response.reason}\n"
                f"Headers: {response.headers}\n"
            )

            if response.status_code == 400:
                raise BadRequest(response)
            if response.status_code == 401:
                raise Unauthorized(response)
            if response.status_code == 403:
                raise Forbidden(response)
            if response.status_code == 404:
                raise NotFound(response)
            if response.status_code == 429:
                if self.wait_on_rate_limit:
                    reset_time = int(response.headers["x-rate-limit-reset"])
                    sleep_time = reset_time - int(time.time()) + 1
                    if sleep_time > 0:
                        log.warning(
                            "Rate limit exceeded. "
                            f"Sleeping for {sleep_time} seconds."
                        )
                        time.sleep(sleep_time)
                    return self.request(method, route, params, data, content_type, accept)
                else:
                    raise TooManyRequests(response)
            if response.status_code >= 500:
                raise ServerError(response)
            if not 200 <= response.status_code < 300:
                raise HTTPException(response)
            
            if b"Error" in response.content or b'error' in response.content:
                raise HTTPException(response)

            return response
        
    @authorize_request
    def fetch_temporary_credentials(self) -> dict:
        """Fetch token from a remote token endpoint."""

        route = "/user-manager/filesystem-access"
        accept = "application/json"
        content_type = "application/json"

        try:
            response = self.request(
                "POST", route, content_type=content_type, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't fetch temporary credentials with HTTP exception: {error}"
            ) from None

        result = response.json()
        
        if result["provider"] != "s3":
            raise DdcClientError(
                f"Unimplemented filesystem provider: {result['provider']}") from None

        credentials = result["credentials"] 
        credentials["endpoint"] = result["endpoint"]
        credentials["expires_at"] = int(datetime.datetime.fromisoformat(credentials.pop("expiration")).timestamp())

        return credentials
        

class IntegrationClient(BaseClient):
    """IntegrationClient class for interacting with the DDC API. Uses a Bearer token for authentication.

    Attributes:
        bearer_token (str): Bearer token.
        expires_in (int): Token expiration timestamp
        host (str | None, optional): Alternative Danube Data Cube host url.
          If None, it will use DEFAULT_DDC_HOST constant. Defaults to None.
    """

    def __init__(
        self,
        bearer_token: str,
        expires_in: int,
        host: str | None = None
        ) -> None:

        """Initializes the IntegrationClient instance.

        Args:
            bearer_token (str): Bearer token.
            expires_in (int): Token expiration timestamp
            host (str | None, optional): Alternative Danube Data Cube host url.
              If None, it will use DEFAULT_DDC_HOST constant. Defaults to None.
        """
        
        host = host or DEFAULT_DDC_HOST
        now = round(time.time())

        self.bearer_token = bearer_token
        self.expires_at = now + expires_in
        
        super().__init__(host, False)

    def _set_auth(self):
        self._auth = OAuth2BearerHandler(self.bearer_token, self.expires_at)

        if self._auth.is_expired():
            raise DdcException('BEARER token is expired')
        
    @authorize_s3_access
    def open_growing_season_cube(
        self,
        growing_season_id: int,
        bucket_name: str = DEFAULT_AOI_BUCKET,
        group: str | None = None
        ) -> xr.Dataset:
        """Open growing season cube as an xarray.Dataset.

        Args:
            growing_season_id (int): ID of the growing season.
            bucket_name (str, optional): Name of the S3 bucket where the zarr cube is stored.
                Defaults to `DEFAULT_AOI_BUCKET`.
            group (str, optional): Zarr group of the dataset. Defaults to None.

        Returns:
            xr.Dataset: Growing season dataset.

        Raises:
            DdcClientError: If user don't have access to the bucket.
            DdcRequestError: If an error occurs during opening the cube.

        """

        route = f"/crop-model/growing-seasons/{growing_season_id}"
        accept = "application/json"
        params = {}

        try:
            response = self.request(
                "GET", route, params=params, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't get growing season with id {growing_season_id} with HTTP exception: {error}"
            ) from None
        
        growing_season = response.json()

        route = f"/aoi-manager/aois/{growing_season['aoi_id']}"
        accept = "application/json"
        params = {}

        try:
            response = self.request(
                "GET", route, params=params, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't get AOI with id {growing_season['aoi_id']} with HTTP exception: {error}"
            ) from None
        
        aoi = response.json()

        zarr_path = f"s3://{bucket_name}/{aoi['zarr_id']}"

        try:
            cube = open_cube(path=zarr_path, storage_options=self._aws_s3, group=group)
        except PermissionError as error:
            raise DdcClientError(
                f"User don't have access for this operation: {error}") from None
        except FileNotFoundError as error:
            raise DdcRequestError(
                f"Invalid aoi_id, no such aoi cube: {error}") from None
        except Exception as error:
            raise DdcRequestError(
                f"Couldn't open AOI dataset with id {growing_season['aoi_id']} with HTTP exception: {error}"
            ) from None

        if growing_season["geometry"] is not None and cube.rio.crs is not None:
            cube = clip_cube(cube, growing_season["geometry"])

        return cube


class DdcClient(BaseClient):
    """DdcClient class for interacting with the DDC API. Uses client ID and secret for authentication.

    Attributes:
        client_id (str | None, optional): Danube Data Cube client id.
          If None, it will use DDC_CLIENT_ID env variable. Defaults to None.
        client_secret (str | None, optional): Danube Data Cube client secret.
          If None, it will use DDC_CLIENT_SECRET env variable. Defaults to None.
        host (str | None, optional): Alternative Danube Data Cube host url.
          If None, it will use DEFAULT_DDC_HOST constant. Defaults to None.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        host: str | None = None
        ) -> None:

        """Initializes the DdcClient instance..

        Args:
            client_id (str | None, optional): Danube Data Cube client id.
              If None, it will use DDC_CLIENT_ID env variable. Defaults to None.
            client_secret (str | None, optional): Danube Data Cube client secret.
              If None, it will use DDC_CLIENT_SECRET env variable. Defaults to None.
            host (str | None, optional): Alternative Danube Data Cube host url.
              If None, it will use DEFAULT_DDC_HOST constant. Defaults to None.

        Raises:
            DdcException: If both `client_id` and `client_secret` are not provided.
        """
        client_id = client_id or os.environ.get('DDC_CLIENT_ID')
        client_secret = client_secret or os.environ.get('DDC_CLIENT_SECRET')
        host = host or DEFAULT_DDC_HOST

        if not client_id or not client_secret:
            raise DdcException(
                'both `client_id` and `client_secret` must be provided, '
                'consider setting environment variables '
                'DDC_CLIENT_ID and DDC_CLIENT_SECRET.'
            )
        
        self.client_id = client_id
        self.client_secret = client_secret
        
        super().__init__(host, False)

    def _set_auth(self):
        token = self.fetch_token()
        self._auth = OAuth2BearerHandler(
            token.access_token.get_secret_value(), token.expires_at)

    @authorize_request
    def get_all_aoi(
        self,
        with_geometry: bool = True,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Retrieve all areas of interests (AOI) for the user.

        If both "limit" and "offset" arguments are None, it retrieves all records using paginated requests.

        Args:
            with_geometry (bool, optional): Indicates whether to include geometry data. Defaults to True.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.
              Defaults to None (API will use the default value).

        Returns:
            pd.DataFrame | list[dict]: AOIs information.
            
        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        route = "/aoi-manager/aois"
        accept = "application/json"
        params = {"with_geometry": with_geometry}
        
        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def get_aoi_by_id(
        self,
        aoi_id: int,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Retrieve an areas of interests (AOI) for the user by ID.

        Args:
            aoi_id (int): ID of the AOI.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: AOI information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        route = f"/aoi-manager/aois/{aoi_id}"
        accept = "application/json"
        params = {}

        try:
            response = self.request(
                "GET", route, params=params, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't get AOI with id {aoi_id} with HTTP exception: {error}"
            ) from None
        
        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def create_aoi(
        self,
        name: str,
        geometry: Geometry | Polygon | MultiPolygon | str | dict,
        time_range: TimeRange | tuple[pd.Timestamp, pd.Timestamp] | tuple[str, str],
        layer_selection_id:  int | None = None,
        layer_ids: list[int] | None = None,
        is_dynamic: bool = False,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Create an area of interests (AOI).

        Args:
            name (str): The name of the area of interest.
            geometry (Geometry | Polygon | MultiPolygon | str | dict): The geometry of the area of interest in WGS84 
              coordinate system. This can be provided as a `ddc_utility.Geometry` object, a `shapely.Polygon`, a `shapely.MultiPolygon`, a WKT string or as a GeoJson dict.
            time_range (TimeRange | tuple[pd.Timestamp, pd.Timestamp] | tuple[str, str]):
              The time range for which the area of interest is defined.
              This can be provided as a `ddc_utility.TimeRange` object, a tuple of two `pandas.Timestamp` objects,
              or a tuple of two strings representing dates.
            layer_selection_id (int | None, optional): Layer selection ID. If both,  
              layer_selection_id and layer_ids are provided, only layer_selection_id will be use. Defaults to None.
            layer_ids (list[int] | None, optional): List of layer IDs. If both, layer_selection_id and layer_ids are 
              provided, only layer_selection_id will be use. Defaults to None.
            is_dynamic (bool, optional): Whether the AOI is dynamic (True) or static (False).
                Defaults to False.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: Created AOI information.

        Raises:
            DdcRequestError: If an error occurs during the request process.

        """
        if not isinstance(time_range, TimeRange):
            time_range = TimeRange(*time_range)
        time_range_str = time_range.to_string(only_date=True)

        if not isinstance(geometry, Geometry):
            geometry = Geometry(geometry)

        route = "/aoi-manager/aois"
        accept = "application/json"
        content_type = "application/json"
        data = {
            "name": name,
            "geometry": geometry.to_json(),
            "start_date": time_range_str[0],
            "end_date": time_range_str[1],
            "is_dynamic": is_dynamic
        }
        if layer_selection_id:
            data["layer_selection_id"] = layer_selection_id
        else:
            data["layer_ids"] = layer_ids
        data = json.dumps(data)
        
        try:
            response = self.request(
                "POST", route, data=data, content_type=content_type, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't create AOI with HTTP exception: {error}"
            ) from None

        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def delete_aoi(
        self,
        aoi_id: int
        ) -> pd.DataFrame | list[dict]:
        """Delete AOI.

        Args:
            aoi_id (int): ID of the AOI.

        Returns:
            None.

        Raises:
            DdcRequestError: If an error occurs during the request process.

        """

        route = f"/aoi-manager/aois/{aoi_id}"

        try:
            self.request("DELETE", route)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't create growing season with HTTP exception: {error}"
            ) from None

    @authorize_request
    def get_data_layers(
        self,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Retrieve available data layers.

        If both "limit" and "offset" arguments are None, it retrieves all records using paginated requests.

        Args:
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.
              Defaults to None (API will use the default value).

        Returns:
            pd.DataFrame | list[dict]: Available data layers information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {}
        route = "/aoi-manager/data-layers"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def get_data_selections(
        self,
        data_layer_selection_id: int | None = None,
        layer_ids: list[int] | None = None,
        geometry: Geometry | Polygon | MultiPolygon | str | dict | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Retrieve available data selections.

        If both "limit" and "offset" arguments are None, it retrieves all records using paginated requests.

        Args:
            data_layer_selection_id (int | None, optional): if provided, it returns a custom data selection that only includes those
              data collections containing the data layers specified in the given data layer selection.
            layer_ids (list[int] | None, optional): if provided, it returns a custom data selection that only includes those
              data collections containing the given data layers.
            geometry (Geometry | Polygon | MultiPolygon | str | dict | None, optional): if provided, the data layer selections
             will be filtered not only by the "EU" and "WORLD" geographic identifiers, but also by the country corresponding
             to the given geometry.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.
              Defaults to None (API will use the default value).

        Returns:
            pd.DataFrame | list[dict]: Available data selections information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {}

        if data_layer_selection_id is not None:
            params["collection_id"] = data_layer_selection_id

        if layer_ids is not None:
            params["layer_ids"] = layer_ids

        if (geometry is not None) and (not isinstance(geometry, Geometry)):
            geometry = Geometry(geometry)
            params["geometry"] = geometry.to_string()

        route = "/aoi-manager/data-selections"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_crop_types(
        self,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Retrieve available crop types.

        Args:
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.
              Defaults to None (API will use the default value).

        Returns:
            pd.DataFrame | list[dict]: Available crop types information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {}

        route = "/crop-model/crop-types"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def create_crop_type(
        self,
        crop_type_name: str,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Create crop type.

        Args:
            crop_type_name (str): Name of the crop type.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
             pd.DataFrame | list[dict]: Created crop type information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """
        route = "/crop-model/crop-types"
        accept = "application/json"
        content_type = "application/json"
        data = {
            "name": crop_type_name
        }
        data = json.dumps(data)

        try:
            response = self.request(
                "POST", route, data=data, content_type=content_type, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't create crop type with HTTP exception: {error}"
            ) from None

        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def get_crop_variety(
        self,
        crop_type_id: int,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Retrieve available crop varieties.

        Args:
            crop_type_id (int): ID of crop type.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.
              Defaults to None (API will use the default value).

        Returns:
            pd.DataFrame | list[dict]: Available crop variety information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {}

        route = f"/crop-model/crop-types/{crop_type_id}/varieties"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def create_crop_variety(
        self,
        crop_type_id: id,
        crop_variety_name: str,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Create crop variety for a given crop type.

        Args:
            crop_type_id (id): ID of crop type.
            crop_variety_name (str): Name of the crop variety.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: Created crop variety information.

        Raises:
            DdcRequestError: If an error occurs during the request process.

        """
        route = "/crop-model/crop-varieties"
        accept = "application/json"
        content_type = "application/json"
        data = {
            "crop_type_id": crop_type_id,
            "name": crop_variety_name
        }
        data = json.dumps(data)

        try:
            response = self.request(
                "POST", route, data=data, content_type=content_type, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't create crop variety with HTTP exception: {error}"
            ) from None

        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def get_crop_models(
        self,
        crop_type_id: int | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Retrieve available crop model list.

        Args:
            crop_type_id (int | None, optional): ID used to filter by the specified crop type.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.
              Defaults to None (API will use the default value).

        Returns:
            pd.DataFrame | list[dict]: Available crop models information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {'crop_type_id': crop_type_id}

        route = "/crop-model/crop-models"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_cube_meta_data_by_aoi(
        self,
        aoi_id: int,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Retrieve meta data of the specified data-cube.

        Args:
            aoi_id (int): ID of the AOI to specify the data-cube.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: Available meta data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {}

        route = f"/data-cube/cube/meta/by-aoi/{aoi_id}"
        accept = "application/json"

        try:
            response = self.request(
                "GET", route, params=params, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't get data with AOI id {aoi_id} with HTTP exception: {error}"
            ) from None
        
        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_cube_meta_data_by_growing_season(
        self,
        gs_id: int,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Retrieve meta data of the specified data-cube.

        Args:
            gs_id (int): ID of the growing season to specify the data-cube.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: Available meta data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {}

        route = f"/data-cube/cube/meta/by-growing-season/{gs_id}"
        accept = "application/json"

        try:
            response = self.request(
                "GET", route, params=params, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't get data with growing season id {gs_id} with HTTP exception: {error}"
            ) from None
        
        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_cube_data_by_aoi(
        self,
        aoi_id: int,
        data_var: str,
        date: pd.Timestamp | str | None,
        zone: bool = False,
        geometry_type: str = "Polygon",
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Retrieve data from the specified data-cube.

        Args:
            aoi_id (int): ID of the AOI to specify the data-cube.
            data_var (str): Name of the data variable
            date (Timestamp | str | None): Date used to narrow the dataset
            zone (bool): If True, returns zones instead of polygons (works with "Polygon" type geometry)
            geometry_type (string): Specify the type of the returned geometries
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: Available data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {
            "data_var": data_var,
            "date": date,
            "zone": zone,
            "geometry_type": geometry_type
        }

        route = f"/data-cube/cube/data/by-aoi/{aoi_id}"
        accept = "application/json"

        try:
            response = self.request(
                "GET", route, params=params, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't get data with AOI id {aoi_id} with HTTP exception: {error}"
            ) from None
        
        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_cube_data_by_growing_season(
        self,
        gs_id: int,
        data_var: str,
        date: pd.Timestamp | str | None,
        zone: bool = False,
        geometry_type: str = "Polygon",
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Retrieve data from the specified data-cube.

        Args:
            gs_id (int): ID of the growing season to specify the data-cube.
            data_var (str): Name of the data variable
            date (Timestamp | str | None): Date used to narrow the dataset
            zone (bool): If True, returns zones instead of polygons (works with "Polygon" type geometry)
            geometry_type (string): Specify the type of the returned geometries
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: Available data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {
            "data_var": data_var,
            "date": date,
            "zone": zone,
            "geometry_type": geometry_type
        }

        route = f"/data-cube/cube/data/by-growing-season/{gs_id}"
        accept = "application/json"

        try:
            response = self.request(
                "GET", route, params=params, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't get data with growing season id {gs_id} with HTTP exception: {error}"
            ) from None
        
        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_time_series_avg_by_aoi(
        self,
        aoi_id: int,
        data_layer: str,
        start_date: pd.Timestamp | str | None = None,
        end_date: pd.Timestamp | str | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Returns a time series contains the average values of the selected layer for the given AOI.

        Args:
            aoi_id (int): ID of the AOI.
            data_layer (str): Name of the data layer
            start_date (Timestamp | str | None): Start date used to narrow the dataset
            end_date (Timestamp | str | None): Start date used to narrow the dataset
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.

        Returns:
            pd.DataFrame | list[dict]: Available data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {
            "data_layer": data_layer,
            "start_date": start_date,
            "end_date": end_date
        }

        route = f"/data-cube/time-series/avg/by-aoi/{aoi_id}"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_time_series_avg_by_growing_season(
        self,
        gs_id: int,
        data_layer: str,
        start_date: pd.Timestamp | str | None = None,
        end_date: pd.Timestamp | str | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Returns a time series contains the average values of the selected layer for the given growing season.

        Args:
            gs_id (int): ID of the growing season.
            data_layer (str): Name of the data layer
            start_date (Timestamp | str | None): Start date used to narrow the dataset
            end_date (Timestamp | str | None): Start date used to narrow the dataset
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.

        Returns:
            pd.DataFrame | list[dict]: Available data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {
            "data_layer": data_layer,
            "start_date": start_date,
            "end_date": end_date
        }

        route = f"/data-cube/time-series/avg/by-growing-season/{gs_id}"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def get_weather_historic_by_aoi(
        self,
        aoi_id: int,
        start_date: pd.Timestamp | str | None = None,
        end_date: pd.Timestamp | str | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Returns historic weather data for the given AOI.

        Args:
            aoi_id (int): ID of the AOI.
            start_date (Timestamp | str | None): Start date used to narrow the dataset
            end_date (Timestamp | str | None): Start date used to narrow the dataset
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.

        Returns:
            pd.DataFrame | list[dict]: Available data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {
            "start_date": start_date,
            "end_date": end_date
        }

        route = f"/data-cube/weather/historic/by-aoi/{aoi_id}"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_weather_historic_by_growing_season(
        self,
        gs_id: int,
        start_date: pd.Timestamp | str | None = None,
        end_date: pd.Timestamp | str | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Returns historic weather data for the given growing season.

        Args:
            gs_id (int): ID of the growing season .
            start_date (Timestamp | str | None): Start date used to narrow the dataset
            end_date (Timestamp | str | None): Start date used to narrow the dataset
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.

        Returns:
            pd.DataFrame | list[dict]: Available data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {
            "start_date": start_date,
            "end_date": end_date
        }

        route = f"/data-cube/weather/historic/by-growing-season/{gs_id}"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_weather_historic_by_location(
        self,
        lat: float,
        lon: float,
        start_date: pd.Timestamp | str | None = None,
        end_date: pd.Timestamp | str | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Returns historic weather data for the given location.

        Args:
            lat (float): Latitude
            lon (float): Longitude
            start_date (Timestamp | str | None): Start date used to narrow the dataset
            end_date (Timestamp | str | None): Start date used to narrow the dataset
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.

        Returns:
            pd.DataFrame | list[dict]: Available data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {
            "lat": lat,
            "lon": lon,
            "start_date": start_date,
            "end_date": end_date
        }

        route = "/data-cube/weather/historic/by-location"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def get_weather_aggregated_by_aoi(
        self,
        aoi_id: int,
        crop_type: str,
        start_date: pd.Timestamp | str | None = None,
        end_date: pd.Timestamp | str | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Returns aggregated historic weather data for the given AOI.

        Args:
            aoi_id (int): ID of the AOI.
            crop_type (str): Name of the crop type
            start_date (Timestamp | str | None): Start date used to narrow the dataset
            end_date (Timestamp | str | None): Start date used to narrow the dataset
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.

        Returns:
            pd.DataFrame | list[dict]: Available data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {
            "crop_type": crop_type,
            "start_date": start_date,
            "end_date": end_date
        }

        route = f"/data-cube/weather/aggregated/by-aoi/{aoi_id}"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_weather_aggregated_by_growing_season(
        self,
        gs_id: int,
        crop_type: str,
        start_date: pd.Timestamp | str | None = None,
        end_date: pd.Timestamp | str | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Returns aggregated historic weather data for the given growing season.

        Args:
            gs_id (int): ID of the growing season.
            crop_type (str): Name of the crop type
            start_date (Timestamp | str | None): Start date used to narrow the dataset
            end_date (Timestamp | str | None): Start date used to narrow the dataset
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.

        Returns:
            pd.DataFrame | list[dict]: Available data information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        params = {
            "crop_type": crop_type,
            "start_date": start_date,
            "end_date": end_date
        }

        route = f"/data-cube/weather/aggregated/by-growing-season/{gs_id}"
        accept = "application/json"

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def run_crop_model(
        self,
        growing_season_id: int,
        init_water_content: float | None = None,
        soil_type: str | None = None,
        irrigation: list[tuple] | None = None,
        simulation: int = 0,
        use_calibration: bool = True,
        return_growth_stages: bool = False,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """
        Run crop model.

        Args:
            growing_season_id (int): ID of the growing season.
            init_water_content (float | None, optional): Initial water content for the simulation.
            soil_type (str | None, optional): USDA soil type definition  
            irrigation (list | None, optional): Irrigation schedule for the simulation in [(date, value), ... ,(date, 
              value)] format. Dates are expecetd to be in YYYY-mm-dd format. Values are in mm. 
            simulation: (int): type of simulation (0: average, 1: best, 2: worst)
            use_calibration (bool): whether calibration data should be used
            return_growth_stages: whether the result should contains the growing steps
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: Crop model run information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        route = "/crop-model/run/yield"
        accept = "application/json"
        content_type = "application/json"

        data = {
            "growing_season_id": growing_season_id,
            "use_calibration": use_calibration,
            "return_growth_stages": return_growth_stages
        }

        if init_water_content is not None:
            data["init_water_content"] = init_water_content

        if soil_type is not None:
            data["soil_type"] = soil_type

        if irrigation is not None:
            irrigation_list = []
            for entry in irrigation:
                irrigation_list.append({
                    "date": entry[0],
                    "depth": entry[1]
                })
            data["irrigation"] = irrigation_list

        if simulation is not None:
            data["simulation"] = simulation

        data = json.dumps(data)

        try:
            response = self.request(
                "POST", route, data=data, content_type=content_type, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't run crop model with HTTP exception: {error}"
            ) from None

        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def run_crop_model_yield_potential(
        self,
        growing_season_id: int,
        init_water_content: float | None = None,
        soil_type: str | None = None,
        irrigation: list[tuple] | None = None,
        use_calibration: bool = True,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """
        Run yield potential crop model function.

        Args:
            growing_season_id (int): ID of the growing season.
            init_water_content (float | None, optional): Initial water content for the simulation.
            soil_type (str | None, optional): USDA soil type definition  
            irrigation (list | None, optional): Irrigation schedule for the simulation in [(date, value), ... ,(date, 
              value)] format. Dates are expecetd to be in YYYY-mm-dd format. Values are in mm. 
            use_calibration (bool): whether calibration data should be used
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: Crop model run information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        route = "/crop-model/run/yield-potential"
        accept = "application/json"
        content_type = "application/json"

        data = {
            "growing_season_id": growing_season_id,
            "use_calibration": use_calibration,
        }

        if init_water_content is not None:
            data["init_water_content"] = init_water_content

        if soil_type is not None:
            data["soil_type"] = soil_type

        if irrigation is not None:
            irrigation_list = []
            for entry in irrigation:
                irrigation_list.append({
                    "date": entry[0],
                    "depth": entry[1]
                })
            data["irrigation"] = irrigation_list

        data = json.dumps(data)

        try:
            response = self.request(
                "POST", route, data=data, content_type=content_type, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't run crop model with HTTP exception: {error}"
            ) from None

        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def get_growing_season(
        self,
        aoi_id: int | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME,
        limit: int | None = None,
        offset: int | None = None
        ) -> pd.DataFrame | list[dict]:
        """Retrieve growing seasons for AOI.

        Args:
            aoi_id (int | None, optional): ID of the AOI to filter
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.
            limit (int | None, optional): Maximum number of records to retrieve. Defaults to None (API will use the default value).
            offset (int | None, optional): Number of records to skip before starting to collect the result set.
              Defaults to None (API will use the default value).

        Returns:
            pd.DataFrame | list[dict]: Growing season information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        route = "/crop-model/growing-seasons"
        accept = "application/json"
        params = {'aoi_id': aoi_id}

        result = self._get_paginated_list(route, params, accept, limit, offset)

        return self._process_response(result, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def get_growing_season_by_id(
        self,
        growing_season_id: int,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Retrieve an growing season for the user by ID.

        Args:
            growing_season_id (int): ID of the growing season.
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: growing season information.

        Raises:
            DdcRequestError: If an error occurs during the request process.
        """

        route = f"/crop-model/growing-seasons/{growing_season_id}"
        accept = "application/json"
        params = {}

        try:
            response = self.request(
                "GET", route, params=params, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't get growing season with id {growing_season_id} with HTTP exception: {error}"
            ) from None
        
        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))

    @authorize_request
    def create_growing_season(
        self,
        aoi_id: int,
        time_range: TimeRange | tuple[pd.Timestamp, pd.Timestamp] | tuple[str, str],
        sowing_date: pd.Timestamp | str,
        crop_type_id: int,
        crop_variety_id: int,
        crop_model_id: int,
        name: str,
        geometry: Geometry | Polygon | MultiPolygon | str | dict,
        crop_yield: float = 0.0,
        insured_yield: float = 0.0,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Create growing season for AOI.

        Args:
            aoi_id (int): ID of the AOI.
            time_range (TimeRange | tuple[pd.Timestamp, pd.Timestamp] | tuple[str, str]):
                The time range for which the growing season is defined.
                This can be provided as a `ddc_utility.TimeRange` object, a tuple of two `pandas.Timestamp` objects,
                or a tuple of two strings representing dates.
            sowing_date (pd.Timestamp | str): The date when the crop is sown.
            crop_type_id (int): ID of crop type.
            crop_variety_id (int): ID of crop variety.
            crop_model_id (int): ID of crop model.
            name (str): name of the growing season
            geometry (Geometry | Polygon | MultiPolygon | str | dict): The geometry of the growing season in WGS84 
              coordinate system. This can be provided as a `ddc_utility.Geometry` object, a `shapely.Polygon`,
              a `shapely.MultiPolygon`, a WKT string or as a GeoJson dict. Must be within the parent AOI's geometry.
            crop_yield (float, optional): Amount of crop yield (default is 0)
            insured_yield (float, optional): Amount of insured yield (default is 0)
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: Created growing season information.

        Raises:
            DdcRequestError: If an error occurs during the request process.

        """

        if not isinstance(time_range, TimeRange):
            time_range = TimeRange(*time_range)
        time_range_str = time_range.to_string(only_date=True)

        if not isinstance(sowing_date, pd.Timestamp):
            sowing_date = pd.Timestamp(sowing_date)
        sowing_date_str = sowing_date.isoformat(sep='T').split('T')[0]

        if not isinstance(geometry, Geometry):
            geometry = Geometry(geometry)

        route = "/crop-model/growing-seasons"
        accept = "application/json"
        content_type = "application/json"
        data = {
            "aoi_id": aoi_id,
            "start_date": time_range_str[0],
            "end_date": time_range_str[1],
            "sowing_date": sowing_date_str,
            "crop_type_id": crop_type_id,
            "crop_variety_id": crop_variety_id,
            "crop_model_id": crop_model_id,
            "name": name,
            "geometry": geometry.to_json(),
            "crop_yield": crop_yield,
            "insured_yield": insured_yield
        }
        data = json.dumps(data)

        try:
            response = self.request(
                "POST", route, data=data, content_type=content_type, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't create growing season with HTTP exception: {error}"
            ) from None

        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def update_growing_season(
        self,
        growing_season_id: int,
        time_range: TimeRange | tuple[pd.Timestamp, pd.Timestamp] | tuple[str, str],
        sowing_date: pd.Timestamp | str,
        crop_type_id: int,
        crop_variety_id: int,
        crop_model_id: int,
        name: str,
        geometry: Geometry | Polygon | MultiPolygon | str | dict,
        crop_yield: float | None = None,
        output_data_type: ReturnType | int = ReturnType.DATAFRAME
        ) -> pd.DataFrame | list[dict]:
        """Update growing season.

        Args:
            growing_season_id (int): ID of the growing season.
            time_range (TimeRange | tuple[pd.Timestamp, pd.Timestamp] | tuple[str, str]):
                The time range for which the growing season is defined.
                This can be provided as a `ddc_utility.TimeRange` object, a tuple of two `pandas.Timestamp` objects,
                or a tuple of two strings representing dates.
            sowing_date (pd.Timestamp | str): The date when the crop is sown.
            crop_type_id (int): ID of crop type.
            crop_variety_id (int): ID of crop variety.
            crop_model_id (int): ID of crop model.
            name (str): name of the growing season
            geometry (Geometry | Polygon | MultiPolygon | str | dict): The geometry of the growing season in WGS84 
              coordinate system. This can be provided as a `ddc_utility.Geometry` object, a `shapely.Polygon`,
              a `shapely.MultiPolygon`, a WKT string or as a GeoJson dict. Must be within the parent AOI's geometry.
            crop_yield (float, optional): Amount of crop yield (default is None)
            output_data_type (ReturnType | int, optional): Specifies the format of the returned data,
              either as a pandas.DataFrame (ReturnType.DATAFRAME) or a list of dictionaries (ReturnType.DICT).
              Defaults to ReturnType.DATAFRAME.

        Returns:
            pd.DataFrame | list[dict]: Created growing season information.

        Raises:
            DdcRequestError: If an error occurs during the request process.

        """

        if not isinstance(time_range, TimeRange):
            time_range = TimeRange(*time_range)
        time_range_str = time_range.to_string(only_date=True)

        if not isinstance(sowing_date, pd.Timestamp):
            sowing_date = pd.Timestamp(sowing_date)
        sowing_date_str = sowing_date.isoformat(sep='T').split('T')[0]

        if not isinstance(geometry, Geometry):
            geometry = Geometry(geometry)

        route = f"/crop-model/growing-seasons/{growing_season_id}"
        accept = "application/json"
        content_type = "application/json"
        data = {
            "start_date": time_range_str[0],
            "end_date": time_range_str[1],
            "sowing_date": sowing_date_str,
            "crop_type_id": crop_type_id,
            "crop_variety_id": crop_variety_id,
            "crop_model_id": crop_model_id,
            "name": name,
            "geometry": geometry.to_json()
        }

        if crop_yield is not None:
            data["crop_yield"] = crop_yield

        data = json.dumps(data)

        try:
            response = self.request(
                "PATCH", route, data=data, content_type=content_type, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't update growing season with HTTP exception: {error}"
            ) from None

        return self._process_response_json(response, output_data_type_map.get(output_data_type, ReturnType.DATAFRAME))
    
    @authorize_request
    def delete_growing_season(
        self,
        growing_season_id: int
        ) -> pd.DataFrame | list[dict]:
        """Delete growing season.

        Args:
            growing_season_id (int): ID of the growing season.

        Returns:
            None.

        Raises:
            DdcRequestError: If an error occurs during the request process.

        """

        route = f"/crop-model/growing-seasons/{growing_season_id}"

        try:
            self.request("DELETE", route)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't create growing season with HTTP exception: {error}"
            ) from None

    @authorize_s3_access
    def open_aoi_cube(
        self,
        aoi_id: int,
        bucket_name: str = DEFAULT_AOI_BUCKET,
        group: str | None = None
        ) -> xr.Dataset:
        """Open AOI cube as an xarray.Dataset.

        Args:
            aoi_id (int): ID of the AOI.
            bucket_name (str, optional): Name of the S3 bucket where the zarr cube is stored.
                Defaults to `DEFAULT_AOI_BUCKET`.
            group (str, optional): Zarr group of the dataset. Defaults to None.

        Returns:
            xr.Dataset: AOI dataset.

        Raises:
            DdcClientError: If user don't have access to the bucket.
            DdcRequestError: If an error occurs during opening the cube.

        """

        zarr_path = f"s3://{bucket_name}/{aoi_id}_{self.client_id}.zarr"

        try:
            cube = open_cube(path=zarr_path, storage_options=self._aws_s3, group=group)
        except PermissionError as error:
            raise DdcClientError(
                f"User don't have access for this operation: {error}") from None
        except FileNotFoundError as error:
            raise DdcRequestError(
                f"Invalid aoi_id, no such aoi cube: {error}") from None
        except Exception as error:
            raise DdcRequestError(
                f"Couldn't open AOI dataset with id {aoi_id} with HTTP exception: {error}"
            ) from None
        return cube

    @authorize_s3_access
    def open_ddc_cube(
        self,
        zarr_path: str,
        zarr_group: str | None = None,
        bucket_name: str = DEFAULT_DDC_BUCKET
        ) -> xr.Dataset:
        """Open DDC dataset as an xarray.Dataset.

        Args:
            zarr_path (str): Zarr path to the dataset.
            zarr_group (str, optional): Zarr group of the dataset.
            bucket_name (str, optional): Name of the S3 bucket where the zarr cube is stored.
                Defaults to `DEFAULT_DDC_BUCKET`.

        Returns:
            xr.Dataset: DDC dataset.

        Raises:
            DdcClientError: If user don't have access to the bucket.
            DdcRequestError: If an error occurs during opening the cube.
        """

        zarr_path = f"s3://{bucket_name}/{zarr_path}"

        try:
            cube = open_cube(path=zarr_path,
                             storage_options=self._aws_s3,
                             group=zarr_group)
        except PermissionError as error:
            raise DdcClientError(
                f"User don't have access for this operation: {error}") from None
        except Exception as error:
            raise DdcRequestError(
                f"Couldn't open DDC dataset with HTTP exception: {error}"
            ) from None
        return cube
    
    @authorize_s3_access
    def open_growing_season_cube(
        self,
        growing_season_id: int,
        bucket_name: str = DEFAULT_AOI_BUCKET,
        group: str | None = None
        ) -> xr.Dataset:
        """Open growing season cube as an xarray.Dataset.

        Args:
            growing_season_id (int): ID of the growing season.
            bucket_name (str, optional): Name of the S3 bucket where the zarr cube is stored.
                Defaults to `DEFAULT_AOI_BUCKET`.
            group (str, optional): Zarr group of the dataset. Defaults to None.

        Returns:
            xr.Dataset: Growing season dataset.

        Raises:
            DdcClientError: If user don't have access to the bucket.
            DdcRequestError: If an error occurs during opening the cube.

        """

        route = f"/crop-model/growing-seasons/{growing_season_id}"
        accept = "application/json"
        params = {}

        try:
            response = self.request(
                "GET", route, params=params, accept=accept)

        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't get growing season with id {growing_season_id} with HTTP exception: {error}"
            ) from None
        
        growing_season = response.json()

        zarr_path = f"s3://{bucket_name}/{growing_season['aoi_id']}_{self.client_id}.zarr"

        try:
            cube = open_cube(path=zarr_path, storage_options=self._aws_s3, group=group)
        except PermissionError as error:
            raise DdcClientError(
                f"User don't have access for this operation: {error}") from None
        except FileNotFoundError as error:
            raise DdcRequestError(
                f"Invalid aoi_id, no such aoi cube: {error}") from None
        except Exception as error:
            raise DdcRequestError(
                f"Couldn't open AOI dataset with id {growing_season['aoi_id']} with HTTP exception: {error}"
            ) from None

        if growing_season["geometry"] is not None and cube.rio.crs is not None:
            cube = clip_cube(cube, growing_season["geometry"])

        return cube
    
    def fetch_token(self) -> AccesToken:
        """Fetch token from a remote token endpoint."""
    
        def custom_serializer(obj):
            if isinstance(obj, SecretStr):
                return obj.get_secret_value()  # Convert datetime to string
            raise TypeError(f"Type {type(obj)} not serializable")
        
        route = "/token-manager/get-token"
        accept = "application/json"
        content_type = "application/json"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        data = json.dumps(data, default=custom_serializer)

        try:
            response = self.request(
                "POST", route, data=data, content_type=content_type, accept=accept)
        except HTTPException as error:
            raise DdcRequestError(f"Couldn't fetch token with HTTP exception: {error}") from None

        result = response.json()
        token = AccesToken(**result)

        return token

    def _process_response_json(self, response: requests.Response, output_data_type: ReturnType):
        
        data = response.json()

        if output_data_type == ReturnType.DATAFRAME:
            if isinstance(data, list):
                return pd.DataFrame(data)
            if isinstance(data, dict):
                return pd.DataFrame([data])
            else:
                raise ValueError(
                    f"Can't post-process API response -- {type(data)} is invalid with output_data_type of {output_data_type}")
        else:
            return data
        
    def _process_response(self, json_response: list | dict, output_data_type: ReturnType):

        if output_data_type == ReturnType.DATAFRAME:
            if isinstance(json_response, list):
                return pd.DataFrame(json_response)
            if isinstance(json_response, dict):
                return pd.DataFrame([json_response])
            else:
                raise ValueError(
                    f"Can't post-process API response -- {type(json_response)} is invalid with output_data_type of {output_data_type}")
        else:
            return json_response
        
    def _get_paginated_list(self, route: str, params: dict, accept = "application/json", limit: int | None = None, offset: int | None = None) -> list:
        
        if limit is not None:
            params["limit"] = limit

        if offset is not None:
            params["offset"] = offset
        
        try:
            response = self.request("GET", route, params=params, accept=accept).json()
        except HTTPException as error:
            raise DdcRequestError(
                f"Couldn't get data with HTTP exception: {error}"
            ) from None

        if ("items" not in response) or not isinstance(response["items"], list):
            raise DdcClientError(f"Invalid 'items' property in paginated response at route '{route}'")
        
        if (limit is not None or offset is not None) or len(response["items"]) == 0:
            return response["items"]

        if ("total" not in response) or not isinstance(response["total"], int):
            raise DdcClientError(f"Invalid 'total' property in paginated response at route '{route}'")
        
        total = response["total"]
        result = response["items"]
        limit = response["limit"]
        offset = response["offset"]
        params["limit"] = limit

        while offset + limit < total:
            
            offset += limit
            params["offset"] = offset

            try:
                response = self.request("GET", route, params=params, accept=accept).json()
            except HTTPException as error:
                raise DdcRequestError(
                    f"Couldn't get data layers with HTTP exception: {error}"
                ) from None
            
            result.extend(response["items"])

        return result
    