from __future__ import annotations

import json
import os
from pathlib import Path

import itkdb
import typer

import module_qc_database_tools
from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    serial_number: str = typer.Option(..., "-sn", "--sn", help="ATLAS serialNumber"),
    config_path: Path = typer.Option(
        (module_qc_database_tools.data / "componentConfigs.json").resolve(),
        "-c",
        "--config",
        help="component configs for registering components",
        exists=True,
        file_okay=True,
        readable=True,
        resolve_path=True,
    ),
    component: str = typer.Option(
        ...,
        "-cp",
        "--component",
        help="Component to register",
    ),
    institution: str = typer.Option("", "-i", "--institution", help="Institution"),
):
    """
    Main executable for registering components.
    """
    config = json.loads(config_path.read_text())[component]

    institution = institution or os.environ.get("INSTITUTION")
    if not institution:
        msg = "Must specify institution from commandline or set the appropriate environment variable."
        raise ValueError(msg)

    client = itkdb.Client()
    register_component(client, institution, config, serial_number)


def register_component(client, institution, config, serial_number):
    """
    Register a component in production database using institution, config, and serial number
    """
    config["institution"] = institution
    config["serialNumber"] = serial_number
    client.post("registerComponent", json=config)


if __name__ == "__main__":
    typer.run(main)
