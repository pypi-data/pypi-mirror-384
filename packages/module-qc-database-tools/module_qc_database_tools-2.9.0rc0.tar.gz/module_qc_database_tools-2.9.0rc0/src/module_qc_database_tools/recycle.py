from __future__ import annotations

import logging
from urllib.parse import urljoin

import pymongo
import requests
from bson.objectid import ObjectId

from module_qc_database_tools.db.local import (
    get_component,
    get_qc_status,
)
from module_qc_database_tools.typing_compat import Dict

log = logging.getLogger(__name__)


def recycle_component(
    db: pymongo.database.Database,
    serial_number: str,
    *,
    localdb_uri: str,
    stage: str | None,
) -> (bool, Dict[str, (bool, str)]):
    """
    Recycle all E-SUMMARY across all stages for given component

    Args:
        db (:obj:`pymongo.database.Database`): The database instance for localDB to retrieve information from.
        serial_number (:obj:`str`): the serial number of the component.
        localdb_uri (:obj:`str`): the localDB URI to use for triggering analysis recycling
        stage (:obj:`str` or :obj:`None`): the stage to recycle if specified, otherwise use all stages (None)

    Returns:
        success (bool): success or failure for recycling all the E-SUMMARIES
        results (dict): dictionary of status for recycling each stage's E-SUMMARY (see :func:`recycle_e_summary`)
    """
    component, _ = get_component(db, serial_number)
    mod_status = get_qc_status(db, component)

    results = {}
    for this_stage, qc_results in mod_status["QC_results"].items():
        if stage and this_stage != stage:
            continue
        e_summary_id = qc_results.get("E_SUMMARY", "-1")
        if e_summary_id == "-1":
            if stage is None:
                log.warning("Stage %s does not have E-SUMMARY, skipping", this_stage)
                continue
            msg = f"Stage {this_stage} does not have E-SUMMARY"
            raise ValueError(msg)

        results[this_stage] = recycle_e_summary(e_summary_id, localdb_uri=localdb_uri)

    return (all(status for status, _ in results.values()), results)


def recycle_e_summary(test_run_id: str | ObjectId, *, localdb_uri: str) -> (bool, str):
    """
    Recycle a given e-summary.

    Args:
        test_run_id (:obj:`str` or :obj:`bson.objectid.ObjectId`): the identifier of the E-Summary to recycle
        localdb_uri (:obj:`str`): the localDB URI to use for triggering analysis recycling

    Returns:
        success (bool): success or failure for recycling all the tests
        content (str): message from localdb
    """

    result = requests.post(
        urljoin(
            localdb_uri,
            "recycle_summary",
        ),
        json={"test_run_id": str(test_run_id)},
        timeout=600,
        headers={"Accept": "application/json"},
    )
    status = result.status_code == 200
    try:
        content = result.json()["message"]
    except KeyError:
        content = result.json()
    except ValueError:
        content = result.content

    return (status, content)


def recycle_analysis(
    test_run_id: str | ObjectId, *, localdb_uri: str, is_complex_analysis: bool = False
) -> (bool, str):
    """
    Recycle a given analysis using it's specific identifier.

    Args:
        test_run_id (:obj:`str` or :obj:`bson.objectid.ObjectId`): the identifier of the test run to recycle
        localdb_uri (:obj:`str`): the localDB URI to use for triggering analysis recycling
        is_complex_analysis (:obj:`bool`): whether the analysis to recycle is complex or not

    Returns:
        status (:obj:`bool`): whether the analysis was recycled successfully
        message (:obj:`str`): message providing context for status

    """
    result = requests.post(
        urljoin(
            localdb_uri,
            "recycle_complex_analysis" if is_complex_analysis else "recycle_analysis",
        ),
        json={"test_run_id": str(test_run_id)},
        timeout=120,
        headers={"Accept": "application/json"},
    )
    status = result.status_code == 200
    try:
        content = result.json()["message"]
    except KeyError:
        content = result.json()
    except ValueError:
        content = result.content

    return (status, content)
