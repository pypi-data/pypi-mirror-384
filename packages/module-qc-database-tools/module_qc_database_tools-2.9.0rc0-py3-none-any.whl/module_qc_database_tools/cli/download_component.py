from __future__ import annotations

import json
import logging
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

import itkdb
import typer
from rich import box
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
)
from rich.table import Table

from module_qc_database_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    OPTIONS_dry_run,
    OPTIONS_output_dir,
    OPTIONS_overwrite,
    OPTIONS_serial_number,
    OPTIONS_stage,
    OPTIONS_test_type,
)
from module_qc_database_tools.cli.utils import get_dbs_or_client
from module_qc_database_tools.db.prod import get_component, get_test_run
from module_qc_database_tools.utils import console

app = typer.Typer(context_settings=CONTEXT_SETTINGS)
log = logging.getLogger(__name__)


def extract_attachment_pack(
    zipf: zipfile.ZipFile,
    output_dir: Path,
    overwrite: bool = False,
    dry_run: bool = False,
) -> int:
    """
    Extract the Attachment_Pack.zip and rename the files based on the attachments_info.json.

    Returns the total size of the files extracted to disk.
    """
    attachments_info = json.loads(
        zipfile.Path(zipf, at="attachments_info.json").read_text(encoding="utf-8")
    )

    size = 0
    for attachment_info in attachments_info:
        zip_info = zipf.getinfo(attachment_info["data_id"])
        zip_info.filename = attachment_info["title"]

        output_path = output_dir / attachment_info["title"]
        if not dry_run and not overwrite and output_path.exists():
            continue  # skipping
        output_path = Path(zipf.extract(zip_info, path=output_dir))
        size += output_path.stat().st_size

    return size


def extract_raw(bf: itkdb.models.file.BinaryFile, output_path: Path) -> int:
    """
    Extract the raw measurement from the RAW.

    Returns the size of the extracted file.
    """
    raw = json.loads(bf.content)

    output_path.write_text(json.dumps([raw["raw"]], indent=4))

    return output_path.stat().st_size


def extract_analysis_result(
    test_run: dict[str, Any], serial_number: str, output_path: Path
) -> int:
    """
    Creates an analysis result using the test run.

    Returns the size of the written analysis.json file.
    """
    analysis_result = {
        "serialNumber": serial_number,
        "testType": test_run["testType"]["code"],
        "runNumber": test_run["runNumber"],
        "passed": test_run["passed"],
        "results": {
            "property": {
                prop["code"]: prop["value"] for prop in test_run["properties"]
            },
            **{result["code"]: result["value"] for result in test_run["results"]},
        },
    }

    output_path.write_text(json.dumps([analysis_result], indent=4))
    return output_path.stat().st_size


def download_attachments(
    test_run_id, client, output_dir, progress, summary, dry_run, overwrite
):
    """
    Download the attachments for the given test run.
    """
    test_run, target_serial_number, stage_code = get_test_run(
        client, test_run_id, eos=True
    )
    test_type_code = test_run["testType"]["code"]
    attachments = test_run.get("attachments", [])

    job_task = progress.add_task(
        f"[yellow]{target_serial_number}[/] for [cyan]{test_type_code}[/] @ [white]{stage_code}[/]"
    )

    for attachment in progress.track(attachments, task_id=job_task):
        title = attachment.get("title") or attachment.get("filename")
        target_path = (
            output_dir
            / test_type_code
            / stage_code.replace("/", "-")
            / target_serial_number
            / title
        )

        if not dry_run and not overwrite and target_path.exists():
            summary.add_row(
                test_type_code,
                stage_code,
                target_serial_number,
                title,
                "-",
                "[blue]Skipped[/]",
            )
            continue

        if dry_run:
            summary.add_row(
                test_type_code,
                stage_code,
                target_serial_number,
                title,
                "-",
                "[yellow]Dry run[/]",
            )
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            if attachment.get("type") == "eos":
                bf = client.get(attachment["url"])  # EOS BinaryFile
            else:
                bf = client.get(
                    "getTestRunAttachment",
                    json={"testRun": test_run_id, "code": attachment["code"]},
                )
        except itkdb.exceptions.ResponseException as e:
            summary.add_row(
                test_type_code, stage_code, title, "-", "-", f"[red]Failed: {e}[/]"
            )
            progress.log(f"[red]Failed to download {title}[/]")
        else:
            if title.endswith("Attachment_Pack.zip"):
                size = extract_attachment_pack(
                    zipf=bf,
                    output_dir=target_path.parent,
                    overwrite=overwrite,
                    dry_run=dry_run,
                )
                status = "[green]Extracted[/]"
            elif title == "RAW":
                size = extract_raw(bf=bf, output_path=target_path)
                status = "[green]Extracted[/]"

                analysis_size = extract_analysis_result(
                    test_run=test_run,
                    serial_number=target_serial_number,
                    output_path=target_path.parent / "analysis.json",
                )
                summary.add_row(
                    test_type_code,
                    stage_code,
                    target_serial_number,
                    "analysis.json",
                    f"{analysis_size / 1024**2:.2f} MB",
                    "[green]Generated[/]",
                )

            else:
                size = bf.save(target_path)
                status = "[green]Downloaded[/]"

            summary.add_row(
                test_type_code,
                stage_code,
                target_serial_number,
                title,
                f"{size / 1024**2:.2f} MB" if size else "-",
                status if size else "[blue]Skipped[/]",
            )

    progress.remove_task(job_task)


