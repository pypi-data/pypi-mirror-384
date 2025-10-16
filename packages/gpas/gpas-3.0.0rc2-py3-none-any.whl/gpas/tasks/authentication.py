import json
import time
from datetime import datetime, timedelta

import httpx
import jwt
from auth0.authentication.token_verifier import (
    AsymmetricSignatureVerifier,
    TokenVerifier,
)
from auth0.exceptions import TokenValidationError
from rich_click import echo, secho, style

from gpas.client import env
from gpas.constants import (
    ALGORITHMS,
    AUTH_AUDIENCE,
    AUTH_CLIENT_ID,
    AUTH_ISSUER,
    CLI_ACCESS_TOKEN,
    DEFAULT_HOST,
)
from gpas.http_helpers import request_with_redirects
from gpas.log_utils import httpx_hooks, logger


def validate_token(id_token: str):
    """Verify the token and its precedence.

    Args:
        id_token(str): The id_token
    """
    jwks_url = f"{AUTH_ISSUER}/.well-known/jwks.json"
    issuer = f"{AUTH_ISSUER}/"
    sv = AsymmetricSignatureVerifier(jwks_url)
    tv = TokenVerifier(signature_verifier=sv, issuer=issuer, audience=AUTH_CLIENT_ID)
    tv.verify(id_token)


def authenticate(host: str = DEFAULT_HOST) -> dict[str, str | int] | None:
    """Requests a user auth token, writes to ~/.config/gpas/tokens/<host>.json.

    Args:
        host (str): The host server. Defaults to DEFAULT_HOST.
    """
    if CLI_ACCESS_TOKEN:
        token_path = env.get_token_path(host)
        with token_path.open(mode="w") as fh:
            token_data = json.loads(CLI_ACCESS_TOKEN)
            expires_in = token_data.get("expires_in", 3600)
            expiry = datetime.now() + timedelta(seconds=expires_in)
            token_data["expiry"] = expiry.isoformat()
            json.dump(token_data, fh)
        logger.info(f"Authenticated via access token ({token_path})")
        secho("Authentication complete!", fg="green", bold=True)
        return None

    device_code_payload = {
        "client_id": AUTH_CLIENT_ID,
        "scope": "openid profile offline_access",
        "audience": AUTH_AUDIENCE,
    }
    device_code_response = httpx.post(
        f"{AUTH_ISSUER}/oauth/device/code", json=device_code_payload
    )

    if device_code_response.status_code != 200:
        logger.error("Error generating the device code")
        secho("Error generating the device code", fg="red", err=True)
        exit()

    secho("Device code successful", fg="green")
    device_code_data = device_code_response.json()
    echo(
        "1. On your computer or mobile device navigate to: "
        + style(device_code_data["verification_uri_complete"], fg="blue", bold=True),
    )
    echo(
        "2. Enter the following code: "
        + style(text=device_code_data["user_code"], fg="cyan", bold=True),
    )
    # New code 👇
    token_payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "device_code": device_code_data["device_code"],
        "client_id": AUTH_CLIENT_ID,
        "audience": AUTH_AUDIENCE,
        "issuer": AUTH_ISSUER,
    }

    authenticated = False
    while not authenticated:
        secho("Checking if the user completed the flow...")
        token_response = httpx.post(f"{AUTH_ISSUER}/oauth/token", data=token_payload)

        token_data = token_response.json()
        if token_response.status_code == 200:
            secho("Authenticated!", fg="green")
            logger.info("Authenticated")
            authenticated = True
        elif token_data["error"] not in ("authorization_pending", "slow_down"):
            secho(token_data["error_description"], fg="red", err=True)
            logger.error(token_data["error_description"])
            return None
        else:
            time.sleep(device_code_data["interval"])
    try:
        validate_token(token_data["id_token"])
    except TokenValidationError:
        secho("Unable to validate token", fg="red", err=True)
        logger.error("Unable to validate token")
    current_user = jwt.decode(
        token_data["id_token"],
        algorithms=ALGORITHMS,
        issuer=AUTH_ISSUER,
        options={"verify_signature": False},
    )
    token_path = env.get_token_path(host)

    # Get expiry time, default token should be 1 hour.
    one_hour_in_seconds = 3600
    expires_in_seconds = token_data.get("expires_in", one_hour_in_seconds)

    env.save_tokens(host, token_data, token_expires_in=expires_in_seconds)

    logger.info(f"Authenticated ({token_path})")
    secho("Authentication complete!", fg="green", bold=True)
    return current_user


def check_authentication(host: str) -> None:
    """Check if the user is authenticated.

    Args:
        host (str): The host server.

    Raises:
        RuntimeError: If authentication fails.
    """
    with httpx.Client(event_hooks=httpx_hooks) as client:
        response = request_with_redirects(
            client,
            "GET",
            f"{env.get_protocol()}://{host}/api/v1/batches",
            headers={"Authorization": f"Bearer {env.get_access_token(host)}"},
        )
    if response.is_error:
        logger.error(f"Authentication failed for host {host}")
        secho(f"Authentication Failed for host {host}", fg="red", err=True)
        raise RuntimeError(
            "Authentication failed. You may need to re-authenticate with `gpas auth`"
        )
