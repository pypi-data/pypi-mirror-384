from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from typing import Any

import arrow
import itksn
from bson import ObjectId
from module_qc_data_tools.utils import get_layer_from_sn

from module_qc_database_tools.typing_compat import LocalDBComponent

log = logging.getLogger(__name__)


def validate_sn(sn):
    """
    Validate the user input SN is compatible.
    Returns True for a valid SN, otherwise False.
    """

    if not isinstance(sn, str):
        return False

    return re.fullmatch(r"20UP[G,I,Q][A-Z][A-Z0-9][0-9]{7}", sn)


def get_component(database, identifier) -> (LocalDBComponent, str):
    """
    Get component information using identifier (serial number or id).

    Args:
        database (:obj:`pymongo.database.Database`): mongoDB database to query for component information
        identifier (:obj:`str`): identifier of component to get information for (serial number or id)

    Returns:
        component (:obj:`dict`): information about the component from localDB
        stage (:obj:`str`): current stage of component
    """
    if ObjectId.is_valid(identifier):
        component = database.component.find_one({"_id": ObjectId(identifier)})
    else:
        component = database.component.find_one({"serialNumber": identifier})

    if not component:
        msg = f"component with {identifier} not in your localDB"
        raise ValueError(msg)

    serial_number = component["serialNumber"]

    component_stage = get_stage(database, component)
    if not component_stage:
        msg = f"component {serial_number} does not have any QC status. Something went wrong in your localDB."
        raise ValueError(msg)

    return (component, component_stage)


def get_serial_number(component: LocalDBComponent) -> str:
    """
    Get the serial number from the component.

    Args:
        component (:obj:`dict`): localDB component to get serial number from

    Returns:
        serial_number (:obj:`str`): serial number of component
    """
    return component["serialNumber"]


def get_property(component: LocalDBComponent, code: str) -> Any:
    """
    Get the property from the component.

    Args:
        component (:obj:`dict`): localDB component to get property information for
        code (:obj:`str`): property code to retrieve

    Returns:
        property (:obj:`dict` or None): property dictionary
    """
    for prop in component.get("properties", []):
        if prop.get("code") == code:
            return prop
    return None


def get_qc_status(database, component: LocalDBComponent) -> str | None:
    """
    Get the module QC status.

    Args:
        component (:obj:`dict`): localDB component to get stage from

    Returns:
        QC (:obj:`dict`): QC status of component
    """
    component_id = str(component["_id"])

    return database.QC.module.status.find_one({"component": component_id})


def get_stage(database, component: LocalDBComponent) -> str | None:
    """
    Get the stage from the component.

    Args:
        component (:obj:`dict`): localDB component to get stage from

    Returns:
        stage (:obj:`str`): stage of component
    """
    component_qcstatus = get_qc_status(database, component)
    return component_qcstatus.get("stage")


def get_qc_result(database, identifier: ObjectId | str):
    """
    Get the QC result for a given identifier

    Args:
        identifier (:obj:`bson.objectid.ObjectId` or :obj:`str`): object id for the result to get information about

    Returns:
        result (:obj:`dict`): QC result from localDB
    """
    if not ObjectId.is_valid(identifier):
        msg = f"{identifier} is not a valid ObjectId"
        raise ValueError(msg)

    result = database.QC.result.find_one({"_id": ObjectId(identifier)})
    if not result:
        msg = f"result with {identifier} not in your localDB"
        raise ValueError(msg)

    return result


def get_children(
    database, component: LocalDBComponent, *, component_type, ignore_types=None
) -> Iterator[LocalDBComponent]:
    """
    Get (unique!) children for component by ID matching the component type from Local DB.

    !!! note

        This returns a generator.

    Args:
        database (:obj:`pymongo.database.Database`): mongoDB database to query for parent-child relationship
        component (:obj:`dict`): the top-level component to recursively get the children of
        component_type (:obj:`str` or :obj:`None`): the component type code to filter children by (None for any)
        ignore_types (:obj:`list` or :obj:`None`): component types to ignore

    Returns:
        children (:obj:`iterator`): generator of localDB components matching the component type
    """

    def _recursive(
        database, component_id: str, *, component_type, ignored_types
    ) -> Iterator[LocalDBComponent]:
        component = database.component.find_one({"_id": ObjectId(component_id)})
        yielded = set()

        current_component_type = component.get("componentType")
        if (
            current_component_type == component_type or component_type is None
        ) and current_component_type not in ignored_types:
            yield component

        for child_id in database.childParentRelation.find(
            {"parent": component_id}
        ).distinct("child"):
            # yield from get_children(database, child_id, component_type=component_type)
            for child in _recursive(
                database,
                child_id,
                component_type=component_type,
                ignored_types=ignored_types,
            ):
                if child["_id"] in yielded:
                    continue
                yield child
                yielded.add(child["_id"])

    component_id = str(component["_id"])
    yield from _recursive(
        database,
        component_id,
        component_type=component_type,
        ignored_types=ignore_types or [],
    )


