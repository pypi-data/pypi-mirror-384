from __future__ import annotations

import logging
import os
import pprint
import sys
from collections import OrderedDict

import bson
import typer
from pymongo import MongoClient

from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS
from module_qc_database_tools.db.local import (
    format_date,
    get_raw_data,
)
from module_qc_database_tools.db.show_qc_status import (
    main as show_qc_status,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


def print_nest(doc, key=None, indent=0):
    """
    Make a print format of a nested object, to be used recursively
    - key: parent keyname
    - doc: contents to be expanded
    - indent: the size of indentation to be inherited
    """
    if type(doc) in [dict, OrderedDict]:
        try:
            max_arg1 = max(len(k) for k, v in doc.items())
        except ValueError:
            return str(None)
        out = []

        for index, k in enumerate(doc):
            v = doc.get(k)
            fmt_arg1 = f":<{(max_arg1)}s"
            if index == 0:
                out += [
                    f"{{0{fmt_arg1}}}:    ".format(k)
                    + print_nest(key=k, doc=v, indent=indent + max_arg1 + 5)
                ]
            else:
                space = "".join([" " for i in range(indent)])
                out += [
                    space
                    + f"{{0{fmt_arg1}}}:    ".format(k)
                    + print_nest(key=k, doc=v, indent=indent + max_arg1 + 5)
                ]

        return "\n".join(out)

    if isinstance(doc, list):
        out = "[ "
        outlist = []
        for index, elem in enumerate(doc):
            if index in range(3, len(doc) - 1):
                pass
            elif index == len(doc) - 1:
                if index >= 3:
                    outlist.append("...")
                if isinstance(elem, dict):
                    ofs = "".join(" " for i in range(indent + 2))
                    outstr = pprint.pformat(elem).replace("\n", "\n" + ofs)
                    outlist.append(outstr)
                else:
                    outlist.append(str(elem))
            elif isinstance(elem, dict):
                outlist.append(pprint.pformat(elem))
            else:
                outlist.append(str(elem))

        out += ", ".join(outlist) + " ] (" + str(len(doc)) + " elements)"

        return out

    if key.lower().find("date") >= 0:
        return format_date(doc)

    return str(doc)


def print_test_run(sn, tr_doc):
    """
    Nicely print a test run
    - sn: serial number
    - tr_doc: LocalDB test run document
    """

    out = OrderedDict()
    out["serialNumber"] = sn
    out["stage"] = tr_doc.pop("stage")
    out["testType"] = tr_doc.pop("testType")
    out["passed"] = tr_doc.pop("passed")
    out["date"] = format_date(tr_doc.get("sys", {}).get("cts", "1970-01-01T00:00:00"))
    out["parameters"] = tr_doc.pop("results")
    try:
        out["properties"] = out.get("parameters").pop("properties")
    except KeyError:
        out["properties"] = out.get("parameters").pop("property")
    out["attachments"] = tr_doc.get("gridfs_attachments")
    out["mqt_data"] = tr_doc.get("mqt_data")

    logging.info(print_nest(doc=out))


def select_test(sn, test_run, mode, client, mongo_uri):
    """
    returns a localdb test run document by an interactive selector if test_run is None
    if test_run (ObjectId string) is provided, just returns the document.
    """
    assert mode in ["filled", "missing-upload"]

    if not test_run:
        if mode == "filled":
            df_out = show_qc_status(sn, mongo_uri, filled=True)
        else:
            df_out = show_qc_status(sn, mongo_uri, missing_upload=True)

        logging.info("------------------------------------------")

        while True:
            select = input(
                f">>> select the test run number to show (0...{len(df_out) - 1}): "
            )

            try:
                selected = int(select)
                if selected >= len(df_out) or selected < 0:
                    logging.error("Invalid select options!")
                    continue
                test_run = df_out.iloc[selected]["test.id"]
                break
            except ValueError:
                logging.error("Invalid select options!")

    tr_doc = client.localdb.QC.result.find_one(
        {"_id": bson.objectid.ObjectId(test_run)}
    )

    if tr_doc is None:
        msg = f"ERROR : test run with id {test_run} not found on LocalDB!"
        raise RuntimeError(msg)

    return tr_doc


@app.command()
def main(
    sn: str = typer.Argument("", help="top node serial number"),
    test_run: str = typer.Argument(
        None,
        help="test run ObjectId string. If not specified, select test run in the interactive mode",
    ),
    mongo_uri: str = OPTIONS["mongo_uri"],
):
    """
    Show the contents of a test run in LocalDB. Only specifying the serial number will provide candidate test runs interactively.
    """
    if os.environ.get("MONGO_URI"):
        mongo_uri = os.environ.get("MONGO_URI")

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    client = MongoClient(mongo_uri)

    try:
        tr_doc = select_test(sn, test_run, "filled", client, mongo_uri)
    except RuntimeError as e:
        logging.error(str(e))
        sys.exit(1)

    tr_doc["mqt_data"] = get_raw_data(client.localdb, tr_doc.get("raw_id"))

    print_test_run(sn, tr_doc)

    return tr_doc


if __name__ == "__main__":
    typer.run(main)
