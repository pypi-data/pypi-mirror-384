from __future__ import annotations

import logging

import itkdb

from module_qc_database_tools import db
from module_qc_database_tools.iv import localdb, proddb
from module_qc_database_tools.utils import ComponentType, get_component_type

log = logging.getLogger(__name__)


def get_reference_info(
    serial_number: str,
    *,
    reference_component_type: str | None,
    reference_stage: str | None,
    reference_test_type: str | None,
):
    """
    Get the pre-defined reference mapping for a given serial number.

    This parses the serial number to determine the component type.

    Args:
        serial_number (:obj:`str`): the serial number of the component.
        reference_component_type (:obj:`str` or :obj:`None`): component type code to use as reference instead of the pre-defined one for the component. Set to `None` to keep defaults.
        reference_stage (:obj:`str` or :obj:`None`): stage code to use as reference stage instead of the pre-defined one for the component. Set to `None` to keep defaults.
        reference_test_type (:obj:`str` or :obj:`None`): test type code to use as reference test type instead of the pre-defined one for the component. Set to `None` to keep defaults.

    Returns:
        reference_info (:obj:`dict`): reference information dictionary containing information about the component type, stage, and test type to use as reference / look-up for IV measurements.
    """
    reference_map = {
        ComponentType.QuadModule: {
            "componentType": "SENSOR_TILE",
            "stage": "BAREMODULERECEPTION",
            "testType": "IV_MEASURE",
        },
        ComponentType.TripletModule: {
            "componentType": "SENSOR_TILE",
            "stage": "BAREMODULERECEPTION",
            "testType": "IV_MEASURE",
        },
        ComponentType.BareModule: {
            "componentType": "SENSOR_TILE",
            "stage": "sensor_manufacturer",
            "testType": "IV_MEASURE",
        },
        ComponentType.SensorTile: {
            "componentType": "SENSOR_TILE",
            "stage": "sensor_manufacturer",
            "testType": "IV_MEASURE",
        },
    }

    component_type = get_component_type(serial_number)
    reference_info = reference_map.get(component_type)
    if not reference_info:
        msg = (
            f"There is no reference information for component type '{component_type}'."
        )
        raise ValueError(msg)

    reference_info["componentType"] = (
        reference_component_type or reference_info["componentType"]
    )
    reference_info["stage"] = reference_stage or reference_info["stage"]
    reference_info["testType"] = reference_test_type or reference_info["testType"]
    return reference_info


