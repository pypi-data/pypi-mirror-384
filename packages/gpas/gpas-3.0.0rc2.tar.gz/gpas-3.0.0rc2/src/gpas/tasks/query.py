import csv
from pathlib import Path

import httpx
from packaging.version import Version
from rich_click import echo, secho, style
from tqdm import tqdm

import gpas
from gpas import models, util
from gpas.client import env
from gpas.constants import DEFAULT_HOST
from gpas.errors import UnsupportedClientError
from gpas.http_helpers import request_with_redirects
from gpas.log_utils import httpx_hooks, logger


def parse_csv(path: Path) -> list[dict]:
    """Parse a CSV file.

    Args:
        path (Path): The path to the CSV file.

    Returns:
        list[dict]: The parsed CSV data.
    """
    with open(path) as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def check_version_compatibility(host: str) -> None:
    """Check the client version expected by the server (Portal).

    Raise an exception if the client version is not
    compatible.

    Args:
        host (str): The host server.
    """
    with httpx.Client(
        event_hooks=httpx_hooks,
        transport=httpx.HTTPTransport(retries=2),
        timeout=10,
    ) as client:
        response = request_with_redirects(
            client,
            "GET",
            f"{env.get_protocol()}://{host}/cli-version",
        )
    lowest_cli_version = response.json()["version"]
    logger.debug(
        f"Client version {gpas.__version__}, server version: {lowest_cli_version})"
    )
    if Version(gpas.__version__) < Version(lowest_cli_version):
        raise UnsupportedClientError(gpas.__version__, lowest_cli_version)


# noinspection PyBroadException
def check_for_newer_version() -> None:
    """Check whether there is a new version of the CLI available on Pypi and advise the user to upgrade."""
    try:
        gpas_pypi_url = "https://pypi.org/pypi/gpas/json"
        with httpx.Client(transport=httpx.HTTPTransport(retries=2)) as client:
            response = request_with_redirects(
                client,
                "GET",
                gpas_pypi_url,
                headers={"Accept": "application/json"},
            )
            if response.status_code == 200:
                latest_version = Version(
                    response.json().get("info", {}).get("version", gpas.__version__)
                )
                if Version(gpas.__version__) < latest_version:
                    secho(
                        f"A new version of the GPAS CLI ({latest_version}) is available to install,"
                        + " please follow the installation steps in the README.md file to upgrade.",
                        fg="cyan",
                    )

    except (httpx.ConnectError, httpx.NetworkError, httpx.TimeoutException):
        pass
    except Exception:  # Errors in this check should never prevent further CLI usage, ignore all errors.
        pass


def fetch_sample_status(
    samples: str | None = None,
    mapping_csv: Path | None = None,
    host: str = DEFAULT_HOST,
) -> dict[str, str]:
    """Get the status of samples from the server.

    Args:
        samples (str | None): A comma-separated list of sample IDs.
        mapping_csv (Path | None): The path to a CSV file containing sample mappings.
        host (str): The host server. Defaults to DEFAULT_HOST.

    Returns:
        dict[str, str]: A dictionary with sample IDs as keys and their statuses as values.
    """
    check_version_compatibility(host)
    if samples:
        guids = util.parse_comma_separated_string(samples)
        guids_samples = dict.fromkeys(guids)
        logger.info(f"Using guids {guids}")
    elif mapping_csv:
        csv_records = parse_csv(Path(mapping_csv))
        guids_samples = {s["remote_sample_name"]: s["sample_name"] for s in csv_records}
        logger.info(f"Using samples in {mapping_csv}")
        logger.debug(guids_samples)
    else:
        raise RuntimeError("Specify either a list of sample IDs or a mapping CSV")

    samples_status = {}
    for guid, sample in tqdm(
        guids_samples.items(), desc="Querying samples", leave=False
    ):
        name = sample if mapping_csv else guid

        try:
            sample = fetch_sample(sample_id=guid, host=host)
        except Exception as e:
            logger.debug(f"Error fetching sample {guid}: {e}")
            raise RuntimeError(f"Failed to fetch sample for {guid}") from None

        samples_status[name] = sample.get("status")
        samples_status["Pipeline version"] = sample.get("pipeline_version")
    return samples_status  # type: ignore


