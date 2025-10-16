from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Literal

import httpx

REDIRECT_STATUSES = {301, 302, 303, 307, 308}


def request_with_redirects(
    client: httpx.Client,
    method: Literal["GET", "POST", "PUT"],
    url: str,
    *,
    data: Any | None = None,
    json: Any | None = None,
    files: Any | None = None,
    headers: Mapping[str, str] | None = None,
    max_redirects: int = 5,
    timeout: int | None = None,
) -> httpx.Response:
    """POST then manually follow up to max_redirects redirects.

    We preserve *all* headers (including Authorization) across redirects.
    """
    # First request (explicitly disable auto-redirects)
    if method == "POST":
        response = client.post(
            url,
            data=data,
            json=json,
            headers=headers,
            files=files,
            follow_redirects=False,
            timeout=timeout,
        )
    elif method == "GET":
        response = client.get(
            url, params=data, headers=headers, follow_redirects=False, timeout=timeout
        )
    elif method == "PUT":
        response = client.put(
            url,
            data=data,
            json=json,
            headers=headers,
            follow_redirects=False,
            timeout=timeout,
        )
    else:
        raise ValueError(f"Unsupported method: {method}")

    redirects_remaining = max_redirects

    while redirects_remaining > 0 and response.status_code in REDIRECT_STATUSES:
        location = response.headers.get("Location")
        if not location:
            break

        # Resolve relative redirects against the previous request URL
        next_url = response.request.url.join(location)

        if method == "POST":
            response = client.post(
                str(next_url),
                data=data,
                json=json,
                files=files,
                headers=headers,
                follow_redirects=False,
                timeout=timeout,
            )
        elif method == "GET":
            response = client.get(
                str(next_url),
                params=data,
                headers=headers,
                follow_redirects=False,
                timeout=timeout,
            )
        elif method == "PUT":
            response = client.put(
                str(next_url),
                data=data,
                json=json,
                headers=headers,
                follow_redirects=False,
                timeout=timeout,
            )

        redirects_remaining -= 1

    return response


@contextmanager
def stream_with_redirects(
    client: httpx.Client,
    url: str,
    headers: Mapping[str, str] | None = None,
    max_redirects: int = 5,
) -> Iterator[httpx.Response]:
    """GET a stream then manually follow up to max_redirects redirects.

    We preserve *all* headers (including Authorization) across redirects.
    """
    # Open first stream and ENTER the context to get an httpx.Response
    response_cm = client.stream("GET", url, headers=headers, follow_redirects=False)
    response = response_cm.__enter__()

    try:
        redirects_remaining = max_redirects

        while redirects_remaining > 0 and response.status_code in REDIRECT_STATUSES:
            location = response.headers.get("Location")
            if not location:
                break

            # Resolve relative redirects against the previous request URL
            next_url = response.request.url.join(location)

            # Close current response/context manager before following redirect
            response.close()
            response_cm.__exit__(None, None, None)

            # Open next stream and ENTER to get the Response
            response_cm = client.stream(
                "GET",
                str(next_url),
                headers=headers,
                follow_redirects=False,
            )
            response = response_cm.__enter__()

            redirects_remaining -= 1

        # Yield the live Response to the caller
        yield response
    finally:
        # Ensure the response and its context manager are closed
        try:
            response.close()
        finally:
            response_cm.__exit__(None, None, None)