def fetch_reference_ivs(
    db_or_client,
    serial_number,
    *,
    reference_component_type=None,
    reference_stage=None,
    reference_test_type=None,
):
    """
    Generate the reference IVs for a component.

    Args:
        db_or_client (:obj:`pymongo.database.Database` or :obj:`itkdb.Client`): The database instance (if fetching from localDB) or client instance (if fetching from prodDB) to retrieve information from.
        serial_number (str): serial number of the component to fetch reference IVs for.
        reference_component_type (:obj:`str` or :obj:`None`): component type code to use as reference instead of the pre-defined one for the component. Leave as `None` to default to automatic.
        reference_stage (:obj:`str` or :obj:`None`): stage code to use as reference stage instead of the pre-defined one for the component. Leave as `None` to default to automatic.
        reference_test_type (:obj:`str` or :obj:`None`): test type code to use as reference test type instead of the pre-defined one for the component. Leave as `None` to default to automatic.

    Returns:
        reference_ivs (:obj:`list`): list of reference IV measurements (:obj:`dict`) for use by module-qc-analysis-tools.
    """
    data = {
        "target_component": serial_number,
        "target_stage": None,
        "reference_IVs": [],
    }

    reference_info = get_reference_info(
        serial_number,
        reference_component_type=reference_component_type,
        reference_stage=reference_stage,
        reference_test_type=reference_test_type,
    )

    use_localdb = not isinstance(db_or_client, itkdb.Client)

    # note: localDB stores componentType as lowercase no matter what
    reference_info["componentType"] = (
        reference_info["componentType"].lower()
        if use_localdb
        else reference_info["componentType"]
    )

    log.info("[u]Reference information[/]")
    log.info("  - component type: [yellow]%s[/]", reference_info["componentType"])
    log.info("  - stage: [yellow]%s[/]", reference_info["stage"])
    log.info("  - test type: [yellow]%s[/]", reference_info["testType"])

    get_component = db.local.get_component if use_localdb else db.prod.get_component
    get_children = db.local.get_children if use_localdb else db.prod.get_children
    get_reference_iv_testRuns = (
        localdb.get_reference_iv_testRuns
        if use_localdb
        else proddb.get_reference_iv_testRuns
    )

    component, data["target_stage"] = get_component(db_or_client, serial_number)

    reference_components = list(
        get_children(
            db_or_client, component, component_type=reference_info["componentType"]
        )
    )

    msg = f"Found {len(reference_components)} reference component{'s' if len(reference_components) != 1 else ''}: [yellow]{', '.join(ref['serialNumber'] for ref in reference_components)}[/]"
    log.info(msg)

    reference_iv_testRuns = get_reference_iv_testRuns(
        db_or_client,
        reference_components,
        reference_stage=reference_info["stage"],
        reference_testType=reference_info["testType"],
    )

    for ref_component, ref_iv_testRun in zip(
        reference_components, reference_iv_testRuns
    ):
        ref_comp_props = {
            prop["code"]: prop["value"] for prop in ref_component["properties"]
        }
        prop_Vfd = ref_comp_props.get("V_FULLDEPL", -999.0)
        prop_Vbd = ref_comp_props.get("BREAKDOWN_VOLTAGE", -999.0)
        prop_Ilc = -999.0  # not a property of the component?

        if not prop_Vfd:
            log.warning(
                "'%s' is not set correctly as a component property, will assume -999.0. It is set as '%s'.",
                "V_FULLDEPL",
                prop_Vfd,
            )
            prop_Vfd = -999.0
        if not isinstance(prop_Vfd, (float, int)):
            log.warning(
                "Wrong type for '%s' property on the component. It was type [red]'%s'[/] and we expected [white]'float'[/].",
                "V_FULLDEPL",
                type(prop_Vfd).__name__,
            )
            prop_Vfd = float(prop_Vfd)

        if not prop_Vbd:
            log.warning(
                "'%s' is not set correctly as a component property, will assume -999.0. It is set as '%s'.",
                "BREAKDOWN_VOLTAGE",
                prop_Vbd,
            )
            prop_Vbd = -999.0
        if not isinstance(prop_Vbd, (float, int)):
            log.warning(
                "Wrong type for '%s' property on the component. It was type [red]'%s'[/] and we expected [white]'float'[/].",
                "BREAKDOWN_VOLTAGE",
                type(prop_Vbd).__name__,
            )
            prop_Vbd = float(prop_Vbd)

        if ref_iv_testRun is None:
            msg = f"Reference IV is not found for {ref_component['serialNumber']}, please fix this in the production database!"
            raise ValueError(msg)

        if use_localdb:
            ref_iv_results = ref_iv_testRun["results"]
            ref_iv_props = ref_iv_results.get("property") or ref_iv_results.get(
                "properties"
            )
        else:
            ref_iv_results = {
                result["code"]: result["value"] for result in ref_iv_testRun["results"]
            }
            ref_iv_props = {
                prop["code"]: prop["value"]
                for prop in (ref_iv_testRun.get("properties") or [])
            }

        try:
            ref_iv_Vbd = ref_iv_results["BREAKDOWN_VOLTAGE"]
        except KeyError:
            log.error(
                "No '%s' key was found in the IV measurement. The following keys exist: [white]%s[/].",
                "BREAKDOWN_VOLTAGE",
                ", ".join(ref_iv_results.keys()),
            )
            raise

        if not isinstance(ref_iv_Vbd, (float, int)):
            log.warning(
                "Wrong type for '%s' result on the test run. It was type [red]'%s'[/] and we expected [white]'float'[/].",
                "BREAKDOWN_VOLTAGE",
                type(ref_iv_Vbd).__name__,
            )
            try:
                ref_iv_Vbd = float(ref_iv_Vbd)
            except TypeError:
                log.error(
                    "Unable to coerce '%s' of the IV measurement to [white]'float'[/].",
                    "BREAKDOWN_VOLTAGE",
                )
                raise

        try:
            ref_iv_Ilc = ref_iv_results["LEAK_CURRENT"]
        except KeyError:
            log.error(
                "No '%s' key was found in the IV measurement. The following keys exist: [white]%s[/].",
                "LEAK_CURRENT",
                ", ".join(ref_iv_results.keys()),
            )
            raise

        if not isinstance(ref_iv_Ilc, (float, int)):
            log.warning(
                "Wrong type for '%s' result on the test run. It was type [red]'%s'[/] and we expected [white]'float'[/].",
                "LEAK_CURRENT",
                type(ref_iv_Ilc).__name__,
            )
            try:
                ref_iv_Ilc = float(ref_iv_Ilc)
            except TypeError:
                log.error(
                    "Unable to coerce '%s' of the IV measurement to [white]'float'[/].",
                    "LEAK_CURRENT",
                )
                raise

        try:
            ref_iv_voltage = ref_iv_results["IV_ARRAY"]["voltage"]
        except KeyError:
            log.error(
                "No 'voltage' key was found in the IV measurement. The following keys exist: [white]%s[/].",
                ", ".join(ref_iv_results["IV_ARRAY"].keys()),
            )
            raise

        try:
            ref_iv_current = ref_iv_results["IV_ARRAY"]["current"]
        except KeyError:
            log.error(
                "No 'current' key was found in the IV measurement. The following keys exist: [white]%s[/].",
                ", ".join(ref_iv_results["IV_ARRAY"].keys()),
            )
            raise

        try:
            props_temp = ref_iv_props["TEMP"]
        except KeyError:
            log.error(
                "No '%s' key was found in the IV measurement properties. The following properties exist: [white]%s[/].",
                "TEMP",
                ", ".join(ref_iv_props.keys()),
            )
            raise

        try:
            props_hum = ref_iv_props["HUM"]
        except KeyError:
            log.error(
                "No '%s' key was found in the IV measurement properties. The following properties exist: [white]%s[/].",
                "HUM",
                ", ".join(ref_iv_props.keys()),
            )
            raise

        ref_iv_temperature = ref_iv_results["IV_ARRAY"].get("temperature") or []
        ref_iv_humidity = ref_iv_results["IV_ARRAY"].get("humidity") or []

        data["reference_IVs"].append(
            {
                "component_sn": ref_component.get("serialNumber"),
                "stage": reference_info.get("stage"),
                "Vbd": ref_iv_Vbd if ref_iv_Vbd >= 0.0 else prop_Vbd,
                "Vfd": prop_Vfd,  # localDB used CV to get this information, but this is on sensor tile
                "Ilc": ref_iv_Ilc if ref_iv_Ilc >= 0.0 else prop_Ilc,
                "temperature": props_temp,
                "IV_ARRAY": {
                    "voltage": ref_iv_voltage,
                    "current": ref_iv_current,
                    "temperature": ref_iv_temperature
                    or [props_temp] * len(ref_iv_current),
                    "humidity": ref_iv_humidity or [props_hum] * len(ref_iv_current),
                },
                "qc_passed": ref_iv_testRun["passed"],
            }
        )

    return data
