from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import itksn
import jsbeautifier
import typer
from module_qc_data_tools.utils import (
    chip_uid_to_serial_number,
    get_layer_from_sn,
)

import module_qc_database_tools
from module_qc_database_tools import db
from module_qc_database_tools.chip_config_api import ChipConfigAPI
from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS
from module_qc_database_tools.cli.utils import (
    get_dbs_or_client,
    load_localdb_config_from_hw,
)
from module_qc_database_tools.core import DPPort, LocalModule, Module

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    serial_number: str = OPTIONS["serial_number"],
    chip_template_path: Path = typer.Option(
        (module_qc_database_tools.data / "YARR" / "chip_template.json").resolve(),
        "--ch",
        "--chipTemplate",
        help="Default chip template from which the chip configs are generated.",
        exists=True,
        file_okay=True,
        readable=True,
        resolve_path=True,
    ),
    output_dir: Optional[Path] = typer.Option(  # noqa: UP045
        None,
        "-o",
        "--outdir",
        help="Path to output directory. If not specified, will store configs in mongodb.",
        exists=False,
        writable=True,
    ),
    modes: list[str] = typer.Option(
        ["warm", "cold", "LP"],
        "-m",
        "--mode",
        help="Modes to generate configs for.",
    ),
    dp_port: DPPort = typer.Option(
        DPPort.A,
        "-p",
        "--port",
        "--dp",
        help="Select DisplayPort on PCIe card that connectivity file will be written for.",
    ),
    version: str = typer.Option(
        "latest",  ## TODO: ["latest", "TESTONWAFER", "MODULE/INITIAL_WARM", ...], ## use stage/test names?
        "-v",
        "--version",
        help="Generate chip configs, default is 'latest'. Possible choices: 'TESTONWAFER', 'latest'",
    ),
    data_merging: list[str] = typer.Option(
        None,
        "--dm",
        "--data-merging",
        help="Data merging mode: '4-to-1' or '2-to-1'",
    ),
    use_current_stage: bool = typer.Option(
        False,
        "--use-current-stage/--use-initial-warm",
        help="From localDB, get the current module stage, generate, and upload the config to the current stage (enabled) or INITIAL_WARM (default).",
    ),
    speed: int = typer.Option(
        1280,
        "-s",
        "--speed",
        help="Readout speed in MHz. Possible choices: [1280, 640, 320, 160] MHz.",
    ),
    layer: str = typer.Option(
        "Unknown",
        "-l",
        "--layer",
        help="Layer of module, used for applying correct QC criteria settings. Options: R0, R0.5, L0, L1, L2 (default is automatically determined from the module SN)",
    ),
    mongo_uri: str = OPTIONS["mongo_uri"],
    localdb_name: str = OPTIONS["localdb_name"],
    itkdb_access_code1: Optional[str] = OPTIONS["itkdb_access_code1"],  # noqa: UP045
    itkdb_access_code2: Optional[str] = OPTIONS["itkdb_access_code2"],  # noqa: UP045
    localdb: bool = OPTIONS["localdb"],
    mongo_serverSelectionTimeout: int = OPTIONS["mongo_serverSelectionTimeout"],
    fast: bool = typer.Option(
        False, "-f", "--fast", help="Fast generation of YARR config, no formatting."
    ),
    no_eos_token: bool = typer.Option(False, "--noeos", help="Do not use eos token"),
    reverse: bool = typer.Option(
        False,
        "--reverse",
        help="Use reversed order of chip ID, e.g. for old L0 linear triplets.",
    ),
    config_hw: Path = OPTIONS["config_hw"],
):
    """
    Main executable for generating yarr config.

    The mongo URI/localdb options can be configured in the hardware configuration file.
    """
    # pylint: disable=duplicate-code

    # Load hardware config and override parameters if provided
    hw_config_data = load_localdb_config_from_hw(config_hw)
    if hw_config_data:
        mongo_uri = hw_config_data.get("mongo_uri", mongo_uri)
        localdb_name = hw_config_data.get("localdb_name", localdb_name)

    client, _ = get_dbs_or_client(
        localdb=localdb,
        mongo_serverSelectionTimeout=mongo_serverSelectionTimeout,
        mongo_uri=mongo_uri,
        localdb_name=localdb_name,
        itkdb_access_code1=itkdb_access_code1,
        itkdb_access_code2=itkdb_access_code2,
    )

    module = (
        LocalModule(client, serial_number)
        if localdb
        else Module(client, serial_number, no_eos_token)
    )

    module_info = itksn.parse(serial_number.encode("utf-8"))

    if layer == "Unknown":
        typer.echo("INFO: Getting layer-dependent config from module SN...")
        layer_config = get_layer_from_sn(serial_number, for_analysis=False)
    else:
        typer.echo(
            f"INFO: Overwriting default layer config ({layer_config}) with manual input ({layer})!"
        )
        layer_config = layer

    chip_template = json.loads(chip_template_path.read_text()) if not localdb else None

    to_generate = []

    for suffix in modes:
        if data_merging and module.module_type == "quad":
            to_generate.extend(suffix + "_" + item for item in data_merging)
        else:
            to_generate.append(suffix)

    ## suffix like warm or warm_4-to-1
    for suffix in to_generate:
        connectivity_path = Path(output_dir or "", module.name).joinpath(
            f"{module.name}_{layer_config}{'_' + suffix if suffix else ''}.json"
        )
        generated_configs = module.generate_config(
            chip_template,
            layer_config,
            dp_port.value,
            suffix=suffix,
            version=version,
            speed=speed,
            reverse=reverse,
        )

        if output_dir:
            save_configs_local(generated_configs, connectivity_path, fast)

            get_bom_info = db.local.get_bom_info if localdb else db.prod.get_bom_info
            infodata = {
                "PCB_BOM_VERSION": get_bom_info(client, serial_number),
            }

            if not any(
                item in module_info.component_code.lower()
                for item in ["digital", "dummy"]
            ):
                get_full_depletion_voltage = (
                    db.local.get_full_depletion_voltage
                    if localdb
                    else db.prod.get_full_depletion_voltage
                )
                infodata["V_FULLDEPL"] = get_full_depletion_voltage(
                    client, serial_number
                )

            connectivity_path = Path(output_dir or "", module.name).joinpath(
                f"{module.name}_info.json"
            )
            typer.echo(f"module information saved to {connectivity_path}")
            connectivity_path.write_text(
                json.dumps(infodata, indent=4), encoding="utf-8"
            )

        elif localdb:
            mongo_client = client.client
            chip_config_client = ChipConfigAPI(mongo_client, dbname=localdb_name)
            current_stage = (
                module.get_current_stage()
                if use_current_stage
                else "MODULE/INITIAL_WARM"
            )
            save_configs_mongo(
                generated_configs, chip_config_client, suffix, current_stage
            )


