from __future__ import annotations

import contextlib
import logging
from collections.abc import Iterator
from typing import Any

import itkdb
import itksn
from itkdb.models.component import Component as ITkDBComponent
from module_qc_data_tools.utils import get_layer_from_sn

from module_qc_database_tools.typing_compat import ProdDBComponent, ProdDBTestRun

log = logging.getLogger(__name__)


def get_component(client, identifier) -> (ProdDBComponent, str):
    """
    Get component information using identifier (serial number or id).

    Args:
        client (:obj:`itkdb.Client`): itkdb client to query for component information
        identifier (:obj:`str`): identifier of component to get information for (serial number or id)

    Returns:
        component (:obj:`dict`): information about the component from prodDB
        stage (:obj:`str`): current stage of component
    """
    try:
        component = client.get("getComponent", json={"component": identifier})
    except itkdb.exceptions.BadRequest as exc:
        msg = "An unknown error occurred. Please see the log."
        with contextlib.suppress(Exception):
            message = exc.response.json()
            if "ucl-itkpd-main/getComponent/componentDoesNotExist" in message.get(
                "uuAppErrorMap", {}
            ):
                msg = f"component with {identifier} not in ITk Production DB."

        raise ValueError(msg) from exc

    current_stage = get_stage(client, component)
    serial_number = component["serialNumber"]
    if not current_stage:
        msg = f"component with {serial_number} does not have a current stage. Something is wrong with this component in ITk Production Database."
        raise ValueError(msg)

    return (component, current_stage)


def get_serial_number(component: ProdDBComponent) -> str:
    """
    Get the serial number from the component.

    Args:
        component (:obj:`dict`): prodDB component to get serial number from

    Returns:
        serial_number (:obj:`str`): serial number of component
    """
    return component["serialNumber"]


def get_stage(client, component: ProdDBComponent) -> str | None:  # noqa: ARG001  # pylint: disable=unused-argument
    """
    Get the stage from the component.

    Args:
        component (:obj:`dict`): prodDB component to get stage from

    Returns:
        stage (:obj:`str`): stage of component
    """
    return (component.get("currentStage") or {}).get("code")


def get_property(component: ProdDBComponent, code: str) -> Any:
    """
    Get the serial number from the component.

    Args:
        component (:obj:`dict`): prodDB component to get property information for
        code (:obj:`str`): property code to retrieve

    Returns:
        property (:obj:`dict` or None): property dictionary
    """
    for prop in component.get("properties", []):
        if prop.get("code", []) == code:
            return prop
    return None


def get_children(
    client, component: ProdDBComponent, *, component_type=None, ignore_types=None
) -> Iterator[ProdDBComponent]:
    """
    Get children for component by ID matching the component type from Local DB.

    !!! note

        This returns a generator.

    Args:
        client (:obj:`itkdb.Client`): itkdb client to query for parent-child relationship
        component (:obj:`dict`): the top-level component to recursively get the children of
        component_type (:obj:`str` or :obj:`None`): the component type code to filter children by (None for any)
        ignore_types (:obj:`list` or :obj:`None`): component types to ignore

    Returns:
        children (:obj:`iterator`): generator of localDB components matching the component type
    """

    def _recursive(
        component: ITkDBComponent, *, component_type, ignored_types
    ) -> Iterator[ProdDBComponent]:
        current_component_type = (component._data.get("componentType") or {}).get(  # pylint: disable=protected-access
            "code"
        )
        if (
            current_component_type == component_type or component_type is None
        ) and current_component_type not in ignored_types:
            yield component._data  # pylint: disable=protected-access

        for child in component.children:
            yield from _recursive(
                child, component_type=component_type, ignored_types=ignored_types
            )

    # walk through structure
    component_model = ITkDBComponent(client, component)
    component_model.walk()

    yield from _recursive(
        component_model, component_type=component_type, ignored_types=ignore_types or []
    )


