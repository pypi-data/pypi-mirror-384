from __future__ import annotations

from collections import defaultdict

import itkdb

from module_qc_database_tools.db.prod import get_component
from module_qc_database_tools.models import ITkDBComponent
from module_qc_database_tools.review.checks import checker
from module_qc_database_tools.review.helpers import Check
from module_qc_database_tools.typing_compat import CheckResult, Dict, Tuple


def fetch_component_info(client: itkdb.Client, serial_number: str):
    """
    Fetch the component, children, and test information for all stages.

    Args:
        client (itkdb.Client): The database instance (if fetching from localDB) or client instance (if fetching from prodDB) to retrieve information from.
        serial_number (str): serial number of the component to fetch reference IVs for.

    Returns:
        component (module_qc_database_tools.models.ITkDBComponent): component model with children and test runs filled in
    """

    component_data, _ = get_component(client, serial_number)

    # build full model
    component = ITkDBComponent(client, component_data)
    component.walk()

    return component


def review_component(
    client: itkdb.Client, serial_number: str, *, filter_checks: str = ""
) -> Tuple[Check, Dict[str, CheckResult]]:
    """
    Execute a review of a component and provide the results of the review.

    Args:
        client: itkdb client
        serial_number: the serial number of the component to perform a series of checks on
        filter_checks: run only checks containing this substring

    Returns:
    """
    top_component = fetch_component_info(client, serial_number)
    all_results = defaultdict(list)

    kwargs = {
        "top_component": top_component,
        "component": top_component,
        "filter_checks": filter_checks,
    }
    # first run the checks for when component=top_component to register them
    initial_results = checker.run_checks(**kwargs)
    for check, result in initial_results.items():
        all_results[check].append(result)

    for test_run in top_component.test_runs:
        top_component_results = checker.run_checks(**kwargs, test_run=test_run)
        for check, result in top_component_results.items():
            all_results[check].append(result)

    for component in top_component.children_flattened:
        if component.component_type == "MODULE_CARRIER":
            continue
        kwargs["component"] = component
        component_results = checker.run_checks(**kwargs)
        for check, result in component_results.items():
            all_results[check].append(result)
        for test_run in component.test_runs:
            kwargs["test_run"] = test_run
            results = checker.run_checks(**kwargs)
            for check, result in results.items():
                all_results[check].append(result)

    return checker, all_results


__all__ = ("review_component",)