def fetch_sample_metadata(
    samples: str | None = None,
    mapping_csv: Path | None = None,
    host: str = DEFAULT_HOST,
) -> dict[str, dict]:
    """Query sample metadata returning a dict of metadata keyed by sample ID.

    Args:
        query_string (str): The query string.
        host (str): The host server.
        protocol (str): The protocol to use. Defaults to DEFAULT_PROTOCOL.

    Returns:
        dict: The query result.
    """
    check_version_compatibility(host)
    if samples:
        guids = util.parse_comma_separated_string(samples)
        guids_samples = dict.fromkeys(guids)
        logger.info(f"Using guids {guids}")
    elif mapping_csv:
        csv_records = parse_csv(Path(mapping_csv))
        guids_samples = {s["remote_sample_name"]: s["sample_name"] for s in csv_records}
        logger.info(f"Using samples in {mapping_csv}")
        logger.debug(f"{guids_samples=}")
    else:
        raise RuntimeError("Specify either a list of sample IDs or a mapping CSV")
    samples_metadata = {}
    for guid, sample in tqdm(
        guids_samples.items(), desc="Querying samples", leave=False
    ):
        name = sample if mapping_csv else guid
        samples_metadata[name] = fetch_sample(sample_id=guid, host=host)
    return samples_metadata


def fetch_output_files(
    sample_id: str, host: str, latest: bool = True
) -> dict[str, models.RemoteFile]:
    """Return models.RemoteFile instances for a sample, optionally including only latest run.

    Args:
        sample_id (str): The sample ID.
        host (str): The host server.
        protocol (str): The protocol to use. Defaults to DEFAULT_PROTOCOL.

    Returns:
        dict[str, models.RemoteFile]: The output files.
    """
    headers = {"Authorization": f"Bearer {env.get_access_token(host)}"}
    with httpx.Client(
        event_hooks=httpx_hooks,
        transport=httpx.HTTPTransport(retries=5),
    ) as client:
        response = request_with_redirects(
            client,
            "GET",
            f"{env.get_protocol()}://{host}/api/v1/samples/{sample_id}/latest/files",
            headers=headers,
        )
    data = response.json().get("files", [])
    output_files = {
        d["filename"]: models.RemoteFile(
            filename=d["filename"],
            sample_id=d["sample_id"],
            run_id=d["run_id"],
        )
        for d in data
    }
    logger.debug(f"{output_files=}")
    if latest:
        max_run_id = max(output_file.run_id for output_file in output_files.values())
        output_files = {k: v for k, v in output_files.items() if v.run_id == max_run_id}
    return output_files


def fetch_amplicon_schemes(host: str | None = None) -> list[str]:
    """Fetch valid amplicon schemes from the server.

    Returns:
        list[str]: List of valid amplicon schemes.
    """
    with httpx.Client(event_hooks=httpx_hooks) as client:
        response = request_with_redirects(
            client,
            "GET",
            f"{env.get_protocol()}://{env.get_host(host)}/api/v1/amplicon_schemes",
        )
    if response.is_error:
        logger.error(f"Amplicon schemes could not be fetched from {env.get_host(host)}")
        raise RuntimeError(
            f"Amplicon schemes could not be fetched from the {env.get_host(host)}. Please try again later."
        )
    return [val for val in response.json()["amplicon_schemes"] if val is not None]


def fetch_credit_balance(host: str) -> None:
    """Get the credit balance for the user.

    Args:
        host (str): The host server.
    """
    logger.info(f"Getting credit balance for {host}")
    with httpx.Client(
        event_hooks=httpx_hooks,
        transport=httpx.HTTPTransport(retries=5),
        timeout=15,
    ) as client:
        response = request_with_redirects(
            client,
            "GET",
            f"{env.get_protocol()}://{host}/api/v1/credits/balance",
            headers={"Authorization": f"Bearer {env.get_access_token(host)}"},
        )
        logger.info(f"Your remaining account balance is {response.text} credits")
        if response.status_code == 200:
            echo(
                f"Your remaining account balance is {style(response.text, bold=True)} credits"
            )
        elif response.status_code == 402:
            logger.error("Customer doesn't have enough credits")
            secho(
                "Your account doesn't have enough credits to fulfil the number of Samples in your Batch",
                fg="red",
                err=True,
            )


def fetch_sample(sample_id: str, host: str) -> dict:
    """Fetch sample data from the server.

    Args:
        sample_id (str): The sample ID.
        host (str): The host server.

    Returns:
        dict: The sample data.
    """
    headers = {"Authorization": f"Bearer {env.get_access_token(host)}"}
    with httpx.Client(
        event_hooks=httpx_hooks,
        transport=httpx.HTTPTransport(retries=5),
    ) as client:
        response = request_with_redirects(
            client,
            "GET",
            f"{env.get_protocol()}://{host}/api/v1/samples/{sample_id}",
            headers=headers,
        )
    return response.json()
