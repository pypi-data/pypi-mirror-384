from __future__ import annotations

import logging

import typer
from rich import print as rich_print
from rich.tree import Tree

from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS, Protocol
from module_qc_database_tools.cli.utils import get_dbs_or_client
from module_qc_database_tools.recycle import recycle_component
from module_qc_database_tools.utils import check_localdb_version, console

app = typer.Typer(context_settings=CONTEXT_SETTINGS)
log = logging.getLogger(__name__)


@app.command()
def main(
    serial_number: str = OPTIONS["serial_number"],
    mongo_serverSelectionTimeout: int = OPTIONS["mongo_serverSelectionTimeout"],
    mongo_uri: str = OPTIONS["mongo_uri"],
    localdb_name: str = OPTIONS["localdb_name"],
    userdb_name: str = OPTIONS["userdb_name"],
    host: str = OPTIONS["host"],
    port: int = OPTIONS["port"],
    protocol: Protocol = OPTIONS["protocol"],
    stage: str = OPTIONS["stage"],
):
    """
    Main executable for bulk recycling a module entirely for each individual e-summary.
    \f
    !!! note "Added in version 2.5.0"

    !!! note "Changed in version 2.5.1"

        This was changed to recycle at the E-SUMMARY level, rather than individual analyses.

    """
    # pylint: disable=duplicate-code
    client, _ = get_dbs_or_client(
        localdb=True,
        mongo_serverSelectionTimeout=mongo_serverSelectionTimeout,
        mongo_uri=mongo_uri,
        localdb_name=localdb_name,
        userdb_name=userdb_name,
    )

    localdb_uri = f"{protocol.value}://{host}:{port}/localdb/"

    check_localdb_version(localdb_uri)

    try:
        overall_status, results = recycle_component(
            client,
            serial_number,
            localdb_uri=localdb_uri,
            stage=None if stage == "all" else stage,
        )
    except ValueError as exc:
        rich_print(f":warning: [red bold]Error[/]: {exc}")
        raise typer.Exit(2) from exc

    tree = Tree(
        f"{':white_check_mark:' if overall_status else ':cross_mark:'} Recycling Statuses for {serial_number}"
    )

    for this_stage, (status, message) in results.items():
        if status:
            tree.add(f":white_check_mark: Stage: {this_stage}: [yellow]{message}[/]")
        else:
            tree.add(f":cross_mark: Stage: {this_stage}: [red bold]{message}[/]")

    console.print(tree)

    if not overall_status:
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(main)
