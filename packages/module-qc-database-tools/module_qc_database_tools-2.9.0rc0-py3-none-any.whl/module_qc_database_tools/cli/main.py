"""
Top-level entrypoint for the command line interface.
"""

from __future__ import annotations

import typer

import module_qc_database_tools
from module_qc_database_tools.cli.assign_tag import main as assign_tag
from module_qc_database_tools.cli.download_component import main as download_component
from module_qc_database_tools.cli.fetch_reference_ivs import main as fetch_reference_ivs
from module_qc_database_tools.cli.generate_yarr_config import (
    main as generate_yarr_config,
)
from module_qc_database_tools.cli.get_bom_info import get_bom_info
from module_qc_database_tools.cli.get_vfd_info import get_vfd_info
from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS
from module_qc_database_tools.cli.pull_component import main as pull_component
from module_qc_database_tools.cli.recycle_analysis import main as recycle_analysis
from module_qc_database_tools.cli.recycle_esummary import main as recycle_esummary
from module_qc_database_tools.cli.register_component import main as register_component
from module_qc_database_tools.cli.review_component import main as review_component
from module_qc_database_tools.cli.run_full_qc import main as run_full_qc
from module_qc_database_tools.cli.sync_component_stages import (
    main as sync_component_stages,
)
from module_qc_database_tools.cli.upload_measurement import main as upload_measurement
from module_qc_database_tools.db.ls import (
    main as ls,
)
from module_qc_database_tools.db.show_qc_pipeline import (
    main as show_qc_pipeline,
)
from module_qc_database_tools.db.show_qc_status import (
    main as show_qc_status,
)
from module_qc_database_tools.db.show_test import (
    main as show_test,
)
from module_qc_database_tools.db.upload_test import (
    main as upload_test,
)

# subcommands
app = typer.Typer(context_settings=CONTEXT_SETTINGS)

app_component = typer.Typer(context_settings=CONTEXT_SETTINGS)
app.add_typer(app_component, name="component", help="Commands to run on components")


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(False, "--version", help="Print the current version."),
    prefix: bool = typer.Option(
        False, "--prefix", help="Print the path prefix for data files."
    ),
) -> None:
    """
    Manage top-level options
    """
    if version:
        typer.echo(f"module-qc-database-tools v{module_qc_database_tools.__version__}")
        raise typer.Exit()
    if prefix:
        typer.echo(module_qc_database_tools.data.resolve())
        raise typer.Exit()


app.command("generate-yarr-config")(generate_yarr_config)
app.command("register-component")(register_component)
app.command("fetch-reference-iv")(fetch_reference_ivs)
app.command("upload-measurement")(upload_measurement)
app.command("sync-component-stages")(sync_component_stages)
app.command("recycle-esummary")(recycle_esummary)
app.command("recycle-analysis")(recycle_analysis)
app.command("get-vfd-info")(get_vfd_info)
app.command("get-bom-info")(get_bom_info)
app.command("ls")(ls)
app.command("show-qc-pipeline")(show_qc_pipeline)
app.command("show-qc-status")(show_qc_status)
app.command("show-test")(show_test)
app.command("upload-test")(upload_test)
app.command("run-full-qc")(run_full_qc)
app_component.command("review")(review_component)
app_component.command("download")(download_component)
app_component.command("pull")(pull_component)
app.command("pull-component")(pull_component)
app.command("review-component")(review_component)
app.command("assign-tag")(assign_tag)

# for generating documentation using mkdocs-click
typer_click_object = typer.main.get_command(app)
