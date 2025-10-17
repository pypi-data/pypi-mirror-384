from __future__ import annotations

import contextlib
import logging
from operator import itemgetter

import itkdb

log = logging.getLogger(__name__)


def get_reference_iv_testRuns(
    client, reference_components, *, reference_stage, reference_testType
):
    """
    Get reference test runs for the referenced components in the reference stage.

    This will grab the latest testRun based on the most recently created date in prodDB.

    !!! warning "do not use `date`"

        Measurements have a datetime when measurement was performed.
        Analyses have a datetime when analysis was performed.

        If an (re)analysis is done and uploaded to prodDB:

        - localDB uses the "analysis record entry" as the `date`
        - webApp uses the "measurement date" as the `date`

        If one is trying to identify the latest test result, one
        cannot rely on the `date` if it was done with webApp (but one
        can rely on the `date` if done with localDB).

    Args:
        client (:obj:`itkdb.Client`): itkdb client to query for test run information
        reference_components (:obj:`list` of :obj:`dict`): list of localDB components to use to pull reference test runs from
        reference_stage (:obj:`str`): the stage for where the tests should be located
        reference_testType (:obj:`str`): the type of tests to use as reference

    Returns:
        reference_iv_testRuns (:obj:`list` of `:obj:`dict`): list of reference test runs corresponding to one test run for each reference component provided
    """

    reference_iv_testRuns = []

    for ref_component in reference_components:
        # for each component, build a list of tests with state=ready, sorting by the 'date' of the test itself
        try:
            ref_testRuns = sorted(
                client.get(
                    "listTestRunsByComponent",
                    json={
                        "filterMap": {
                            "serialNumber": ref_component["serialNumber"],
                            "stage": [reference_stage],
                            "testType": [reference_testType],
                            "state": ["ready"],
                        }
                    },
                ),
                # warning: do not use 'date'
                # - measurements have a datetime when measurement was performed
                # - analyses have a datetime when analysis was performed
                #
                # if an (re)analysis is done and uploaded to prodDB
                # - localDB uses the "analysis record entry" as the 'date'
                # - webApp uses the "measurement date" as the 'date'
                #
                # If one is trying to identify the latest test result, one
                # cannot rely on the 'date' if it was done with webApp (but one
                # can rely on the 'date' if done with localDB).
                key=itemgetter("cts"),
            )
        except itkdb.exceptions.BadRequest as exc:
            msg = "An unknown error occurred. Please see the log."
            raise ValueError(msg) from exc

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
        testRun_id = ref_testRuns[-1]["id"]

        try:
            ref_testRun = client.get("getTestRun", json={"testRun": testRun_id})
        except itkdb.exceptions.BadRequest as exc:
            msg = "An unknown error occurred. Please see the log."
            with contextlib.suppress(Exception):
                message = exc.response.json()
                if "ucl-itkpd-main/getTestRun/testRunDaoGetFailed" in message.get(
                    "uuAppErrorMap", {}
                ):
                    msg = f"test run with id={testRun_id} for {ref_component['serialNumber']} not in ITk Production DB."

            raise ValueError(msg) from exc

        reference_iv_testRuns.append(ref_testRun)

    return reference_iv_testRuns
