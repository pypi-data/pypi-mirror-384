import logging
import os
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from types import TracebackType

import httpx
from rich_click import secho

from gpas.errors import (
    AuthorizationError,
    InsufficientFundsError,
    MissingError,
    ServerSideError,
)

logger = logging.getLogger("gpas")
logger.setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.ERROR)


def get_log_file_path() -> Path:
    """Get the platform-specific log file path."""
    if sys.platform == "win32":
        log_dir = Path(os.getenv("LOCALAPPDATA", "")) / "gpas"
    else:
        # Use XDG Base Directory Specification for Unix-like systems
        xdg_state_home = os.getenv("XDG_STATE_HOME")
        if xdg_state_home:
            log_dir = Path(xdg_state_home) / "gpas"
        else:
            log_dir = Path.home() / ".local" / "state" / "gpas"

    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "gpas.log"


def configure_debug_logging(debug: bool) -> None:
    """Configure logging for debug mode.

    Args:
        debug (bool): Whether to enable debug logging.
    """
    log_file = get_log_file_path()
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(module)s - %(lineno)d - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    if len(logger.handlers) == 0:
        logger.addHandler(handler)
        logger.propagate = False

    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    else:
        logger.setLevel(logging.INFO)
        # Suppress tracebacks on exceptions unless in debug mode.
        sys.excepthook = exception_handler


def exception_handler(
    exception_type: type[BaseException],
    exception: BaseException,
    _traceback: TracebackType | None,
) -> None:
    """Handle uncaught exceptions by logging them.

    Args:
        exception_type (type): Exception type.
        exception (BaseException): Exception instance.
        _traceback (TracebackType): Traceback object.
    """
    secho(f"{exception_type.__name__}: {exception}")


def log_request(request: httpx.Request) -> None:
    """Log HTTP request details.

    Args:
        request (httpx.Request): The HTTP request object.
    """
    logger.debug(f"Request: {request.method} {request.url}")


def log_response(response: httpx.Response) -> None:
    """Log HTTP response details.

    Args:
        response (httpx.Response): The HTTP response object.
    """
    if response.is_error:
        request = response.request
        response.read()
        message = response.json().get("message")
        secho(f"{request.method} {request.url} ({response.status_code})")
        secho(message)


def raise_for_status(response: httpx.Response) -> None:
    """Raise an exception for HTTP error responses.

    Args:
        response (httpx.Response): The HTTP response object.

    Raises:
        httpx.HTTPStatusError: If the response contains an HTTP error status.
    """
    if 300 <= response.status_code < 400:
        return  # Follow redirects

    if response.is_error:
        response.read()
        if response.status_code == httpx.codes.UNAUTHORIZED:
            logger.error("Have you tried running `gpas auth`?")
            raise AuthorizationError()
        elif response.status_code == httpx.codes.PAYMENT_REQUIRED:
            raise InsufficientFundsError()
        elif response.status_code == httpx.codes.FORBIDDEN:
            raise PermissionError()
        elif response.status_code == httpx.codes.NOT_FOUND:
            raise MissingError()
        elif response.status_code == httpx.codes.UPGRADE_REQUIRED:
            return None
        elif response.status_code >= 500:
            raise ServerSideError()

    # Default to httpx errors in other cases
    response.raise_for_status()


httpx_hooks: Mapping[str, list[Callable]] = {
    "request": [log_request],
    "response": [log_response, raise_for_status],
}