def set_component_stage(database, serial_number: str, stage: str, *, userdb) -> None:
    """
    Set component (by serial number) to the current stage.

    Args:
        database (:obj:`pymongo.database.Database`): mongoDB database to set QC status for stage
        serial_number (:obj:`str`): serial number of component
        stage (:obj:`str`): code of stage to set component to
        userdb (:obj:`pymongo.database.Database`): mongoDB database to query for stage information

    Returns:
        None
    """
    component = database.component.find_one({"serialNumber": serial_number})
    component_id = str(component["_id"])
    ldb_component_type = component["componentType"]

    ctype_map = {
        "module": "MODULE",
        "module_pcb": "PCB",
        "bare_module": "BARE_MODULE",
        "sensor_tile": "SENSOR_TILE",
        "front-end_chip": "FE_CHIP",
        "ob_bare_module_cell": "OB_BARE_MODULE_CELL",
        "ob_loaded_module_cell": "OB_LOADED_MODULE_CELL",
    }

    pdb_component_type = ctype_map[ldb_component_type]
    stages = userdb.QC.stages.find_one({"code": pdb_component_type}).get("stage_flow")

    if stage not in stages:
        msg = f"{stage} is not a valid stage on this component type: {pdb_component_type} ({ldb_component_type})"
        raise ValueError(msg)

    return (
        database.QC.module.status.update_one(
            {"component": component_id}, {"$set": {"stage": stage}}
        ).modified_count
        == 1
    )


# pylint: disable=duplicate-code
def get_bom_info(database, serial_number: str):
    """
    Fetch BoM version from LocalDB

    Args:
        database (:obj:`pymongo.database.Database`): mongoDB database to query for test run information
        serial_number (str): serial number of the component to fetch BoM info for.

    Returns:
        bom_info (:obj:`dict`): dict of the code/value pair of the BoM version

    """
    module, _ = get_component(database, serial_number)
    for child in get_children(database, module, component_type="module_pcb"):
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
def get_full_depletion_voltage(database, serial_number):
    """
    Fetch full depletion voltage from LocalDB

    Args:
        database (:obj:`pymongo.database.Database`): mongoDB database to query for test run information
        serial_number (str): serial number of the component to fetch the full depletion voltage for

    Returns:
        dict[str, float]: mapping between child serial number and full depletion voltage
    """

    module, _ = get_component(database, serial_number)
    data = {}
    for child in get_children(database, module, component_type="sensor_tile"):
        prop = get_property(child, "V_FULLDEPL")
        child_serial = get_serial_number(child)

        ## prop is {'code': 'V_FULLDEPL', 'name': 'Depletion Voltage (V)', 'dataType': 'float', 'required': True, 'default': False, 'registrationHidden': False, 'countdown': None, 'permanent': False, 'value': None, 'dateTime': None, 'userIdentity': None}
        ## missing data is None in LDB
        ## TypeError: type NoneType doesn't define __round__ method
        try:
            data[child_serial] = round(prop["value"])
        except TypeError:  ## used to be exceptions.MissingData
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


def get_stage_flow(database, code="MODULE"):
    """
    Get the stage flow list of the specified component
    """
    stage_doc = database.QC.stages.find_one({"code": code})
    return stage_doc.get("stage_flow", [])


def get_alternatives(database, code="MODULE"):
    """
    Get the alternative stage list of the specified component
    """
    stage_doc = database.QC.stages.find_one({"code": code})
    return stage_doc.get("alternatives", [])


def get_disabled_tests(database, code="MODULE"):
    """
    Get the disabled stage/test document
    """
    stage_doc = database.QC.stages.find_one({"code": code})
    return stage_doc.get("disabled_tests", {})


def component_type_to_code(component_type):
    """
    Convert LocalDB component type to the component type code
    """
    _map = {"front-end_chip": "FE_CHIP", "module_pcb": "PCB"}

    return _map.get(component_type.lower(), component_type).upper()


def get_raw_data(database, _id):
    """
    Retrieve a RAW format from LocalDB by (stringified) ObjectId
    """
    return database.QC.testRAW.find_one({"_id": ObjectId(_id)})


def format_date(mongo_date):
    """
    Make a format suitable for printing for date records in Mongo
    """
    dt = arrow.get(mongo_date).replace(microsecond=0).to("local")

    return str(dt)
