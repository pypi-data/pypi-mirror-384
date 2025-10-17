from __future__ import annotations

import logging
import os
from pathlib import Path

import requests
import typer

from module_qc_database_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    LogLevel,
    Protocol,
)
from module_qc_database_tools.cli.utils import (
    get_dbs_or_client,
    load_localdb_config_from_hw,
)
from module_qc_database_tools.db.prod import get_component

log = logging.getLogger(__name__)
app = typer.Typer(context_settings=CONTEXT_SETTINGS)


# pylint: disable=duplicate-code
@app.command()
def main(
    serial_number: str = OPTIONS["serial_number"],
    itkdb_access_code1: str = OPTIONS["itkdb_access_code1"],
    itkdb_access_code2: str = OPTIONS["itkdb_access_code2"],
    tags: list[str] = OPTIONS["tags"],
    host: str = OPTIONS["host"],
    port: int = OPTIONS["port"],
    protocol: Protocol = OPTIONS["protocol"],
    verify_ssl: bool = OPTIONS["verify_ssl"],
    _verbosity: LogLevel = OPTIONS["verbosity"],
    config_hw: Path = OPTIONS["config_hw"],
):
    """Assign tags to a module. Tags do not have to be pre-defined. Detach a tag by assigning it twice."""
    itkdb_access_code1 = itkdb_access_code1 or os.environ.get("ITKDB_ACCESS_CODE1")
    itkdb_access_code2 = itkdb_access_code2 or os.environ.get("ITKDB_ACCESS_CODE2")

    hw_config_data = load_localdb_config_from_hw(config_hw)
    if hw_config_data:
        host = hw_config_data.get("host", host)
        port = hw_config_data.get("port", port)
        protocol = Protocol(hw_config_data.get("protocol", protocol.value))
        # Merge tags from config with CLI tags
        config_tags = hw_config_data.get("tags", [])
        tags = list(set(tags + config_tags))
        serial_number = hw_config_data.get("serial_number", serial_number)
        itkdb_access_code1 = hw_config_data.get(
            "itkdb_access_code1", itkdb_access_code1
        )
        itkdb_access_code2 = hw_config_data.get(
            "itkdb_access_code2", itkdb_access_code2
        )

    client, _ = get_dbs_or_client(
        itkdb_access_code1=itkdb_access_code1,
        itkdb_access_code2=itkdb_access_code2,
    )

    component, _ = get_component(client, serial_number)

    myid = component.get("id")

    url = f"{protocol.value}://{host}:{port}/localdb/assign_tag"

    for tag in tags:
        data = {"componentid": myid, "tag_name": tag}

        try:
            response = requests.post(
                url,
                data=data,
                verify=verify_ssl,
                timeout=60,
            )
            log.info(response.json())
        except Exception as err:
            log.error("POST failed: %s", err)

            raise typer.Exit(1) from err


if __name__ == "__main__":
    typer.run(main)