def set_component_stage(client, serial_number: str, stage: str, *, userdb=None) -> None:  # noqa: ARG001  # pylint: disable=unused-argument
    """
    Set component (by serial number) to the current stage.

    Args:
        client (:obj:`itkdb.Client`): itkdb client to query for parent-child relationship
        serial_number (:obj:`str`): serial number of component
        stage (:obj:`str`): code of stage to set component to

    Returns:
        None
    """
    component, current_stage = get_component(client, serial_number)
    pdb_component_type = component["componentType"]["code"]

    all_stages = [ct_stage["code"] for ct_stage in component["componentType"]["stages"]]

    if stage not in all_stages:
        msg = (
            f"{stage} is not a valid stage on this component type: {pdb_component_type}"
        )
        raise ValueError(msg)

    try:
        client.post(
            "setComponentStage",
            json={
                "component": serial_number,
                "stage": stage,
                "rework": all_stages.index(current_stage) > all_stages.index(stage),
            },
        )
    except itkdb.exceptions.BadRequest:
        msg = f"Unable to set {serial_number} to {stage}"
        log.exception(msg)
        return False
    return True


# pylint: disable=duplicate-code
def get_bom_info(client, serial_number: str):
    """
    Fetch BoM version from ProdDB

    Args:
        client (:obj:`itkdb.Client`): itkdb client to query for test run information
        serial_number (str): serial number of the component to fetch BoM info for.

    Returns:
        bom_info (:obj:`dict`): dict of the code/value pair of the BoM version

    """
    module, _ = get_component(client, serial_number)
    for child in get_children(client, module, component_type="PCB"):
        bom_info = get_property(child, "PCB_BOM_VERSION")

        if not bom_info:
            msg = f"Could not find BoM information on PCB: {get_serial_number(child)}."
            raise ValueError(msg)

        # the value stored in prodDB is actually the code in CodeTable
        code_stored_in_prodDB = bom_info["value"] if bom_info["value"] else "09"

        code_table = {ct["code"]: ct["value"] for ct in bom_info["codeTable"]}
        value = code_table.get(code_stored_in_prodDB, "Unknown")
        return {"code": code_stored_in_prodDB, "value": value}

    msg = f"There is no PCB on module {serial_number}."
    raise ValueError(msg)


# pylint: disable=duplicate-code
def get_full_depletion_voltage(client, serial_number: str):
    """
    Fetch full depetion voltage from ProdDB.

    Args:
        client (:obj:`itkdb.Client`): itkdb client to query for test run information
        serial_number (str): serial number of the component to fetch BoM info for.

    Returns:
        dict[str, float]: mapping between child serial number and full depletion voltage

    """

    module, _ = get_component(client, serial_number)
    data = {}
    for child in get_children(client, module, component_type="SENSOR_TILE"):
        prop = get_property(child, "V_FULLDEPL")
        child_serial = get_serial_number(child)

        ## prop is {'code': 'V_FULLDEPL', 'name': 'Depletion Voltage (V)', 'dataType': 'float', 'required': True, 'default': False, 'registrationHidden': False, 'countdown': None, 'permanent': False, 'value': None, 'dateTime': None, 'userIdentity': None}
        ## missing data is None in PDB
        ## TypeError: type NoneType doesn't define __round__ method
        try:
            data[child_serial] = round(prop["value"])
        except TypeError:
            if get_layer_from_sn(serial_number, for_analysis=False) in ["L1", "L2"]:
                data[child_serial] = 50
            else:
                data[child_serial] = 5
            log.warning(
                "Sensor tile does not have depletion voltage set, will return the default expected value for %s (%iV)!",
                itksn.parse(serial_number.encode("utf-8")).component_code,
                data[child_serial],
            )

    return data


def get_test_run(
    client: itkdb.Client, identifier: str, eos: bool = False
) -> (ProdDBTestRun, str, str):
    """
    Get test run information using identifier (id).

    Args:
        client: itkdb client to query for test run information
        identifier: identifier of test run to get information for
        eos: whether to include eos tokens or not

    Returns:
        test_run (:obj:`dict`): information about the test run from prodDB
        serial_number (:obj:`str`): component serial number associated with test run
        stage (:obj:`str`): stage the test run was evaluated at
    """
    try:
        test_run = client.get(
            "getTestRun", json={"testRun": identifier, "noEosToken": not eos}
        )
    except itkdb.exceptions.BadRequest as exc:
        msg = "An unknown error occurred. Please see the log."
        with contextlib.suppress(Exception):
            message = exc.response.json()
            if "ucl-itkpd-main/getComponent/testRunDoesNotExist" in message.get(
                "uuAppErrorMap", {}
            ):
                msg = f"test run with {identifier} not in ITk Production DB."

        raise ValueError(msg) from exc

    test_component = test_run["components"][0]
    serial_number = get_serial_number(test_component)
    tested_at_stage = test_component["testedAtStage"]["code"]
    return (test_run, serial_number, tested_at_stage)
