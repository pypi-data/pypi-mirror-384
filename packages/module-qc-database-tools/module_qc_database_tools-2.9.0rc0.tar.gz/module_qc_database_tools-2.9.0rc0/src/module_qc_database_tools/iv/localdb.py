from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def get_reference_iv_testRuns(
    database, reference_components, *, reference_stage, reference_testType
):
    """
    Get reference test runs for the referenced components in the reference stage.

    This will grab the latest testRun based on the most recently modified date in localDB.

    Args:
        database (:obj:`pymongo.database.Database`): mongoDB database to query for test run information
        reference_components (:obj:`list` of :obj:`dict`): list of localDB components to use to pull reference test runs from
        reference_stage (:obj:`str`): the stage for where the tests should be located
        reference_testType (:obj:`str`): the type of tests to use as reference

    Returns:
        reference_iv_testRuns (:obj:`list` of `:obj:`dict`): list of reference test runs corresponding to one test run for each reference component provided
    """
    reference_iv_testRuns = []

    for ref_component in reference_components:
        ref_testRuns = list(
            database.QC.result.find(
                {
                    "stage": reference_stage,
                    "component": str(ref_component["_id"]),
                    "testType": reference_testType,
                },
                sort=[("sys.mts", 1)],
            )
        )

        if not ref_testRuns:
            reference_iv_testRuns.append(None)
            continue

        # pylint: disable=duplicate-code
        if len(ref_testRuns) != 1:
            log.warning(
                "Multiple test runs of %s were found for %s. Choosing the latest tested.",
                reference_testType,
                ref_component["serialNumber"],
            )

        # get the last one
        ref_testRun = ref_testRuns[-1]
        reference_iv_testRuns.append(ref_testRun)

    return reference_iv_testRuns
