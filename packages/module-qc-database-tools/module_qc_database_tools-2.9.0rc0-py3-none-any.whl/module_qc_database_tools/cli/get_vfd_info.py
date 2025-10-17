from __future__ import annotations

import logging
from typing import Optional

import typer

from module_qc_database_tools import db
from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS
from module_qc_database_tools.cli.utils import get_dbs_or_client

app = typer.Typer(context_settings=CONTEXT_SETTINGS)
log = logging.getLogger(__name__)


@app.command()
def get_vfd_info(
    serial_number: str = OPTIONS["serial_number"],
    mongo_uri: str = OPTIONS["mongo_uri"],
    localdb_name: str = OPTIONS["localdb_name"],
    itkdb_access_code1: Optional[str] = OPTIONS["itkdb_access_code1"],  # noqa: UP045
    itkdb_access_code2: Optional[str] = OPTIONS["itkdb_access_code2"],  # noqa: UP045
    localdb: bool = OPTIONS["localdb"],
    mongo_serverSelectionTimeout: int = OPTIONS["mongo_serverSelectionTimeout"],
):
    """
    Main executable for get Vfd Information
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

    get_full_depletion_voltage = (
        db.local.get_full_depletion_voltage
        if localdb
        else db.prod.get_full_depletion_voltage
    )
    vfd = get_full_depletion_voltage(client, serial_number)

    if not vfd:
        log.warning("Full depletion Voltage was not found")

    typer.echo(vfd)


if __name__ == "__main__":
    typer.run(get_vfd_info)
