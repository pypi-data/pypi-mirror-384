from __future__ import annotations

import inspect
import logging
from typing import Optional

import typer
from rich import box
from rich.rule import Rule
from rich.table import Table
from rich.tree import Tree

from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS
from module_qc_database_tools.cli.utils import get_dbs_or_client
from module_qc_database_tools.review import review_component
from module_qc_database_tools.utils import console

app = typer.Typer(context_settings=CONTEXT_SETTINGS)
log = logging.getLogger(__name__)


@app.command()
def main(
    serial_number: str = OPTIONS["serial_number"],
    itkdb_access_code1: Optional[str] = OPTIONS["itkdb_access_code1"],  # noqa: UP045
    itkdb_access_code2: Optional[str] = OPTIONS["itkdb_access_code2"],  # noqa: UP045
    show_skipped_checks: bool = OPTIONS["show_skipped_checks"],
    show_good_checks: bool = OPTIONS["show_good_checks"],
    filter_checks: str = OPTIONS["filter_checks"],
):
    """
    Main executable for reviewing component uploaded to Prod DB.

    For more details on the checks run, please see the [checks API][module_qc_database_tools.review.checks].
    \f
    !!! note "Added in version 2.5.1"

    """
    # pylint: disable=duplicate-code
    client, _ = get_dbs_or_client(
        itkdb_access_code1=itkdb_access_code1,
        itkdb_access_code2=itkdb_access_code2,
    )

    checker, all_results = review_component(
        client, serial_number, filter_checks=filter_checks
    )

    overall_status = True

    statistics = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "notran": 0}

    tree = Tree(f"checks for {serial_number}", highlight=True)
    for name, check in checker.checks.items():
        results = all_results[name]
        signature = inspect.signature(check)
        unskipped_results = [
            result for result in results if result["status"] is not None
        ]
        check_status = all(result["status"] for result in unskipped_results)
        tree_check = tree.add(
            f"{':white_check_mark:' if check_status and bool(unskipped_results) else ':cross_mark:' if bool(unskipped_results) else ':bell_with_slash:' if bool(results) else ':heavy_large_circle:'} {name}{signature}",
            expanded=not (check_status)
            or show_good_checks
            or show_skipped_checks
            or not (unskipped_results),
        )
        if not unskipped_results and not results:
            tree_check.add("no checks were ran")
            statistics["notran"] += 1
            overall_status &= False
            continue
        for result in results:
            statistics["total"] += 1
            args = ",".join(str(arg) for arg in result["args"])
            if result["status"]:
                statistics["passed"] += 1
                if show_good_checks:
                    tree_check.add(f":white_check_mark: {args}")
            elif result["status"] is None:
                statistics["skipped"] += 1
                if show_skipped_checks:
                    tree_check.add(
                        f":bell_with_slash: {args}: [bright_black]{result['message']}[/]"
                    )
            elif result["status"] is False:
                statistics["failed"] += 1
                tree_check.add(f":cross_mark: {args}: [red bold]{result['message']}[/]")

        overall_status &= check_status

    tree.label = (
        f"{':white_check_mark:' if overall_status else ':cross_mark:'} {tree.label}"
    )
    tree.expanded = not (overall_status) or show_good_checks or show_skipped_checks
    console.print(tree)

    grade = (
        statistics["passed"]
        / (statistics["notran"] + statistics["passed"] + statistics["failed"])
    ) * 100.0
    table = Table(title=Rule("Summary"), show_footer=True, box=box.SIMPLE)
    table.add_column("Checks", "Grade", style="bold bright_black")
    table.add_column("Count", f"{grade:0.1f}%", style="yellow", justify="right")

    table.add_row("Total", f"[yellow]{statistics['total']}[/]")
    table.add_row("Passed", f"[bright_green]{statistics['passed']}[/]")
    table.add_row("Failed", f"[red]{statistics['failed']}[/]")
    table.add_row("Not Ran", f"[red]{statistics['notran']}[/]")
    table.add_row("Skipped", f"[deep_sky_blue3]{statistics['skipped']}[/]")

    console.print(table)

    if not overall_status:
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(main)
