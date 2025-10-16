from datetime import time
from unittest.mock import MagicMock, patch

import pytest

from calibsunapi.client import CalibsunApiClient
from calibsunapi.exceptions import NoCredentialsError, NotAuthenticatedError
from calibsunapi.models.listplants import Plant
from calibsunapi.models.uploadmeasurements import UploadLinkMeasurementsResponse, UploadMeasurementsFormats


@patch("calibsunapi.client.requests.post")
def test_authenticate_success(mock_post, client: CalibsunApiClient):
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "test_token", "expires_in": 3600, "token_type": "Bearer"}
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    client._authenticate()

    assert client._token is not None
    assert client._token.access_token == "test_token"


@patch("calibsunapi.client.requests.post")
def test_authenticate_no_credentials(mock_post):
    client = CalibsunApiClient()
    print(client.calibsun_client_id)
    with pytest.raises(NoCredentialsError):
        client._authenticate()


@patch("calibsunapi.client.requests.get")
def test_list_plants(mock_get, authentified_client: CalibsunApiClient, plant: dict):
    mock_response = MagicMock()
    mock_response.json.return_value = [plant]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    plants = authentified_client.list_plants()

    assert len(plants) == 1
    assert isinstance(plants[0], Plant)
    assert plants[0].site_id == plant.get("site_id")


@patch("calibsunapi.client.requests.post")
@patch("calibsunapi.client.requests.get")
def test_push_measurements(mock_get, mock_post, authentified_client: CalibsunApiClient):
    mock_get_response = MagicMock()
    mock_get_response.json.return_value = {"url": "http://example.com/upload", "fields": {"field1": "value1"}}
    mock_get_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_get_response

    mock_post_response = MagicMock()
    mock_post_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_post_response

    response = authentified_client.push_measurements("site_id", UploadMeasurementsFormats.JSON, data={"key": "value"})

    assert response.raise_for_status.called


@patch("calibsunapi.client.requests.get")
def test_get_latest_forecast(mock_get, authentified_client: CalibsunApiClient):
    mock_response = MagicMock()
    mock_response.json.return_value = {"forecast": "data"}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    forecast = authentified_client.get_latest_forecast("site_id", "target")

    assert forecast == {"forecast": "data"}


@patch("calibsunapi.client.requests.get")
def test_get_latest_forecast_probabilistic(mock_get, authentified_client: CalibsunApiClient):
    mock_response = MagicMock()
    mock_response.json.return_value = {"forecast": "probabilistic_data"}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    forecast = authentified_client.get_latest_forecast_probabilistic("site_id", "target")

    assert forecast == {"forecast": "probabilistic_data"}


@patch("calibsunapi.client.requests.get")
def test_get_latest_forecast_deterministic(mock_get, authentified_client: CalibsunApiClient):
    mock_response = MagicMock()
    mock_response.json.return_value = {"forecast": "deterministic_data"}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    forecast = authentified_client.get_latest_forecast_deterministic("site_id", "target")

    assert forecast == {"forecast": "deterministic_data"}


@patch("calibsunapi.client.requests.get")
def test_get_forecast(mock_get, authentified_client: CalibsunApiClient):
    mock_response = MagicMock()
    mock_response.json.return_value = {"forecast": "fixed_time_data"}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    forecast = authentified_client.get_forecast(time(0, 0), "site_id", "target")

    assert forecast == {"forecast": "fixed_time_data"}


@patch("calibsunapi.client.requests.post")
@patch("calibsunapi.client.CalibsunApiClient._get_upload_parameters")
def test_push_measurements_no_auth_header(
    mock_get_upload_parameters, mock_post, authentified_client: CalibsunApiClient
):
    # Mock the upload parameters response
    mock_get_upload_parameters.return_value = UploadLinkMeasurementsResponse(
        url="https://example.com/upload", fields={"key": "value"}
    )

    # Mock the POST request
    mock_post.return_value = MagicMock(status_code=200)

    # Call push_measurements
    authentified_client.push_measurements(
        site_id="test_site", format=UploadMeasurementsFormats.JSON, data={"test": "data"}
    )

    # Assert the POST request was made without the Authorization header
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "headers" not in kwargs