def save_configs_local(configs, connectivity_path, fast):
    """
    Save the configs generated to disk.
    """
    connectivity_path.parent.mkdir(parents=True, exist_ok=True)

    connectivity_path.write_text(json.dumps(configs["module"], indent=4))
    typer.echo(f"module connectivity file saved to {connectivity_path}")
    chip_type = configs["module"]["chipType"]
    for chip_config, chip_spec in zip(configs["module"]["chips"], configs["chips"]):
        ## quad chip IDs are 12/13/14/15 for FE1/2/3/4
        ## triplet chip IDs are 1/2/3 for FE1/2/3
        ## chip IDs are defined via wirebonds
        ## FEx are "defined" via silkscreen on the flex
        fe = chip_spec[chip_type]["Parameter"]["ChipId"] % 11
        output_path = connectivity_path.parent.joinpath(chip_config["config"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if fast:
            output_path.write_text(
                json.dumps(chip_spec)
            )  ## file size is 1.8M, no linebreak
        else:
            ## needed to avoid having chip config file at 14MB (but slow)
            beautified = jsbeautifier.beautify(
                json.dumps(chip_spec), jsbeautifier.default_options()
            )
            output_path.write_text(beautified)  ## file size 1.9MB
        # output_path.write_text(json.dumps(chip_spec, indent=4)) ## file size 14MB due to linebreaks

        typer.echo(f"FE{fe} config file saved to {output_path}")


def save_configs_mongo(configs, chip_config_client, mode, stage):
    """
    Save the configs generated to mongo.
    """
    chip_type = configs["module"]["chipType"]
    for chip_spec in configs["chips"]:
        chip_serial_number = chip_uid_to_serial_number(
            chip_spec[chip_type]["Parameter"]["Name"]
        )
        fe = chip_spec[chip_type]["Parameter"]["ChipId"] % 11
        base_commit_id = chip_config_client.create_config(
            chip_serial_number, stage, branch=mode
        )
        new_commit_id = chip_config_client.commit(
            base_commit_id,
            chip_spec,
            "initial generation from module-qc-database-tools",
        )
        typer.echo(
            f"FE{fe} config file saved to mongodb from {base_commit_id} ➜ {new_commit_id}"
        )


if __name__ == "__main__":
    typer.run(main)
