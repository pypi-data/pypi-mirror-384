from pathlib import Path

import httpx
from hostile.lib import ALIGNER
from hostile.util import BUCKET_URL, CACHE_DIR
from rich_click import secho
from tenacity import retry, stop_after_attempt, wait_random_exponential
from tqdm import tqdm

from gpas import models, util
from gpas.client import env
from gpas.constants import DEFAULT_HOST, HOSTILE_INDEX_NAME
from gpas.errors import MissingError
from gpas.http_helpers import request_with_redirects, stream_with_redirects
from gpas.log_utils import httpx_hooks, logger
from gpas.tasks.query import (
    check_version_compatibility,
    fetch_output_files,
    fetch_sample,
    parse_csv,
)


def download(
    samples: str | None = None,
    mapping_csv: Path | None = None,
    filenames: str = "main_report.json",
    inputs: bool = False,
    out_dir: Path = Path("."),
    rename: bool = True,
    host: str = DEFAULT_HOST,
) -> None:
    """Download the latest output files for a sample.

    Args:
        samples (str | None): A comma-separated list of sample IDs.
        mapping_csv (Path | None): The path to a CSV file containing sample mappings.
        filenames (str): A comma-separated list of filenames to download. Defaults to "main_report.json".
        inputs (bool): Whether to download input files as well. Defaults to False.
        out_dir (Path): The directory to save the downloaded files. Defaults to the current directory.
        rename (bool): Whether to rename the downloaded files based on the sample name. Defaults to True.
        host (str): The host server. Defaults to DEFAULT_HOST.
    """
    check_version_compatibility(host)
    headers = {"Authorization": f"Bearer {env.get_access_token(host)}"}
    if mapping_csv:
        sample_records = parse_csv(Path(mapping_csv))
        logger.info(f"Using samples in {mapping_csv}")
        secho(f"Using samples in {mapping_csv}")
    elif samples:
        sample_records = [
            {
                "remote_sample_name": sample_id,
                "sample_name": None,
                "pipeline_version": None,
            }
            for sample_id in util.parse_comma_separated_string(samples)
        ]
        logger.info(f"Using guids {samples}")
        secho(f"Using guids {samples}")
    else:
        raise RuntimeError("Specify either a list of samples or a mapping CSV")

    unique_filenames: set[str] = util.parse_comma_separated_string(filenames)

    for sample_record in sample_records:
        sample_id: str | None = sample_record.get("remote_sample_name")

        if sample_id is None:
            logger.warning("Skipping record with missing 'remote_sample_name'")
            continue

        sample_name: str | None = sample_record.get("sample_name")
        pipeline_version: str | None = sample_record.get("pipeline_version")

        if pipeline_version is None:
            # Try to fetch the pipeline_version if not provided in the CSV for backwards compatibility
            try:
                sample = fetch_sample(sample_id=sample_id, host=host)
                pipeline_version = sample["pipeline_version"]
                logger.info(
                    f"Fetched pipeline_version for {sample_id}: {pipeline_version}"
                )
            except Exception as e:
                logger.warning(f"Could not fetch pipeline_version for {sample_id}: {e}")

        logger.info(
            f"sample_id: {sample_id}, sample_name: {sample_name}, pipeline_version: {pipeline_version}"
        )

        if pipeline_version is None:
            pipeline_version = ""

        try:
            output_files = fetch_output_files(
                sample_id=sample_id, host=host, latest=True
            )
            output_files_without_version = {
                key.replace(f"_v{pipeline_version}", "").replace(
                    f".v{pipeline_version}", ""
                ): val
                for key, val in output_files.items()
            }
        except MissingError:
            output_files_without_version = {}  # There are no output files. The run may have failed.

        with httpx.Client(
            event_hooks=httpx_hooks,
            transport=httpx.HTTPTransport(retries=5),
            timeout=7200,  # 2 hours
        ) as client:
            for filename in unique_filenames:
                prefixed_filename = f"{sample_id}_{filename}"
                if prefixed_filename in output_files_without_version:
                    output_file = output_files_without_version[prefixed_filename]
                    url = (
                        f"{env.get_protocol()}://{host}/api/v1/"
                        f"samples/{output_file.sample_id}/"
                        f"runs/{output_file.run_id}/"
                        f"files/{prefixed_filename}"
                    )
                    if rename and mapping_csv:
                        replaced_filename = output_file.filename.replace(
                            f"{sample_id}.", ""
                        ).replace(f"{sample_id}_", "")
                        filename_fmt = f"{sample_name}.{replaced_filename}"
                    else:
                        filename_fmt = output_file.filename
                    download_single(
                        client=client,
                        filename=filename_fmt,
                        url=url,
                        headers=headers,
                        out_dir=Path(out_dir),
                    )
                elif set(
                    filter(None, filenames)
                ):  # Skip case where filenames = set("")
                    logger.warning(
                        f"Skipped {sample_name if sample_name and rename else sample_id}.{filename}"
                    )
                    secho(
                        f"Skipped {sample_name if sample_name and rename else sample_id}.{filename}",
                        fg="yellow",
                    )
            if inputs:
                input_files = fetch_latest_input_files(sample_id=sample_id, host=host)
                for input_file in input_files.values():
                    if rename and mapping_csv:
                        suffix = input_file.filename.partition(".")[2]
                        filename_fmt = f"{sample_name}.{suffix}"
                    else:
                        filename_fmt = input_file.filename
                    url = (
                        f"{env.get_protocol()}://{host}/api/v1/"
                        f"samples/{input_file.sample_id}/"
                        f"runs/{input_file.run_id}/"
                        f"input-files/{input_file.filename}"
                    )
                    download_single(
                        client=client,
                        filename=filename_fmt,
                        url=url,
                        headers=headers,
                        out_dir=Path(out_dir),
                    )


