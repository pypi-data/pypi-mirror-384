from unittest.mock import call, mock_open

import jwt
import pytest

from gpas.constants import AUTH_AUDIENCE, AUTH_CLIENT_ID, AUTH_ISSUER
from gpas.tasks import authenticate


def create_dummy_jwt(payload):
    """Creates a dummy JWT for testing purposes, without a signature."""
    return jwt.encode(payload, key="", algorithm="none")


@pytest.fixture
def mock_httpx_post(mocker):
    """Fixture to mock httpx.post."""
    return mocker.patch("httpx.post")


@pytest.fixture
def mock_time_sleep(mocker):
    """Fixture to mock time.sleep."""
    return mocker.patch("time.sleep")


@pytest.fixture
def mock_validate_token(mocker):
    """Fixture to mock validate_token."""
    return mocker.patch("gpas.tasks.authentication.validate_token")


@pytest.fixture
def mock_token_path(mocker):
    """Fixture to mock the token path and file operations."""
    mock_path = mocker.MagicMock()
    mock_path.open = mock_open()
    mocker.patch("gpas.client.env.get_token_path", return_value=mock_path)
    return mock_path


def test_authenticate_success(
    mocker,
    mock_httpx_post,
    mock_time_sleep,
    mock_validate_token,
    capsys,
):
    """Tests the successful authentication path."""
    device_code_response_data = {
        "device_code": "test_device_code",
        "user_code": "TEST-CODE",
        "verification_uri_complete": "https://test.com/verify",
        "interval": 1,
    }
    # Prepare the successful token response data
    success_token_data = {
        "id_token": create_dummy_jwt({"name": "testuser", "iss": f"{AUTH_ISSUER}/"}),
        "expires_in": 3600,
        "access_token": "access_token",
        "refresh_token": "refresh_token",
    }
    id_token = success_token_data["id_token"]

    mock_httpx_post.side_effect = [
        # Response for device code request
        mocker.MagicMock(status_code=200, json=lambda: device_code_response_data),
        # First response for token request (pending)
        mocker.MagicMock(
            status_code=403,
            json=lambda: {
                "error": "authorization_pending",
                "error_description": "Authorization pending.",
            },
        ),
        # Second response for token request (success)
        mocker.MagicMock(
            status_code=200,
            json=lambda: {
                "id_token": id_token,
                "expires_in": 3600,
                "access_token": "access_token",
                "refresh_token": "refresh_token",
            },
        ),
    ]

    # mock save tokens
    mock_save_tokens = mocker.patch("src.gpas.tasks.authentication.env.save_tokens")

    test_host = "test.example.com"
    user = authenticate(host=test_host)
    assert user is not None
    assert user["name"] == "testuser"

    # Check that the correct calls to httpx.post were made
    expected_calls = [
        call(
            f"{AUTH_ISSUER}/oauth/device/code",
            json={
                "client_id": AUTH_CLIENT_ID,
                "scope": "openid profile offline_access",
                "audience": AUTH_AUDIENCE,
            },
        ),
        call(
            f"{AUTH_ISSUER}/oauth/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": "test_device_code",
                "client_id": AUTH_CLIENT_ID,
                "audience": AUTH_AUDIENCE,
                "issuer": AUTH_ISSUER,
            },
        ),
        call(
            f"{AUTH_ISSUER}/oauth/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": "test_device_code",
                "client_id": AUTH_CLIENT_ID,
                "audience": AUTH_AUDIENCE,
                "issuer": AUTH_ISSUER,
            },
        ),
    ]
    mock_httpx_post.assert_has_calls(expected_calls)

    # Check that time.sleep was called
    mock_time_sleep.assert_called_once_with(1)

    # Check that validate_token was called
    mock_validate_token.assert_called_once_with(id_token)

    # check tokens saved
    mock_save_tokens.assert_called_once_with(
        test_host, success_token_data, token_expires_in=3600
    )

    # Check output to user
    captured = capsys.readouterr()
    assert "https://test.com/verify" in captured.out
    assert "TEST-CODE" in captured.out
    assert "Authenticated!" in captured.out


def test_authenticate_device_code_error(mocker, mock_httpx_post, caplog):
    """Tests the path where the device code request fails."""
    mock_httpx_post.return_value = mocker.MagicMock(status_code=400)

    with pytest.raises(SystemExit):
        authenticate()

    assert "Error generating the device code" in caplog.text


def test_authenticate_token_request_error(mocker, mock_httpx_post, capsys):
    """Tests the path where the token request returns a non-pending error."""
    device_code_response_data = {
        "device_code": "test_device_code",
        "user_code": "TEST-CODE",
        "verification_uri_complete": "https://test.com/verify",
        "interval": 1,
    }
    mock_httpx_post.side_effect = [
        mocker.MagicMock(status_code=200, json=lambda: device_code_response_data),
        mocker.MagicMock(
            status_code=403,
            json=lambda: {
                "error": "access_denied",
                "error_description": "User denied access.",
            },
        ),
    ]

    authenticate()

    captured = capsys.readouterr()
    assert "User denied access." in captured.err
