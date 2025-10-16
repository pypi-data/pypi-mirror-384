import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.gpas.client.env import get_refresh_token, refresh_auth_token, save_tokens


@pytest.fixture
def mock_path(mocker):
    """Fixture to mock the token path and file operations."""
    mock_path = mocker.MagicMock()
    mock_path.open = mock_open()
    mocker.patch("src.gpas.client.env.get_token_path", return_value=mock_path)
    return mock_path


@pytest.fixture
def mock_datetime_now(mocker):
    """Mocks datetime.now() to return a fixed, predictable time."""
    fixed_now = datetime(2025, 1, 15, 10, 0, 0)
    mock_now = mocker.patch("src.gpas.client.env.datetime")
    mock_now.now.return_value = fixed_now
    return mock_now


@pytest.fixture(autouse=True)
def mock_auth_constants(mocker):
    """Mocks the global constants used for Auth0 API calls."""
    mocker.patch("src.gpas.client.env.AUTH_ISSUER", "test.auth0.com")
    mocker.patch("src.gpas.client.env.AUTH_CLIENT_ID", "test_client_id")


class TestTokenManagement:
    TOKEN_DATA_SUCCESS = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
    }
    HOST = "test.api.com"
    EXPIRES_IN = 3600
    BUFFER = 300  # 5 minutes

    def test_save_tokens_new_file(self, mock_path, mock_datetime_now, mocker):
        """Tests saving tokens when the file does not exist (initial login)."""
        mock_path.exists.return_value = False
        m_open = mock_open()
        mocker.patch("src.gpas.client.env.open", m_open)

        save_tokens(self.HOST, self.TOKEN_DATA_SUCCESS, self.EXPIRES_IN)

        # expected expiry calculation: 1 hour (3600s) - 5 mins (300s) = 3300s
        expected_expiry_dt = mock_datetime_now.now.return_value + timedelta(
            seconds=self.EXPIRES_IN - self.BUFFER
        )

        # check file opened to write in
        m_open.assert_called_once_with(mock_path, "w")

        # check the data written to file
        written_data = "".join(
            call_args.args[0] for call_args in m_open.return_value.write.call_args_list
        )
        saved_data = json.loads(written_data)

        assert saved_data["access_token"] == "new_access_token"
        assert saved_data["refresh_token"] == "new_refresh_token"
        assert saved_data["expiry"] == expected_expiry_dt.isoformat()

    def test_get_refresh_token_success(self, mock_path, mocker):
        """Tests successful retrieval of the refresh token."""
        mock_path.exists.return_value = True
        mock_token_data = {"refresh_token": "retrieved_refresh_token"}

        m_open = mock_open(read_data=json.dumps(mock_token_data))
        mocker.patch("src.gpas.client.env.open", m_open)

        token = get_refresh_token(self.HOST)

        # check got refrsh token
        assert token == "retrieved_refresh_token"
        m_open.assert_called_once_with(mock_path)
        mock_path.exists.assert_called_once()

    @patch("src.gpas.client.env.save_tokens")
    @patch("src.gpas.client.env.get_refresh_token", return_value="valid_refresh_token")
    def test_refresh_auth_token_success(
        self, mock_get_refresh_token, mock_save_tokens, mocker
    ):
        """Tests the successful exchange of refresh token for a new access token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.TOKEN_DATA_SUCCESS
        mock_response.raise_for_status.return_value = None

        mock_post = mocker.patch(
            "src.gpas.client.env.requests.post", return_value=mock_response
        )

        refresh_auth_token(self.HOST)

        # cehck the POST call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "test.auth0.com/oauth/token"

        # pheck payload
        assert kwargs["json"] == {
            "grant_type": "refresh_token",
            "client_id": "test_client_id",
            "refresh_token": "valid_refresh_token",
        }

        # check tokens are saved
        mock_save_tokens.assert_called_once_with(
            self.HOST, self.TOKEN_DATA_SUCCESS, self.EXPIRES_IN
        )