@retry(wait=wait_random_exponential(multiplier=2, max=60), stop=stop_after_attempt(10))
def download_single(
    client: httpx.Client,
    url: str,
    filename: str,
    headers: dict[str, str],
    out_dir: Path,
) -> None:
    """Download a single file from the server with retries.

    Args:
        client (httpx.Client): The HTTP client to use for the request.
        url (str): The URL of the file to download.
        filename (str): The name of the file to save.
        headers (dict[str, str]): The headers to include in the request.
        out_dir (Path): The directory to save the downloaded file.
    """
    logger.info(f"Downloading {filename}")
    secho(f"Downloading {filename}")
    try:
        with stream_with_redirects(client, url=url, headers=headers) as r:
            file_size = int(r.headers.get("content-length", 0))
            chunk_size = 262_144
            with (
                Path(out_dir).joinpath(f"{filename}").open("wb") as fh,
                tqdm(
                    total=file_size,
                    unit="B",
                    unit_scale=True,
                    desc=filename,
                    leave=False,  # Works only if using a context manager
                    position=0,  # Avoids leaving line break with leave=False
                ) as progress,
            ):
                for data in r.iter_bytes(chunk_size):
                    fh.write(data)
                    progress.update(len(data))
        logger.debug(f"Downloaded {filename}")
        secho(f"Downloaded {filename}", fg="green")
    except Exception as exc:
        logger.error(exc)
        secho(
            f"Something went wrong downloading {filename}",
            fg="red",
            bold=True,
            err=True,
        )


def download_index(name: str = HOSTILE_INDEX_NAME) -> None:
    """Download and cache the host decontamination index.

    Args:
        name (str): The name of the index. Defaults to HOSTILE_INDEX_NAME.
    """
    logger.info(f"Cache directory: {CACHE_DIR}")
    logger.info(f"Manifest URL: {BUCKET_URL}/manifest.json")
    ALIGNER.minimap2.value.check_index(name)
    ALIGNER.bowtie2.value.check_index(name)


def fetch_latest_input_files(sample_id: str, host: str) -> dict[str, models.RemoteFile]:
    """Return models.RemoteFile instances for a sample input files.

    Args:
        sample_id (str): The sample ID.
        host (str): The host server.

    Returns:
        dict[str, models.RemoteFile]: The latest input files.
    """
    headers = {"Authorization": f"Bearer {env.get_access_token(host)}"}
    with httpx.Client(
        event_hooks=httpx_hooks,
        transport=httpx.HTTPTransport(retries=5),
    ) as client:
        response = request_with_redirects(
            client,
            "GET",
            f"{env.get_protocol()}://{host}/api/v1/samples/{sample_id}/latest/input-files",
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
    return output_files
