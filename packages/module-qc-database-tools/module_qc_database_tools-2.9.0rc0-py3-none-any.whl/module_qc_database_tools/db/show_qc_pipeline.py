from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import typer
from pymongo import MongoClient

from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS
from module_qc_database_tools.db.local import (
    get_disabled_tests,
    get_stage_flow,
)
from module_qc_database_tools.db.ls import (
    main as ls,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    pipeline: str = typer.Argument(
        "pre-production",
        help="pipeline filter [production, pre-production, others]",
    ),
    stage_show: str = typer.Option(None, "-s", "--stage", help="Select specific stage"),
    custom_filter: str = typer.Option(
        ".*", "-c", "--custom-filter", help="Custom serial number regex match"
    ),
    list_components: bool = typer.Option(
        False, "-l", "--list-components", help="enumerate components in each stage"
    ),
    output: str = typer.Option(
        False, "-o", "--output-path", help="output result as json"
    ),
    mongo_uri: str = OPTIONS["mongo_uri"],
):
    """
    Summarize the QC pipeline status. Can specify "pre-production (v1.1)" or "production (v2)",
    and on top of that user can select modules by regex match to serial numbers using the -c option.
    """
    if os.environ.get("MONGO_URI"):
        mongo_uri = os.environ.get("MONGO_URI")

    client = MongoClient(mongo_uri)

    ctype_code = "MODULE"

    stage_flow = get_stage_flow(client.localdbtools, code=ctype_code)
    disabled_stages = get_disabled_tests(client.localdbtools, code=ctype_code)

    df_out = pd.DataFrame(ls(ctype_code, sn_only=True, mongo_uri=mongo_uri, quiet=True))

    logging.basicConfig(
        stream=sys.stdout, level=logging.INFO, format="%(message)s", force=True
    )

    pipeline_map = {"production": "3", "pre-production": "2"}

    summary = []

    for stage in stage_flow:
        if disabled_stages.get(stage, {}).get("disabled", False):
            continue

        if stage_show and stage != stage_show:
            continue

        df_filtered = df_out[
            df_out.serialNumber.str.contains(
                f"20UP[I,G][M,R][A-Z0-9]{pipeline_map.get(pipeline)}.*", regex=True
            )
            & df_out.serialNumber.str.contains(custom_filter, regex=True)
            & df_out.stage.str.match(stage)
        ]

        if len(df_filtered) == 0:
            continue

        stage_info = {"stage": stage, "components.size": len(df_filtered)}
        summary.append(stage_info)

    df_summary = pd.DataFrame(summary)

    if stage_show or list_components:
        for stage in stage_flow:
            if disabled_stages.get(stage, {}).get("disabled", False):
                continue

            if stage_show and stage != stage_show:
                continue

            df_filtered = df_out[
                df_out.serialNumber.str.contains(
                    f"20UP[I,G][M,R][A-Z0-9]{pipeline_map.get(pipeline)}.*", regex=True
                )
                & df_out.serialNumber.str.contains(custom_filter, regex=True)
                & df_out.stage.str.match(stage)
            ]
            if stage_show:
                if len(df_filtered):
                    logging.info(
                        df_summary[df_summary.stage.str.match(stage_show)].to_string(
                            index=False
                        )
                    )
                    logging.info(df_filtered.serialNumber.to_string(index=False))
            elif list_components and len(df_filtered) > 0:
                logging.info(
                    df_summary[df_summary.stage.str.fullmatch(stage)].to_string(
                        index=False
                    )
                )
                logging.info(df_filtered.serialNumber.to_string(index=False))
                logging.info("---------------------------------------------")
    else:
        logging.info(df_summary.to_string(index=False))

    if output:
        out_data = {"summary": [], "components": {}}

        for stage in stage_flow:
            df_filtered = df_out[
                df_out.serialNumber.str.contains(
                    f"20UP[I,G][M,R][A-Z0-9]{pipeline_map.get(pipeline)}.*", regex=True
                )
                & df_out.serialNumber.str.contains(custom_filter, regex=True)
                & df_out.stage.str.match(stage)
            ]

            stage_info = {"stage": stage, "components.size": len(df_filtered)}
            out_data["summary"].append(stage_info)

            out_data["components"][stage] = list(df_filtered.serialNumber)

        with Path(output).open("w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=4)


if __name__ == "__main__":
    typer.run(main)
