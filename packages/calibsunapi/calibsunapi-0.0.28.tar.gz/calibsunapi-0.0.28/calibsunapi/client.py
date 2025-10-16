"""Main module for the Calibsun API client."""
import json
import logging
import os
from datetime import datetime, time, timedelta, timezone
from io import BytesIO
from typing import Any, Optional, Union

import requests

from calibsunapi.decorators import requires_authentication
from calibsunapi.endpoints import EndpointRoutes
from calibsunapi.exceptions import NoCredentialsError
from calibsunapi.models.listplants import Plant
from calibsunapi.models.uploadmeasurements import UploadLinkMeasurementsResponse, UploadMeasurementsFormats
from calibsunapi.token import Token
from calibsunapi.utils import format_time


class CalibsunApiClient:
    """Main class for the Calibsun API client."""

    _token: Union[Token, None] = None

    def __init__(self, calibsun_client_id: Union[str, None] = None, calibsun_client_secret: Union[str, None] = None):
        """
        Initializes the client with the provided client ID and client secret.
        If the client ID and client secret are not provided, the method attempts to
        retrieve them from the environment variables 'CALIBSUN_CLIENT_ID' and
        'CALIBSUN_CLIENT_SECRET', respectively. If neither is found, a warning is logged.
        Args:
            calibsun_client_id (Union[str, None], optional): The client ID for Calibsun.
                Defaults to None.
            calibsun_client_secret (Union[str, None], optional): The client secret for
                Calibsun. Defaults to None.
        Attributes:
            calibsun_client_id (str or None): The client ID for Calibsun.
            calibsun_client_secret (str or None): The client secret for Calibsun.
        """

        self.calibsun_client_id = os.getenv("CALIBSUN_CLIENT_ID", calibsun_client_id)
        self.calibsun_client_secret = os.getenv("CALIBSUN_CLIENT_SECRET", calibsun_client_secret)
        if self.calibsun_client_id is None:
            logging.warning("CALIBSUN_CLIENT_ID not supplied.")
        if self.calibsun_client_secret is None:
            logging.warning("CALIBSUN_CLIENT_SECRET not supplied.")

    def _authenticate(self):
        if self.calibsun_client_id is None or self.calibsun_client_secret is None:
            raise NoCredentialsError()
        response = requests.post(
            EndpointRoutes.TOKEN,
            json={
                "client_id": self.calibsun_client_id,
            },
            headers={"x-api-key": self.calibsun_client_secret},
        )
        response.raise_for_status()
        logging.info("Succesfully authenticated with Calibsun API.")
        self._token = Token(**response.json())

    @property
    def _auth_headers(self) -> dict[str, str]:
        if self.token is not None:
            return {"Authorization": f"Bearer {self.token.access_token}"}
        else:
            return {}

    @property
    def token(self) -> Token:
        if self._token is None or self._token.is_expired():
            self._authenticate()
        return self._token

    def _get(self, *args, **kwargs):
        return requests.get(*args, **kwargs, headers=self._auth_headers)

    def _get_no_auth(self, *args, **kwargs):
        return requests.get(*args, **kwargs)

    def _post(self, *args, **kwargs):
        return requests.post(*args, **kwargs, headers=self._auth_headers)

    def _get_upload_parameters(
        self, site_id: str, format: UploadMeasurementsFormats
    ) -> UploadLinkMeasurementsResponse:
        response = self._get(EndpointRoutes.UPLOAD.format(site_id=site_id, format=format))
        response.raise_for_status()
        return UploadLinkMeasurementsResponse(**response.json())

    @requires_authentication
    def list_plants(self) -> list[Plant]:
        """
        Retrieve a list of plants from the API.

        This method sends a GET request to the LISTPLANT endpoint and returns a list of Plant objects.

        Returns:
            list[Plant]: A list of Plant objects retrieved from the API.

        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        response = self._get(EndpointRoutes.LISTPLANT)
        response.raise_for_status()
        return [
            Plant(
                site_id=plant.get("site_id"),
                **plant.get("site_configuration").get("site_characteristics"),
                client=self,
            )
            for plant in response.json()
        ]

    @requires_authentication
    def push_measurements(
        self,
        site_id: str,
        format: UploadMeasurementsFormats = UploadMeasurementsFormats.JSON,
        filepath: Optional[str] = None,
        data: Optional[Any] = None,
    ) -> requests.Response:
        """
        Push measurements to the specified site.
        Args:
            site_id (str): The ID of the site to which the measurements will be uploaded.
            format (UploadMeasurementsFormats, optional): The format of the upload. Defaults to UploadMeasurementsFormats.JSON.
            filepath (Optional[str], optional): The path to the file containing the measurements. Defaults to None.
            data (Optional[Any], optional): The data to be uploaded if no file is provided. Defaults to None.
        Returns:
            requests.Response: The response from the server after attempting to upload the measurements.
        Raises:
            HTTPError: If the upload fails and the server returns an HTTP error.
            NotAuthenticatedError: If the client is not authenticated.
            ValueError: If both filepath and data are provided or if neither is provided
        """
        if None not in [filepath, data]:
            raise ValueError("Either filepath or data must be provided, but not both.")
        if filepath is not None:
            filelike = open(filepath, "r")
        elif data is not None:
            filelike = BytesIO()
            filelike.write(json.dumps(data).encode("utf-8"))
            filelike.seek(0)
        else:
            raise ValueError("Either filepath or data argument must be provided.")
        parameters = self._get_upload_parameters(site_id, format)
        reponse = requests.post(url=parameters.url, files={"file": filelike}, data=parameters.fields)
        reponse.raise_for_status()
        return reponse

    @requires_authentication
    def get_latest_forecast(self, site_id: str, target: str, run_tag: Optional[str] = None) -> dict:
        """
        Retrieve the latest forecast for a given site and target.
        Args:
            site_id (str): The identifier of the site for which the forecast is requested.
            target (str): The target parameter for the forecast.
            run_tag (Optional[str], optional): An optional run tag to filter the forecast. Defaults to None.
        Returns:
            dict: A dictionary containing the latest forecast data.
        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
            NotAuthenticatedError: If the client is not authenticated.
        """
        params = {"run_tag": run_tag} if run_tag is not None else {}
        response = self._get(EndpointRoutes.LATESTFORECAST.format(site_id=site_id, target=target), params=params)
        response.raise_for_status()
        return response.json()

    @requires_authentication
    def get_latest_forecast_probabilistic(self, site_id: str, target: str, run_tag: Optional[str] = None) -> dict:
        """
        Retrieve the latest probabilistic forecast for a given site and target.
        Args:
            site_id (str): The identifier of the site for which to retrieve the forecast.
            target (str): The target parameter for the forecast.
            run_tag (Optional[str], optional): An optional run tag to filter the forecast. Defaults to None.
        Returns:
            dict: A dictionary containing the latest probabilistic forecast data.
        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
            NotAuthenticatedError: If the client is not authenticated.
        """
        params = {"run_tag": run_tag} if run_tag is not None else {}
        response = self._get(EndpointRoutes.LATESTFORECAST_PROBA.format(site_id=site_id, target=target), params=params)
        response.raise_for_status()
        return response.json()

    @requires_authentication
    def get_latest_forecast_deterministic(self, site_id: str, target: str, run_tag: Optional[str] = None) -> dict:
        """
        Fetches the latest deterministic forecast for a given site and target.
        Args:
            site_id (str): The identifier of the site for which the forecast is requested.
            target (str): The target parameter for the forecast.
            run_tag (Optional[str], optional): An optional run tag to filter the forecast. Defaults to None.
        Returns:
            dict: A dictionary containing the latest deterministic forecast data.
        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
            NotAuthenticatedError: If the client is not authenticated.
        """
        params = {"run_tag": run_tag} if run_tag is not None else {}
        response = self._get(EndpointRoutes.LATESTFORECAST_DET.format(site_id=site_id, target=target), params=params)
        response.raise_for_status()
        return response.json()

    def get_latest_forecast_demo(self, target: str) -> dict:
        """
        Fetches the latest forecast demo for a given target.
        Args:
            target (str): The target for which to fetch the latest forecast demo.
        Returns:
            dict: The latest forecast demo data in JSON format.
        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
            NotAuthenticatedError: If the client is not authenticated.
        """
        response = self._get_no_auth(EndpointRoutes.LATESTFORECASTDEMO.format(target=target))
        response.raise_for_status()
        return response.json()

    def get_latest_forecast_demo_probabilistic(self, target: str) -> dict:
        """
        Fetches the latest probabilistic forecast demo for a given target.
        Args:
            target (str): The target for which to fetch the forecast.
        Returns:
            dict: The JSON response from the API containing the forecast data.
        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        response = self._get_no_auth(EndpointRoutes.LATESTFORECASTDEMO_PROBA.format(target=target))
        response.raise_for_status()
        return response.json()

    def get_latest_forecast_demo_deterministic(self, target: str) -> dict:
        """
        Fetches the latest deterministic forecast demo for a given target.
        Args:
            target (str): The target for which to fetch the latest deterministic forecast demo.
        Returns:
            dict: The JSON response from the API containing the latest deterministic forecast demo.
        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
        """
        response = self._get_no_auth(EndpointRoutes.LATESTFORECASTDEMO_DET.format(target=target))
        response.raise_for_status()
        return response.json()

    @requires_authentication
    def get_forecast(self, forecast_time: time, site_id: str, target: str, run_tag: Optional[str] = None) -> dict:
        """
        Retrieve the forecast for a specific time at the current day, site, and target.

        Args:
            forecast_time (time): The time for which the forecast is requested.
            site_id (str): The identifier of the site for which the forecast is requested.
            target (str): The target parameter for the forecast.
            run_tag (Optional[str], optional): An optional run tag to filter the forecast. Defaults to None.
        Returns:
            dict: The forecast data in JSON format.

        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
            NotAuthenticatedError: If the client is not authenticated.
        """
        forecast_time = format_time(forecast_time)
        params = {"run_tag": run_tag} if run_tag is not None else {}
        response = self._get(
            EndpointRoutes.FIXEDTIMEFORECAST.format(time=forecast_time, site_id=site_id, target=target), params=params
        )
        response.raise_for_status()
        return response.json()

    @requires_authentication
    def get_deterministic_forecast(
        self, forecast_time: time, site_id: str, target: str, run_tag: Optional[str] = None
    ) -> dict:
        """
        Retrieves a deterministic forecast for a specific site and target at a given forecast time for the current day.

        Args:
            forecast_time (time): The time for which the forecast is requested.
            site_id (str): The identifier of the site for which the forecast is requested.
            target (str): The target parameter for the forecast.
            run_tag (Optional[str], optional): An optional run tag to filter the forecast. Defaults to None.
        Returns:
            dict: The JSON response from the API containing the deterministic forecast data.

        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
            NotAuthenticatedError: If the client is not authenticated.
        """
        forecast_time = format_time(forecast_time)
        params = {"run_tag": run_tag} if run_tag is not None else {}
        response = self._get(
            EndpointRoutes.FIXEDTIMEFORECAST_DET.format(time=forecast_time, site_id=site_id, target=target),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    @requires_authentication
    def get_probabilistic_forecast(
        self, forecast_time: time, site_id: str, target: str, run_tag: Optional[str] = None
    ) -> dict:
        """
        Retrieve a probabilistic forecast for a specific site and target at a given forecast time for the current day.
        Args:
            forecast_time (time): The time for which the forecast is requested.
            site_id (str): The identifier of the site for which the forecast is requested.
            target (str): The target variable for the forecast (e.g., temperature, wind speed).
            run_tag (Optional[str], optional): An optional run tag to filter the forecast. Defaults to None.
        Returns:
            dict: A dictionary containing the probabilistic forecast data.
        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
            NotAuthenticatedError: If the client is not authenticated.
        """

        forecast_time = format_time(forecast_time)
        params = {"run_tag": run_tag} if run_tag is not None else {}
        response = self._get(
            EndpointRoutes.FIXEDTIMEFORECAST_PROBA.format(time=forecast_time, site_id=site_id, target=target),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get_forecast_availability(
        self,
        site_id: str,
        target: str,
        start_date: datetime = datetime.now(tz=timezone.utc) - timedelta(days=1),
        end_date: datetime = datetime.now(tz=timezone.utc),
        run_tag: Optional[str] = None,
    ) -> list[datetime]:
        params = {
            "start_date": start_date.isoformat(timespec="seconds"),
            "end_date": end_date.isoformat(timespec="seconds"),
        }
        if run_tag is not None:
            params["run_tag"] = run_tag
        response = self._get(EndpointRoutes.FORECASTAVAILABILITY.format(site_id=site_id, target=target), params=params)
        response.raise_for_status()
        return [datetime.fromisoformat(dt) for dt in response.json()]

    def get_historical_forecast(
        self, forecast_datetime: datetime, site_id: str, target: str, run_tag: Optional[str] = None
    ) -> dict:
        """
        Retrieve the historical forecast for a specific datetime, site, and target.

        Args:
            forecast_datetime (datetime): The datetime for which the forecast is requested.
            site_id (str): The identifier of the site for which the forecast is requested.
            target (str): The target parameter for the forecast.
            run_tag (Optional[str], optional): An optional run tag to filter the forecast. Defaults to None.

        Returns:
            dict: The historical forecast data in JSON format.

        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
            NotAuthenticatedError: If the client is not authenticated.
        """
        params = {"run_tag": run_tag} if run_tag is not None else {}
        response = self._get(
            EndpointRoutes.HISTORICAL_FORECAST.format(
                datetime=forecast_datetime.isoformat(), siteid=site_id, target=target
            ),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get_historical_deterministic_forecast(
        self, forecast_datetime: datetime, site_id: str, target: str, run_tag: Optional[str] = None
    ) -> dict:
        """
        Retrieve the historical forecast for a specific datetime, site, and target.

        Args:
            forecast_datetime (datetime): The datetime for which the forecast is requested.
            site_id (str): The identifier of the site for which the forecast is requested.
            target (str): The target parameter for the forecast.
            run_tag (Optional[str], optional): An optional run tag to filter the forecast. Defaults to None.
        Returns:
            dict: The historical forecast data in JSON format.

        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
            NotAuthenticatedError: If the client is not authenticated.
        """
        params = {"run_tag": run_tag} if run_tag is not None else {}
        response = self._get(
            EndpointRoutes.HISTORICAL_FORECAST_DET.format(
                datetime=forecast_datetime.isoformat(), siteid=site_id, target=target
            ),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def get_historical_probabilistic_forecast(
        self, forecast_datetime: datetime, site_id: str, target: str, run_tag: Optional[str] = None
    ) -> dict:
        """
        Retrieve the historical probabilistic forecast for a specific datetime, site, and target.

        Args:
            forecast_datetime (datetime): The datetime for which the forecast is requested.
            site_id (str): The identifier of the site for which the forecast is requested.
            target (str): The target parameter for the forecast.
            run_tag (Optional[str], optional): An optional run tag to filter the forecast. Defaults to None.

        Returns:
            dict: The historical probabilistic forecast data in JSON format.

        Raises:
            HTTPError: If the HTTP request returned an unsuccessful status code.
            NotAuthenticatedError: If the client is not authenticated.
        """
        params = {"run_tag": run_tag} if run_tag is not None else {}
        response = self._get(
            EndpointRoutes.HISTORICAL_FORECAST_PROBA.format(
                datetime=forecast_datetime.isoformat(), siteid=site_id, target=target
            ),
            params=params,
        )
        response.raise_for_status()
        return response.json()