@app.command()
def main(
    serial_number: OPTIONS_serial_number = ...,
    output_dir: OPTIONS_output_dir = ...,
    itkdb_access_code1: Optional[str] = OPTIONS["itkdb_access_code1"],  # noqa: UP045
    itkdb_access_code2: Optional[str] = OPTIONS["itkdb_access_code2"],  # noqa: UP045
    test_type: OPTIONS_test_type = None,
    stage: OPTIONS_stage = None,
    dry_run: OPTIONS_dry_run = False,
    overwrite: OPTIONS_overwrite = False,
):
    """
    Main executable for downloading components from production database to disk.

    This will:

    \b
    - download all test run results
    - download all attachments
    - extract (`Attachment_Pack.zip`) attachment packs
    - extract (`RAW`) measurement inputs for `module-qc-analysis-tools`
    - generate (`analysis.json`) analysis output from `module-qc-analysis-tools` from the test run results

    \f
    !!! note "Added in version 2.5.7"

    """
    logging.getLogger("itkdb").setLevel(logging.ERROR)

    # pylint: disable=duplicate-code
    client, _ = get_dbs_or_client(
        itkdb_access_code1=itkdb_access_code1,
        itkdb_access_code2=itkdb_access_code2,
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    component, _ = get_component(client, serial_number)

    filtered_test_runs = []

    for test_group in component["tests"]:
        for test_run in test_group["testRuns"]:
            if stage and test_run["stage"]["code"] != stage:
                continue

            if test_group["code"] == "E_SUMMARY":
                e_summary, *_ = get_test_run(client, test_run["id"], eos=False)
                for result in e_summary["results"]:
                    if (
                        result["dataType"] == "testRun"
                        and result["value"]
                        and not (
                            test_type
                            and result["value"]["testType"]["code"] != test_type
                        )
                    ):
                        filtered_test_runs.append(result["value"]["id"])

            else:
                if test_type and test_group["code"] != test_type:
                    continue
                filtered_test_runs.append(test_run["id"])

    if not filtered_test_runs:
        console.print(
            f"[bold yellow]No test runs found matching filters for {serial_number}[/]"
        )
        raise typer.Exit(0)

    summary = Table(
        title=f"Test Runs for {serial_number}",
        show_footer=True,
        box=box.SIMPLE,
        highlight=True,
    )
    summary.add_column("Test Type", style="atlas.test_name")
    summary.add_column("Stage")
    summary.add_column("Component")
    summary.add_column("Attachment", style="bright_black italic")
    summary.add_column("Size")
    summary.add_column("Status")

    with Progress(
        "[progress.description]{task.description:<80s}",
        BarColumn(),
        MofNCompleteColumn(),
        auto_refresh=True,
    ) as progress:
        main_task = progress.add_task(
            "Downloading attachments for test runs", total=len(filtered_test_runs)
        )

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(
                    download_attachments,
                    test_run_id=test_run_id,
                    client=client,
                    output_dir=output_dir,
                    progress=progress,
                    summary=summary,
                    dry_run=dry_run,
                    overwrite=overwrite,
                )
                for test_run_id in filtered_test_runs
            ]

            for future in as_completed(futures):
                future.result()
                progress.advance(main_task)

        progress.remove_task(main_task)
    console.print(summary)


if __name__ == "__main__":
    typer.run(main)
