from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import jsbeautifier
import typer
from rich import print as rich_print

from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS
from module_qc_database_tools.cli.utils import get_dbs_or_client
from module_qc_database_tools.iv import fetch_reference_ivs

app = typer.Typer(context_settings=CONTEXT_SETTINGS)
log = logging.getLogger(__name__)


@app.command()
def main(
    serial_number: str = OPTIONS["serial_number"],
    output_file: Optional[Path] = OPTIONS["output_file"],  # noqa: UP045
    mongo_uri: str = OPTIONS["mongo_uri"],
    localdb_name: str = OPTIONS["localdb_name"],
    itkdb_access_code1: Optional[str] = OPTIONS["itkdb_access_code1"],  # noqa: UP045
    itkdb_access_code2: Optional[str] = OPTIONS["itkdb_access_code2"],  # noqa: UP045
    localdb: bool = OPTIONS["localdb"],
    mongo_serverSelectionTimeout: int = OPTIONS["mongo_serverSelectionTimeout"],
    reference_component_type: Optional[str] = typer.Option(  # noqa: UP045
        None,
        "-c",
        "--reference-component-type",
        help="Component Type to use as reference",
    ),
    reference_stage: Optional[str] = typer.Option(  # noqa: UP045
        None, "-s", "--reference-stage", help="Stage to use as reference"
    ),
    reference_test_type: Optional[str] = typer.Option(  # noqa: UP045
        None, "-t", "--reference-test-type", help="Test Type to use as reference"
    ),
):
    """
    Main executable for fetching reference IVs from either production DB (default) or local DB.

    !!! note "Added in version 2.3.0"

    """
    # pylint: disable=duplicate-code
    client, _ = get_dbs_or_client(
        localdb=localdb,
        mongo_serverSelectionTimeout=mongo_serverSelectionTimeout,
        mongo_uri=mongo_uri,
        localdb_name=localdb_name,
        itkdb_access_code1=itkdb_access_code1,
        itkdb_access_code2=itkdb_access_code2,
    )

    try:
        reference_ivs = fetch_reference_ivs(
            client,
            serial_number,
            reference_component_type=reference_component_type,
            reference_stage=reference_stage,
            reference_test_type=reference_test_type,
        )
    except ValueError as exc:
        rich_print(f":warning: [red bold]Error[/]: {exc}")
        raise typer.Exit(2) from exc

    json_data = json.dumps(reference_ivs, sort_keys=True)
    options = jsbeautifier.default_options()
    options.indent_size = 4
    pretty_json_data = jsbeautifier.beautify(json_data, options)

    if output_file:
        output_file.write_text(pretty_json_data)
        msg = f"Written to {output_file!s}"
        log.info(msg)
    else:
        rich_print(pretty_json_data)


if __name__ == "__main__":
    typer.run(main)
