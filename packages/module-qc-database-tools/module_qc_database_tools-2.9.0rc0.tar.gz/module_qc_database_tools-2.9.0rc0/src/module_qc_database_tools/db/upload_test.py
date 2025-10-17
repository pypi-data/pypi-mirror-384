from __future__ import annotations

import json
import logging
import os
import sys
from getpass import getpass
from typing import Optional

import requests
import typer
from pymongo import MongoClient

from module_qc_database_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS, Protocol
from module_qc_database_tools.db.show_test import select_test

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    sn: str = typer.Argument("", help="top node serial number"),
    test_run: str = typer.Argument(
        None,
        help="test run ObjectId string. If not specified, select test run in the interactive mode",
    ),
    mongo_uri: str = OPTIONS["mongo_uri"],
    protocol: Protocol = OPTIONS["protocol"],
    host: str = OPTIONS["host"],
    port: str = OPTIONS["port"],
    itkdb_access_code1: Optional[str] = OPTIONS["itkdb_access_code1"],  # noqa: UP045
    itkdb_access_code2: Optional[str] = OPTIONS["itkdb_access_code2"],  # noqa: UP045
):
    """
    List tests missing PDB uploading, and submit the selected test to ITkPD.
    """
    if os.environ.get("MONGO_URI"):
        mongo_uri = os.environ.get("MONGO_URI")
    if os.environ.get("ITKDB_ACCESS_CODE1"):
        itkdb_access_code1 = os.environ.get("ITKDB_ACCESS_CODE1")
    if os.environ.get("ITKDB_ACCESS_CODE2"):
        itkdb_access_code2 = os.environ.get("ITKDB_ACCESS_CODE2")

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    client = MongoClient(mongo_uri)

    try:
        test_run = str(
            select_test(sn, test_run, "missing-upload", client, mongo_uri).get("_id")
        )
    except RuntimeError as e:
        logging.error(str(e))
        sys.exit(1)

    try:
        if not (itkdb_access_code1 and itkdb_access_code2):
            itkdb_access_code1 = getpass("itkdb access code1: ")
            itkdb_access_code2 = getpass("itkdb access code2: ")

        for i in range(3):
            res = requests.post(
                f"{protocol}://{host}:{port}/localdb/submit_test/{test_run}",
                data={"code1": itkdb_access_code1, "code2": itkdb_access_code2},
                timeout=(3.0, 120.0),
            )

            res_doc = json.loads(res.text)

            if res_doc.get("INFO"):
                logging.info(res_doc.get("INFO"))

            if res_doc.get("WARNING"):
                logging.warning(res_doc.get("WARNING"))

            if res_doc.get("ERROR"):
                logging.error(res_doc.get("ERROR"))

            if res_doc.get("ERROR", "") == "Failure in itkdb authentication" and i < 2:
                itkdb_access_code1 = getpass("access code1: ")
                itkdb_access_code2 = getpass("access code2: ")
                continue
            break

    except Exception as e:
        del itkdb_access_code1
        del itkdb_access_code2
        raise e


if __name__ == "__main__":
    typer.run(main)
