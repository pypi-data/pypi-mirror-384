from __future__ import annotations

import logging
import os
import re
import sys
from collections import OrderedDict

import typer
from pymongo import ASCENDING, DESCENDING, MongoClient
from rich.table import Table

from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS
from module_qc_database_tools.utils import console

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    search_str: str = typer.Argument(
        "MODULE",
        help="component type [MODULE, BARE_MODULE, PCB, FE_CHIP, ...] or serial number regex match",
    ),
    list_long: bool = typer.Option(
        False, "-l", help="List components in the long format"
    ),
    sort_by_sn: bool = typer.Option(
        False, "-s", help="List components sorted by serial number"
    ),
    sn_only: bool = typer.Option(False, "-o", help="Show only serial numbers"),
    reverse: bool = typer.Option(False, "-r", help="Reverse the order of the sort."),
    quiet: bool = typer.Option(False, "-q", help="Muting stdout (to be used as API)"),
    mongo_uri: str = OPTIONS["mongo_uri"],
):
    """
    List up components stored in LocalDB.
    """

    if isinstance(quiet, bool) and quiet is True:
        logging.basicConfig(
            stream=sys.stderr, level=logging.WARNING, format="%(message)s", force=True
        )
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")

    search_str = search_str.upper()

    if os.environ.get("MONGO_URI"):
        mongo_uri = os.environ.get("MONGO_URI")

    client = MongoClient(mongo_uri)

    ctype_map = {"fe_chip": "front-end_chip", "pcb": "module_pcb"}

    sort_key = "_id" if sort_by_sn is False else "serialNumber"
    order = ASCENDING if reverse is False else DESCENDING

    sn_general_regex = "20UP[G,I,Q][A-Z][A-Z0-9][0-9]{7}"

    docs = []

    ctype_list = [
        ctype_map.get(ctype.get("code").lower(), ctype.get("code").lower())
        for ctype in client.localdbtools.componentType.find({}, {"code": 1})
    ]

    search_scope = None
    for ctype in ctype_list:
        if re.compile(".*" + search_str.lower() + ".*").match(ctype):
            search_scope = {
                "componentType": ctype_map.get(ctype.lower(), ctype.lower())
            }
            break

    for cpt in client.localdb.component.find(search_scope).sort(sort_key, order):
        if not cpt.get("serialNumber"):
            continue

        if not re.compile(sn_general_regex).match(cpt.get("serialNumber")):
            continue

        if search_scope is None and not re.compile(".*" + search_str + ".*").match(
            cpt.get("serialNumber")
        ):
            continue

        doc = OrderedDict()

        doc["serialNumber"] = cpt.get("serialNumber", None)

        try:
            doc["alt_id"] = next(
                p
                for p in cpt.get("properties", {})
                if p.get("code", None) == "ALTERNATIVE_IDENTIFIER"
            ).get("value")

            if doc["alt_id"] is None:
                doc["alt_id"] = "n/a"
        except StopIteration:
            doc["alt_id"] = "n/a"

        doc["stage"] = client.localdb.QC.module.status.find_one(
            {"component": str(cpt.get("_id"))}
        ).get("stage")

        if list_long:
            doc["id"] = str(cpt.get("_id"))

            for prop in cpt.get("properties"):
                if (
                    prop.get("dataType") == "codeTable"
                    and prop.get("value") is not None
                ):
                    ct = {}
                    for o in prop.get("codeTable"):
                        ct.update({o.get("code"): o.get("value")})
                    doc[prop.get("code")] = str(ct.get(prop.get("value")))
                elif (
                    prop.get("dataType") != "codeTable"
                    and prop.get("value") is not None
                ):
                    doc[prop.get("code")] = str(prop.get("value"))

        docs += [doc]

    if sn_only:
        for doc in docs:
            console.print(doc["serialNumber"])
    else:
        table = Table(title="Components in LocalDB", highlight=True)
        table.add_column("Serial Number", justify="center", no_wrap=True)
        table.add_column("Alt. ID", style="bright_black", no_wrap=True)
        table.add_column("Stage", no_wrap=True)

        for doc in docs:
            table.add_row(doc["serialNumber"], doc["alt_id"], doc["stage"])

        console.print(table)

    return docs


if __name__ == "__main__":
    typer.run(main)
