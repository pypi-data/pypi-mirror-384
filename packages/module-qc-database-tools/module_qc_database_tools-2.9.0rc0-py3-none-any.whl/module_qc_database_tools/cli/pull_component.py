from __future__ import annotations

import json
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
from module_qc_database_tools.cli.utils import load_localdb_config_from_hw

log = logging.getLogger(__name__)
app = typer.Typer(context_settings=CONTEXT_SETTINGS)


# pylint: disable=duplicate-code
@app.command()
def main(
    serial_numbers: list[str] = OPTIONS["serial_numbers"],
    host: str = OPTIONS["host"],
    port: int = OPTIONS["port"],
    protocol: Protocol = OPTIONS["protocol"],
    verify_ssl: bool = OPTIONS["verify_ssl"],
    fastrun: bool = OPTIONS["fast-run"],
    fullrun: bool = OPTIONS["full-run"],
    user_name: str = OPTIONS["user_name"],
    user_pass: str = OPTIONS["user_pass"],
    itkdb_access_code1: str = OPTIONS["itkdb_access_code1"],
    itkdb_access_code2: str = OPTIONS["itkdb_access_code2"],
    _verbosity: LogLevel = OPTIONS["verbosity"],
    config_hw: Path = OPTIONS["config_hw"],
):
    """Pull components from the PDB to Local DB."""
    itkdb_access_code1 = itkdb_access_code1 or os.environ.get("ITKDB_ACCESS_CODE1")
    itkdb_access_code2 = itkdb_access_code2 or os.environ.get("ITKDB_ACCESS_CODE2")

    hw_config_data = load_localdb_config_from_hw(config_hw)
    if hw_config_data:
        host = hw_config_data.get("host", host)
        port = hw_config_data.get("port", port)
        protocol = Protocol(hw_config_data.get("protocol", protocol.value))
        # Merge SNs from config with CLI SNs
        config_serial_numbers = hw_config_data.get("serial_numbers", [])
        serial_numbers = list(set(serial_numbers + config_serial_numbers))
        user_name = hw_config_data.get("userName", user_name)
        itkdb_access_code1 = hw_config_data.get(
            "itkdb_access_code1", itkdb_access_code1
        )
        itkdb_access_code2 = hw_config_data.get(
            "itkdb_access_code2", itkdb_access_code2
        )

    s = requests.Session()
    url_login = f"{protocol.value}://{host}:{port}/localdb/login"
    login_data = {
        "username": user_name,
        "password": user_pass,
    }
    response = s.post(
        url_login,
        data=login_data,
        headers={"Referer": url_login},
        verify=verify_ssl,
    )

    url = f"{protocol.value}://{host}:{port}/localdb/download_component"
    pullmode = "submit"
    if fastrun:
        pullmode = "submit|skipAtt"
    elif fullrun:
        pullmode = "submit|noSkipSynched"
    component_ids = json.dumps([{"value": sn} for sn in serial_numbers])
    data = {
        "stage": pullmode,
        "code1": itkdb_access_code1,
        "code2": itkdb_access_code2,
        "component_ids": component_ids,
    }

    try:
        response = s.post(
            url,
            data=data,
            verify=verify_ssl,
            timeout=60,
        )
        response.raise_for_status()
        html_preview = response.text[:200].replace("\n", " ")
        data = {"html_response": html_preview}
        log.info(data)

    except Exception as err:
        log.error("POST failed: %s", err)

        raise typer.Exit(1) from err


if __name__ == "__main__":
    typer.run(main)
