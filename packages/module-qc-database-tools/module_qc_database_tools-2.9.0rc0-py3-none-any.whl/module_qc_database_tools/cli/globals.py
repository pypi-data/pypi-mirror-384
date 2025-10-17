from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Optional

import itksn
import typer
from bson.objectid import ObjectId
from click.exceptions import BadParameter
from construct.core import ConstructError

from module_qc_database_tools.typing_compat import Annotated

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def sn_callback(value: str):
    """
    Callback to check if the serial number provided is valid.
    """
    try:
        itksn.parse(value.encode("utf-8"))
    except ConstructError as exc:
        msg = f"Invalid serial number format: {value}"
        raise typer.BadParameter(msg) from exc
    return value


def sns_callback(value: list[str]):
    """
    Callback to check if the serial numbers provided are valid.
    """
    try:
        for v in value:
            itksn.parse(v.encode("utf-8"))
    except ConstructError as exc:
        msg = f"Invalid serial number format: {v}"
        raise typer.BadParameter(msg) from exc
    return value


class LogLevel(str, Enum):
    """
    Enum for log levels.
    """

    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"


class Protocol(str, Enum):
    """
    Enum for upload protocols.
    """

    HTTP = "http"
    HTTPS = "https"


OPTIONS = {}


def parse_object_id(value: str):
    """
    parse a string as a mongodb object id
    """
    if not ObjectId.is_valid(value):
        msg = f"{value} is not a valid ObjectId"
        raise BadParameter(msg)
    return ObjectId(value)


def verbosity_callback(ctx: typer.Context, value: LogLevel):
    """
    Callback to set log level at the package-level.
    """
    if ctx.resilient_parsing:
        return None

    logging.getLogger("module_qc_database_tools").setLevel(value.value)
    return value


def mongo_id_callback(ctx: typer.Context, value: str):
    """
    Callback to assert that the value is a valid MongoID.
    """
    if ctx.resilient_parsing:
        return

    if not ObjectId.is_valid(value):
        msg = f"{value} is not a valid ObjectId"
        raise BadParameter(msg)


OPTIONS["verbosity"]: LogLevel = typer.Option(
    LogLevel.info,
    "-v",
    "--verbosity",
    help="Log level [options: DEBUG, INFO (default) WARNING, ERROR]",
    callback=verbosity_callback,
)
OPTIONS["measurement_path"]: Path = typer.Option(
    "Measurement/",
    "-p",
    "--path",
    help="Path to directory with output measurement files",
    exists=True,
    file_okay=True,
    readable=True,
    writable=True,
    resolve_path=True,
)
OPTIONS["protocol"]: Protocol = typer.Option(
    Protocol.HTTP, "--protocol", help="Protocol to connect to localDB (http or https)"
)
OPTIONS["verify_ssl"]: bool = typer.Option(
    True,
    "--verify/--skip-verify",
    help="if https protocol, verify or not the SSL certificate",
)
OPTIONS["host"]: str = typer.Option("localhost", "--host", help="localDB server")
OPTIONS["port"]: int = typer.Option(
    5000,
    "--port",
    help="localDB port",
)
OPTIONS["dry_run"]: bool = typer.Option(
    False,
    "-n",
    "--dry-run",
    help="Dry-run, do not submit to localDB or update controller config.",
)
OPTIONS["output_path"]: Path = typer.Option(
    "tmp.json",
    "--out",
    "--output-path",
    help="Analysis output result json file path to save in the local host",
    exists=False,
    writable=True,
)
OPTIONS["output_file"]: Optional[Path] = typer.Option(  # noqa: UP045
    None,
    "-o",
    "--output-file",
    help="Path to file. If not specified, will print to stdout.",
    exists=False,
    writable=True,
    dir_okay=False,
)

OPTIONS["config_hw"]: Path = typer.Option(
    None,
    "-c",
    "--config",
    help="Hardware Config file path",
    exists=True,
    file_okay=True,
    readable=True,
    resolve_path=True,
    is_eager=True,  # must be eagerly evaluated first so we can check it in config_callback()
)

OPTIONS["controller_config"]: Optional[Path] = typer.Option(  # noqa: UP045
    None,
    "-r",
    "--controller-config",
    help="Controller config file path",
    exists=True,
    file_okay=True,
    readable=True,
    resolve_path=True,
    is_eager=True,  # must be eagerly evaluated first so we can check it in config_callback()
)

OPTIONS["base_dir"]: Optional[Path] = typer.Option(  # noqa: UP045
    Path.home(),
    "-b",
    "--base-dir",
    help="Base directory.",
    exists=True,
    file_okay=True,
    readable=True,
    resolve_path=True,
    is_eager=True,  # must be eagerly evaluated first so we can check it in config_callback()
)

