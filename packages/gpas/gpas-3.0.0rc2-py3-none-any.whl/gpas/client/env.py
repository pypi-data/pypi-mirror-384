import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from gpas.constants import (
    AUTH_CLIENT_ID,
    AUTH_ISSUER,
    DEFAULT_HOST,
    DEFAULT_PROTOCOL,
    DEFAULT_UPLOAD_HOST,
)
from gpas.log_utils import logger


def get_protocol() -> str:
    """Get the protocol to use for communication.

    Returns:
        str: The protocol (e.g., 'http', 'https').
    """
    if "GPAS_PROTOCOL" in os.environ:
        return os.environ["GPAS_PROTOCOL"]
    else:
        return DEFAULT_PROTOCOL


def get_host(cli_host: str | None = None) -> str:
    """Return hostname using 1) CLI argument, 2) environment variable, 3) default value.

    Args:
        cli_host (str | None): The host provided via CLI argument.

    Returns:
        str: The resolved hostname.
    """
    return (
        cli_host if cli_host is not None else os.environ.get("GPAS_HOST", DEFAULT_HOST)
    )


def get_upload_host(cli_host: str | None = None) -> str:
    """Return hostname using 1) CLI argument, 2) environment variable, 3) default value.

    Args:
        cli_host (str | None): The host provided via CLI argument.

    Returns:
        str: The resolved hostname.
    """
    return (
        cli_host
        if cli_host is not None
        else os.environ.get("GPAS_UPLOAD_HOST", DEFAULT_UPLOAD_HOST)
    )


def get_token_path(host: str) -> Path:
    """Get the path to the token file for a given host.

    Args:
        host (str): The host for which to get the token path.

    Returns:
        Path: The path to the token file.
    """
    conf_dir = Path.home() / ".config" / "gpas"
    token_dir = conf_dir / "tokens"
    token_dir.mkdir(parents=True, exist_ok=True)
    token_path = token_dir / f"{host}.json"
    return token_path


def get_token_expiry(host: str) -> datetime | None:
    """Get the expiry date of the token for a given host.

    Args:
        host (str): The host for which to get the token expiry date.

    Returns:
        datetime | None: The expiry date of the token, or None if the token does not exist.
    """
    token_path = get_token_path(host)
    if token_path.exists():
        try:
            with open(token_path) as token_string:
                token: dict = json.load(token_string)
                expiry = token.get("expiry", False)
                if expiry:
                    return datetime.fromisoformat(expiry)
        except json.JSONDecodeError:
            return None
    return None


def is_auth_token_live(host: str) -> bool:
    """Check if the authentication token for a given host is still valid.

    Args:
        host (str): The host for which to check the token validity.

    Returns:
        bool: True if the token is still valid, False otherwise.
    """
    expiry = get_token_expiry(host)
    if expiry:
        logger.debug(f"Token expires: {expiry}")
        return expiry > datetime.now()
    return False


def get_access_token(host: str) -> str:
    """Reads token from ~/.config/gpas/tokens/<host>.

    Args:
        host (str): The host for which to retrieve the token.

    Returns:
        str: The access token.
    """
    token_path = get_token_path(host)
    logger.debug(f"Getting token path: {token_path}")
    try:
        data = json.loads(token_path.read_text())
    except FileNotFoundError as fne:
        logger.exception("Can't find access token")
        raise FileNotFoundError(
            f"Token not found at {token_path}, have you authenticated?"
        ) from fne
    return data["access_token"].strip()


def save_tokens(host: str, token_data: dict[str, Any], token_expires_in: int = 3600):
    """Saves the token data, calculating and storing the expiry datetime.

    Args:
        host (str): The host for which to save the tokens.
        token_data (dict): The dictionary response from Auth0's /oauth/token endpoint.
        token_expires_in (int): The 'expires_in' value from the Auth0 response (in seconds).
    """
    token_path = get_token_path(host)

    # calculate expiry time, but include 5 min buffer to start refresh before expired
    buffer_seconds = 300
    expiry_datetime = datetime.now() + timedelta(
        seconds=token_expires_in - buffer_seconds
    )

    # get existing token data
    existing_data = {}
    if token_path.exists():
        try:
            with open(token_path) as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            pass  # ignore if file is corrupt/empty

    # merge existing data with update with new tokens/alculated expiry
    data_to_save = existing_data | {
        "access_token": token_data["access_token"],
        # only overwrite refresh_token if a new one is provided
        "refresh_token": token_data.get(
            "refresh_token", existing_data.get("refresh_token")
        ),
        "expiry": expiry_datetime.isoformat(),
    }

    # save
    with open(token_path, "w") as f:
        json.dump(data_to_save, f, indent=4)
    logging.info(
        f"New token and refresh token saved for {host}. Expires: {expiry_datetime.isoformat()}"
    )


def get_refresh_token(host: str) -> str | None:
    """Get refresh token from stored file.

    Args:
        host (str): The host for which to get the refresh token.

    Returns:
        str | None: The refresh token if available
    """
    token_path = get_token_path(host)
    if token_path.exists():
        try:
            with open(token_path) as f:
                data = json.load(f)
                return data.get("refresh_token")
        except json.JSONDecodeError:
            return None
    return None


def refresh_auth_token(host: str) -> None:
    """Exchanges the stored refresh token for a new access token via Auth0.

    Args:
        host (str): The host for which to refresh the token.
    """
    refresh_token = get_refresh_token(host)

    if not refresh_token:
        # user session expired, need to log in again
        raise Exception(
            f"No refresh token available for {host}. Please re-authenticate."
        )

    token_url = f"{AUTH_ISSUER}/oauth/token"

    # payload for Auth0 refresh_token grant type following docs
    payload = {
        "grant_type": "refresh_token",
        "client_id": AUTH_CLIENT_ID,
        "refresh_token": refresh_token,
    }

    try:
        response = requests.post(token_url, json=payload)
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        logging.error(
            f"Refresh Token is invalid or expired. Failed to exchange for new access token: {e.response.text}"
        )
        raise Exception("Session expired. Please log in again.") from e

    # Success: save new access and refresh tokens with new expiry
    token_data = response.json()
    expires_in = token_data.get("expires_in", 3600)
    save_tokens(host, token_data, expires_in)

    logging.info("Token successfully refreshed and saved.")


def ensure_token_valid(host: str):
    """Ensure the current access token is still valid.

    Args:
        host (str): The host for which to check the toen.
    """
    if not is_auth_token_live(host):
        refresh_auth_token(host)
