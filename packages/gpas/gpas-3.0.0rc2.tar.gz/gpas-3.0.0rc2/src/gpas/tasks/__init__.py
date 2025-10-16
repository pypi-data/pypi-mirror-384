"""Init file containing all tasks that can be run from the CLI interface."""

from gpas.tasks.authentication import authenticate, check_authentication
from gpas.tasks.download import (
    download,
    download_index,
    download_single,
    fetch_latest_input_files,
)
from gpas.tasks.prep_samples import (
    build_upload_csv,
    decontaminate_samples_with_hostile,
    generate_output_dir,
    validate_upload_permissions,
)
from gpas.tasks.query import (
    check_for_newer_version,
    check_version_compatibility,
    fetch_amplicon_schemes,
    fetch_credit_balance,
    fetch_output_files,
    fetch_sample,
    fetch_sample_metadata,
    fetch_sample_status,
    parse_csv,
)
from gpas.tasks.upload import (
    create_batch_on_server,
    get_pipeline_version,
    get_pipeline_versions,
    prepare_sample,
    prepare_upload_files,
    remove_empty_dir,
    remove_file,
    start_upload_session,
    upload_batch,
    upload_file,
    upload_samples,
)
from gpas.tasks.validate import validate_csv

__all__ = [
    "fetch_sample_metadata",
    "fetch_sample_status",
    "parse_csv",
    "check_version_compatibility",
    "check_for_newer_version",
    "fetch_output_files",
    "fetch_amplicon_schemes",
    "fetch_credit_balance",
    "authenticate",
    "check_authentication",
    "download",
    "download_single",
    "download_index",
    "fetch_latest_input_files",
    "fetch_latest_input_files",
    "fetch_sample",
    "prepare_upload_files",
    "upload_batch",
    "get_pipeline_version",
    "create_batch_on_server",
    "upload_samples",
    "upload_file",
    "start_upload_session",
    "prepare_sample",
    "remove_empty_dir",
    "remove_file",
    "build_upload_csv",
    "decontaminate_samples_with_hostile",
    "validate_upload_permissions",
    "validate_csv",
    "generate_output_dir",
    "get_pipeline_versions",
]