OPTIONS["module_connectivity"]: Optional[Path] = typer.Option(  # noqa: UP045
    None,
    "-m",
    "--module-connectivity",
    help="path to the module connectivity. Used also to identify the module SN, and to set the default output directory",
    exists=True,
    file_okay=True,
    readable=True,
    writable=True,
    resolve_path=True,
)


OPTIONS["serial_number"]: str = typer.Option(
    ...,
    "--sn",
    "--serial-number",
    help="Module serial number",
    callback=sn_callback,
)
OPTIONS["serial_numbers"]: list[str] = typer.Option(
    ...,
    "--sns",
    "--serial-numbers",
    help="Module serial numbers. Example for list of SNs: --sns SN1 --sns SN2 --sns SN3....",
    callback=sns_callback,
)
OPTIONS["stage"]: str = typer.Option(..., "-stage", "--stage", help="Stage to use")
OPTIONS["mongo_uri"]: str = typer.Option(
    "mongodb://localhost:27017/localdb",
    "-u",
    "--uri",
    help="mongo URI (see documentation for mongo client)",
)
OPTIONS["localdb_name"]: str = typer.Option(
    "localdb",
    "-d",
    "--dbname",
    help="database name used for localDB. This is in your localDB config either as --db (command-line) or as mongoDB.db (yaml).",
)
OPTIONS["userdb_name"]: str = typer.Option(
    "localdbtools",
    "-u",
    "--userdbname",
    help="database name used for localDB tools. This is in your localDB config either as --userdb (command-line) or as userDB.db (yaml).",
)
OPTIONS["userdb_pass"]: str = typer.Option(
    None,
    "--userdbpass",
    help="database password used for localDB tools of your account.",
)
OPTIONS["user_name"]: str = typer.Option(
    None,
    "--username",
    help="Viewer user name with rights to write into localDB/mongoDB. `viewerUser` in LDB config. Might be required.",
)
OPTIONS["user_pass"]: str = typer.Option(
    None,
    "--userpass",
    help="Viewer user password with rights to write into localDB/mongoDB. Might be required.",
)
OPTIONS["itkdb_access_code1"]: Optional[str] = typer.Option(  # noqa: UP045
    None, "--accessCode1", help="Access Code 1 for production DB"
)
OPTIONS["itkdb_access_code2"]: Optional[str] = typer.Option(  # noqa: UP045
    None, "--accessCode2", help="Access Code 2 for production DB"
)
OPTIONS["localdb"]: bool = typer.Option(
    False,
    "--localdb/--proddb",
    help="Whether to use localDB (default) or from Production DB.",
)
OPTIONS["mongo_serverSelectionTimeout"]: int = typer.Option(
    5,
    "--serverSelectionTimeout",
    help="server selection timeout in seconds",
)
OPTIONS["test_run_id"]: ObjectId = typer.Option(
    ...,
    "--test-run",
    help="Test Run ID",
    parser=parse_object_id,
)
OPTIONS["is_complex_analysis"]: bool = typer.Option(
    False,
    "--simple/--complex",
    help="Whether the analysis is simple (default) or complex.",
)

OPTIONS["tags"]: list[str] = typer.Option(
    [],
    "-t",
    "--tag",
    help="tag(s) to add to result, example for add list of tags: --tag 'tag1' --tag 'tag2' --tag 'tag3'... ",
)
OPTIONS["show_skipped_checks"]: bool = typer.Option(
    False,
    "--show-skipped-checks/--hide-skipped-checks",
    help="Whether to hide skipped checks or not",
)
OPTIONS["show_good_checks"]: bool = typer.Option(
    False,
    "--show-good-checks/--hide-good-checks",
    help="Whether to show good checks or not",
)
OPTIONS["filter_checks"]: str = typer.Option(
    "",
    "-k",
    "--filter-checks",
    help="Pattern to filter checks by",
)
OPTIONS_serial_number = Annotated[
    str,
    typer.Option(
        "--sn",
        "--serial-number",
        help="Module serial number",
        callback=sn_callback,
    ),
]
OPTIONS_output_dir = Annotated[
    Path, typer.Option("--output-dir", help="Directory to save the files")
]

OPTIONS_test_type = Annotated[
    Optional[str], typer.Option("--test-type", help="Filter by test type code")
]
OPTIONS_stage = Annotated[
    Optional[str], typer.Option("--stage", help="Filter by stage")
]
OPTIONS_dry_run = Annotated[
    bool,
    typer.Option("-n", "--dry-run", help="Dry run, do not create or modify anything."),
]
OPTIONS_overwrite = Annotated[
    bool, typer.Option("--overwrite", help="Overwrite existing files")
]
OPTIONS["fast-run"]: bool = typer.Option(
    False,
    "--fast",
    help="Fast Pull, No Attachments",
)
OPTIONS["full-run"]: bool = typer.Option(
    False,
    "--full",
    help="Reset Pull, Resync All: Slow",
)
