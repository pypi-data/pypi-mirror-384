import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from gpas import __version__ as version


def test_cli_help_override(cli_main) -> None:
    """Test the CLI help command.

    This test ensures that the help message for the 'upload' command is displayed correctly.
    """
    runner = CliRunner()
    result = runner.invoke(cli_main, ["upload", "-h"])
    assert result.exit_code == 0


def test_cli_version(cli_main) -> None:
    """Test the CLI version command.

    This test ensures that the version of the CLI is displayed correctly.
    """
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--version"])
    assert result.exit_code == 0
    assert version in result.output


@pytest.mark.slow
def test_cli_decontaminate_illumina(cli_main, illumina_sample_csv: Path) -> None:
    """Test the CLI decontaminate command for Illumina samples.

    Args:
        illumina_sample_csv (Path): Path to the Illumina sample CSV file.
    """
    runner = CliRunner()
    result = runner.invoke(cli_main, ["decontaminate", str(illumina_sample_csv)])
    assert result.exit_code == 0
    for f in os.listdir("."):
        if f.endswith(".fastq.gz"):
            os.remove(f)


@pytest.mark.slow
def test_cli_decontaminate_illumina_with_extended_name(
    cli_main, illumina_extended_sample_csv: Path
) -> None:
    """Test the CLI decontaminate command for Illumina samples that contain multiple instances of _1_1_....

    Args:
        illumina_sample_csv (Path): Path to the Illumina sample CSV file.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli_main,
        ["decontaminate", str(illumina_extended_sample_csv), "--output-dir", "."],
    )
    assert os.path.isfile("tuberculosis_1_1_1.clean_1.fastq.gz")
    assert os.path.isfile("tuberculosis_1_1_1.clean_2.fastq.gz")
    assert result.exit_code == 0
    for f in os.listdir("."):
        if f.endswith(".fastq.gz"):
            os.remove(f)


@pytest.mark.slow
def test_cli_decontaminate_illumina_with_output_dir(
    cli_main, illumina_sample_csv: Path
) -> None:
    """Test the CLI decontaminate command for Illumina samples with an output directory.

    Args:
        illumina_sample_csv (Path): Path to the Illumina sample CSV file.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli_main, ["decontaminate", str(illumina_sample_csv), "--output-dir", "."]
    )
    assert result.exit_code == 0
    for f in os.listdir("."):
        if f.endswith(".fastq.gz"):
            os.remove(f)


@pytest.mark.slow
def test_cli_fail_decontaminate_output_dir(cli_main, illumina_sample_csv: Path) -> None:
    """Test the CLI decontaminate command failure with a non-existent output directory.

    Args:
        illumina_sample_csv (Path): Path to the Illumina sample CSV file.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli_main,
        ["decontaminate", str(illumina_sample_csv), "--output-dir", "totallyfakedir"],
    )
    assert result.exit_code != 0
    assert (
        "Directory 'totallyfakedir' does not exist" in result.stdout
        or "Directory 'totallyfakedir' does not exist" in result.stderr
    )


def test_cli_fail_upload_output_dir(cli_main, illumina_sample_csv: Path) -> None:
    """Test the CLI upload command failure with a non-existent output directory.

    Args:
        illumina_sample_csv (Path): Path to the Illumina sample CSV file.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli_main, ["upload", str(illumina_sample_csv), "--output-dir", "totallyfakedir"]
    )
    assert result.exit_code != 0
    assert (
        "Directory 'totallyfakedir' does not exist" in result.stdout
        or "Directory 'totallyfakedir' does not exist" in result.stderr
    )


def test_cli_fail_download_output_dir(cli_main, illumina_sample_csv: Path) -> None:
    """Test the CLI download command failure with a non-existent output directory.

    Args:
        illumina_sample_csv (Path): Path to the Illumina sample CSV file.
    """
    runner = CliRunner()
    result = runner.invoke(cli_main, ["download", "--output-dir", "totallyfakedir"])
    assert result.exit_code != 0
    assert (
        "Directory 'totallyfakedir' does not exist" in result.stdout
        or "Directory 'totallyfakedir' does not exist" in result.stderr
    )


def test_validation_fail_control(cli_main, invalid_control_csv: Path) -> None:
    """Test validation failure for control CSV.

    Args:
        invalid_control_csv (Path): Path to the invalid control CSV file.
    """
    runner = CliRunner()
    result = runner.invoke(cli_main, ["validate", str(invalid_control_csv)])
    assert result.exit_code == 1
    assert result.exc_info is not None
    assert result.exc_info[0] == ValidationError
    assert "Input should be 'positive', 'negative' or ''" in str(result.exc_info)


@patch("gpas.tasks.get_pipeline_version", return_value="2.4.1")
def test_build_csv_specimen_organism(cli_main, reads: Path) -> None:
    """Test building a CSV with a specimen organism via the CLI.

    This test is present because the build_csv() function uses a different
    variable name (`pipeline`) for specimen organism.

    Args:
        reads (Path): Path to a reads folder containing `fastq` and `fastq.gz` files.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir) / "test_ont.csv"

        runner = CliRunner()
        result = runner.invoke(
            cli_main,
            [
                "build-csv",
                "--output-csv",
                str(temp_file_path),
                "--batch-name",
                "test_ont",
                "--country",
                "GBR",
                "--instrument-platform",
                "ont",
                str(reads),
            ],
        )
        assert result.exit_code == 0
