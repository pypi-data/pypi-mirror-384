import hostile
import httpx

import gpas
from gpas.client import env
from gpas.http_helpers import request_with_redirects
from gpas.log_utils import httpx_hooks, logger
from gpas.models import UploadBatch


def validate_csv(host: str, batch: UploadBatch):
    """Validates the CSV prior to upload.

    Calls `/validate_creation` in Portal to validate payload - endpoint returns 422 if issues are found.

    Args:
        batch (models.UploadBatch): The batch of samples to decontaminate
        host (str): The host server.

    Returns:
        None
    """
    instrument_platform = batch.samples[0].instrument_platform
    collection_date = batch.samples[0].collection_date
    country = batch.samples[0].country
    telemetry_data = {
        "client": {
            "name": "pathogena-client",
            "version": gpas.__version__,
        },
        "decontamination": {
            "name": "hostile",
            "version": hostile.__version__,
        },
        "specimen_organism": batch.samples[0].specimen_organism,
    }

    local_batch_name = (
        batch.samples[0].batch_name
        if batch.samples[0].batch_name not in ["", " ", None]
        else f"batch_{collection_date}"
    )
    data = {
        "collection_date": str(collection_date),
        "instrument": instrument_platform,
        "country": country,
        "name": local_batch_name,
        "amplicon_scheme": batch.amplicon_scheme,
        "telemetry_data": telemetry_data,
    }
    try:
        with httpx.Client(
            event_hooks=httpx_hooks,
            transport=httpx.HTTPTransport(retries=5),
            timeout=60,
        ) as client:
            validation_response = request_with_redirects(
                client,
                "POST",
                f"{env.get_protocol()}://{host}/api/v1/batches/validate_creation",
                headers={
                    "Authorization": f"Bearer {env.get_access_token(host)}",
                    "accept": "application/json",
                },
                json=data,
            )
        assert validation_response.status_code == 200
    except AssertionError:
        logger.error(
            f"Unexpected response code from CSV validation. Response: {validation_response}"
        )
        exit(1)
