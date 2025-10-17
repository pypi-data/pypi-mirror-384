from __future__ import annotations

import logging

import typer
from bson.objectid import ObjectId
from rich import print as rich_print

from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS, Protocol
from module_qc_database_tools.recycle import recycle_analysis
from module_qc_database_tools.utils import check_localdb_version

app = typer.Typer(context_settings=CONTEXT_SETTINGS)
log = logging.getLogger(__name__)


@app.command()
def main(
    test_run_id: ObjectId = OPTIONS["test_run_id"],
    host: str = OPTIONS["host"],
    port: int = OPTIONS["port"],
    protocol: Protocol = OPTIONS["protocol"],
    is_complex_analysis: bool = OPTIONS["is_complex_analysis"],
):
    """
    Main executable for recycling a single analysis.
    \f
    !!! note "Added in version 2.5.1"

    """
    localdb_uri = f"{protocol.value}://{host}:{port}/localdb/"

    check_localdb_version(localdb_uri)

    try:
        status, message = recycle_analysis(
            test_run_id,
            localdb_uri=localdb_uri,
            is_complex_analysis=is_complex_analysis,
        )
    except ValueError as exc:
        rich_print(f":warning: [red bold]Error[/]: {exc}")
        raise typer.Exit(2) from exc

    if not status:
        rich_print(f":cross_mark: [red bold]Error[/]: {message}")
        raise typer.Exit(1)

    rich_print("[green]Recycled successfully.[/]")


if __name__ == "__main__":
    typer.run(main)
