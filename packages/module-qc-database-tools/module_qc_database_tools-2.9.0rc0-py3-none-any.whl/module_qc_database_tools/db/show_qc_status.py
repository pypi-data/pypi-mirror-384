from __future__ import annotations

import copy
import logging
import os
import sys
from collections import OrderedDict

import bson
import pandas as pd
import typer
from pymongo import MongoClient
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS
from module_qc_database_tools.db.local import (
    component_type_to_code,
    format_date,
    get_disabled_tests,
    get_stage_flow,
    validate_sn,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


def get_component(
    client,
    cpt_id,
    single=False,
    insert_status=False,
    use_cache=True,
    top_ctype=None,
    progress_bar=None,
):
    """
    Get a LocalDB component doc with augmentation.
    Specifying either _id or serial_number is mandatory.
    - By default, recursively associate sub-components within the document.
    - If single is False, then do not go through sub-components.
    - If insert_status is True, then augment the document with QC status information
    """
    component = None
    try:
        component = client.localdb.component.find_one(
            {"_id": bson.objectid.ObjectId(cpt_id)},
            {"serialNumber": True, "componentType": True},
        )
    except bson.objectid.InvalidId:
        if not validate_sn(cpt_id):
            msg = f'get_component(): ERROR: Invalid component id or serial number "{cpt_id}"'
            logging.error(msg)
            sys.exit(1)

        component = client.localdb.component.find_one(
            {"serialNumber": cpt_id},
            {"serialNumber": True, "componentType": True},
        )

    if not component:
        msg = f'Component "{cpt_id}" is not found in LocalDB'
        logging.info(msg)
        sys.exit(2)

    ctype_code = component_type_to_code(component.get("componentType"))

    if insert_status:
        for mode in ["localdb", "pdb"]:
            component[f"{mode}_status"], component["stage"] = get_status(
                client,
                component=component,
                mode=mode,
                test_info="header"
                if mode == "localdb"
                else (None if use_cache else "real_check"),
                top_ctype=ctype_code if top_ctype is None else top_ctype,
                progress_bar=progress_bar,
            )

    if single is False:
        children = [
            get_component(
                client,
                cpt_id=cpr.get("child"),
                insert_status=insert_status,
                use_cache=use_cache,
                top_ctype=ctype_code if top_ctype is None else top_ctype,
                progress_bar=progress_bar,
            )
            for cpr in list(
                client.localdb.childParentRelation.find(
                    {"parent": str(component.get("_id"))}
                )
            )
            if not (
                component.get("componentType") == "module"
                and get_component(client, cpt_id=cpr.get("child"), single=True).get(
                    "componentType"
                )
                == "front-end_chip"
            )
        ]

        if len(children) > 0:
            component["children"] = children

    return component


def flatten(obj):
    """
    Tool function: Flatten an object
    """
    keys = [k for k, v in obj.items()]

    for k1 in keys:
        v1 = obj.get(k1)
        if isinstance(v1, dict):
            for k2, v2 in v1.items():
                obj["::".join([k1, k2])] = v2

    for k in keys:
        if isinstance(obj[k], dict):
            obj.pop(k)

    return obj


def get_status(
    client,
    cpt_id=None,
    component=None,
    mode="localdb",
    test_info=None,
    top_ctype=None,
    progress_bar=None,
):
    """
    Get the status document of a component
    """
    assert mode.lower() in ["localdb", "pdb"]

    if mode.lower() == "localdb":
        assert test_info in [None, "header", "full"]
    elif mode.lower() == "pdb":
        assert test_info in [None, "real_check"]

    mode_select = "QC_results_pdb" if mode.lower() == "pdb" else "QC_results"

    if not component and cpt_id is not None:
        component = get_component(client, cpt_id=cpt_id, single=True)

    if not component:
        return None

    status_doc = client.localdb.QC.module.status.find_one(
        {"component": str(component.get("_id"))}, {"stage": True, mode_select: True}
    )

    current_stage = status_doc.get("stage")
    mid_format = flatten(status_doc.get(mode_select))

    status_summary = OrderedDict()

    code = component_type_to_code(component.get("componentType"))

    filter_code = code if top_ctype is None else top_ctype
    stage_flow = [
        s
        for s in get_stage_flow(database=client.localdbtools, code=code)
        if s.startswith(filter_code)
    ]

    disabled_tests = get_disabled_tests(database=client.localdbtools, code=code)

    if progress_bar:
        fetch_task = progress_bar.add_task(
            "Fetching tests...",
            total=len(stage_flow),
            visible=mode.lower() == "localdb",
        )

    for stage_index, stage in enumerate(stage_flow):
        if progress_bar:
            progress_bar.update(
                fetch_task,
                description=f"Fetching test for {component.get('serialNumber')} ({mode})...",
            )

        status_summary[stage] = {
            s[len(stage) + 2 :]: mid_format.get(s)
            for s in mid_format
            if s.find(stage + "::") >= 0
        }
        status_summary[stage].update({"stage_index": stage_index})

        if not (mode.lower() == "localdb" and test_info is not None):
            continue

        for ttype, tr_id in status_summary[stage].items():
            if ttype == "stage_index":
                continue

            status_summary[stage][ttype] = {}
            if disabled_tests.get(stage, {}).get("disabled", 0) == 1:
                # entire stage is disabled
                status_summary[stage][ttype]["enabled"] = False
            elif ttype in disabled_tests.get(stage, {}).get("tests", []):
                # if ttype in the list, then the test is disabled
                status_summary[stage][ttype]["enabled"] = False
            else:
                # if ttype is not in the list, then the test is enabled
                status_summary[stage][ttype]["enabled"] = True

            try:
                tr = client.localdb.QC.result.find_one(
                    {"_id": bson.objectid.ObjectId(tr_id)}
                )

                if test_info == "full":
                    status_summary[stage][ttype] = tr
                elif test_info == "header":
                    analysis_version = (
                        tr.get("results", {})
                        .get("property", {})
                        .get("ANALYSIS_VERSION", None)
                    )

                    if not analysis_version:
                        analysis_version = (
                            tr.get("results", {})
                            .get("properties", {})
                            .get("ANALYSIS_VERSION", None)
                        )

                    dt = format_date(
                        tr.get("sys", {}).get("cts", "1970-01-01T00:00:00")
                    )

                    header = {
                        "id": tr_id,
                        "passed": tr.get("passed"),
                        "analysis_version": analysis_version,
                        "date": dt,
                    }
                    status_summary[stage][ttype].update(header)

            except bson.objectid.InvalidId:
                pass

        if progress_bar:
            progress_bar.advance(fetch_task)

    # progress_bar.remove_task(fetch_task)

    return status_summary, current_stage


def flatten_tests(component, cpt_index=0):
    """
    Flatten the component doc with QC status information to a flattened table
    to be fed to pd.dataframe
    """
    out = []
    obj = {}

    for k, v in component.items():
        if type(v) in [OrderedDict, dict, list, bson.objectid.ObjectId]:
            continue

        obj[k] = v

    for stage, tests in component.get("localdb_status").items():
        tmp1 = copy.deepcopy(obj)
        tmp1["stage"] = stage
        tmp1["stage_index"] = tests["stage_index"]
        tmp1["cpt_index"] = cpt_index
        tests.pop("stage_index")

        for ttype, tr in tests.items():
            tmp2 = copy.deepcopy(tmp1)
            tmp2["testType"] = ttype

            if tr == "-1":
                tmp2["test.id"] = None
                tmp2["pdb.uploaded"] = False
                out.append(tmp2)
                continue

            if tr is None:
                tmp2["test.id"] = None
                tmp2["pdb.uploaded"] = False
                out.append(tmp2)
                continue

            for k, v in tr.items():
                tmp2[f"test.{k}"] = v

            pdb_status = component.get("pdb_status", {})
            if not isinstance(pdb_status, dict):
                logging.info("Error: 'pdb_status' is not a valid dictionary.")
                continue

            for k, v in pdb_status.get(stage, {}).items():
                if k != ttype:
                    continue

                try:
                    bson.objectid.ObjectId(v)
                    tmp2["pdb.uploaded"] = True
                except bson.objectid.InvalidId:
                    tmp2["pdb.uploaded"] = False

            out.append(tmp2)

    df_out = pd.DataFrame(out)

    cpt_index += 1

    if component.get("children"):
        for child in component.get("children"):
            child_df, cpt_index = flatten_tests(child, cpt_index)
            df_out = pd.concat([df_out, child_df], ignore_index=True)

    return df_out, cpt_index


def print_children(children, indent=0):
    """
    Print children recursively
    """
    indent_str = "".join(" " for i in range(indent))
    out = indent_str + "sub-components"
    logging.info(out)
    for child in children:
        indent_str = "".join(" " for i in range(indent + 4))
        out = (
            indent_str
            + " - "
            + child.get("serialNumber")
            + " ("
            + child.get("componentType")
            + ")"
        )
        logging.info(out)
        if child.get("children"):
            print_children(child.get("children"), indent + 7)


def print_component_info(cpt_doc):
    """
    Print basic component info
    """
    for key in ["serialNumber", "componentType", "stage", "_id"]:
        out = f"{key:<20s}: {cpt_doc.get(key)}"
        logging.info(out)

    print_children(cpt_doc.get("children"), indent=0)


@app.command()
def main(
    sn: str = typer.Argument("", help="top node serial number"),
    mongo_uri: str = OPTIONS["mongo_uri"],
    showall: bool = typer.Option(
        False, "-a", "--all", help="Show all tests including disabled stages/tests"
    ),
    missing: bool = typer.Option(
        False, "-i", "--incomplete", help="Show only missing tests"
    ),
    missing_upload: bool = typer.Option(
        False, "-u", "--missing-upload", help="Show only tests missing PDB uploading"
    ),
    filled: bool = typer.Option(False, "-f", "--filled", help="Show only filled tests"),
):
    """
    Show the QC status of a component and its sub-components.
    """

    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")

    if os.environ.get("MONGO_URI"):
        mongo_uri = os.environ.get("MONGO_URI")

    client = MongoClient(mongo_uri)

    if not validate_sn(sn):
        msg = f"Invalid serial number: {sn}"
        logging.error(msg)
        sys.exit(1)

    # Define custom progress bar
    with Progress(
        TextColumn(
            "[progress.description]{task.description}[progress.percentage]{task.percentage:>3.0f}%"
        ),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
    ) as progress_bar:
        cpt_doc = get_component(
            client,
            cpt_id=sn,
            single=False,
            insert_status=True,
            progress_bar=progress_bar,
        )

    print_component_info(cpt_doc)
    logging.info("------------------------------------------")

    tests_df, _cpt_index = flatten_tests(cpt_doc)
    tests_df = tests_df.sort_values(["stage_index", "cpt_index"])
    tests_df = tests_df.drop(["stage_index", "cpt_index"], axis="columns")

    if isinstance(showall, bool) and showall:
        logging.info("[ All Tests (incl. Disabled Tests) ]")
        condition = tests_df.index.isin(tests_df.index)
    elif isinstance(missing, bool) and missing:
        logging.info("[ Missing Tests ]")
        condition = tests_df["test.enabled"] & tests_df["test.id"].isna()
    elif isinstance(missing_upload, bool) and missing_upload:
        logging.info("[ Tests Missing PDB Upload ]")
        condition = (
            tests_df["test.enabled"]
            & ~tests_df["test.id"].isna()
            & ~tests_df["pdb.uploaded"]
        )
    elif isinstance(filled, bool) and filled:
        logging.info("[ Registered Tests ]")
        condition = tests_df["test.enabled"] & ~tests_df["test.id"].isna()
    else:
        logging.info("[ All Enabled Tests ]")
        condition = tests_df["test.enabled"]

    filtered_df = tests_df[condition].reset_index(drop=True)
    logging.info(filtered_df.to_string())

    return filtered_df


if __name__ == "__main__":
    typer.run(main)
