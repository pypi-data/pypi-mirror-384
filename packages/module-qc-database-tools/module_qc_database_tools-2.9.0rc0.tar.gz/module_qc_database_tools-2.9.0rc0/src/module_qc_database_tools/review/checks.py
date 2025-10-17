from __future__ import annotations

from packaging.version import Version

from module_qc_database_tools.exceptions import SkipCheck
from module_qc_database_tools.review.helpers import Check, onlyif
from module_qc_database_tools.typing_compat import (
    Dict,
    InstitutionCode,
    Set,
    StageCode,
    TestTypeCode,
    Tuple,
)

checker = Check(allowed_params={"top_component", "component", "test_run"})

REQUIREMENTS_ELECTRICAL_TESTS: Set[TestTypeCode] = {
    "ADC_CALIBRATION",
    "ANALOG_READBACK",
    "DATA_TRANSMISSION",
    "INJECTION_CAPACITANCE",
    "IV_MEASURE",
    "LP_MODE",
    "MIN_HEALTH_TEST",
    "PIXEL_FAILURE_ANALYSIS",
    "SLDO",
    "TUNING",
    "VCAL_CALIBRATION",
}
REQUIREMENTS_MQT: str = "2.3.0"
REQUIREMENTS_YARR: str = "1.5.3"
REQUIREMENTS_MQAT: str = "2.2.9rc4"
REQUIREMENTS_ESUMMARY_LINKS: Set[TestTypeCode] = {
    "ADC_CALIBRATION",
    "ANALOG_READBACK",
    "DATA_TRANSMISSION",
    "INJECTION_CAPACITANCE",
    "LP_MODE",
    "MIN_HEALTH_TEST",
    "PIXEL_FAILURE_ANALYSIS",
    "SLDO",
    "TUNING",
    "VCAL_CALIBRATION",
}
REQUIREMENTS_ESUMMARY_SKIP: Dict[
    Tuple[InstitutionCode, StageCode], Set[TestTypeCode]
] = {
    ("LPNHE", "MODULE/THERMAL_CYCLES"): REQUIREMENTS_ESUMMARY_LINKS,
    ("LPNHE", "MODULE/LONG_TERM_STABILITY_TEST"): REQUIREMENTS_ESUMMARY_LINKS,
    ("HR", "MODULE/POST_PARYLENE_WARM"): REQUIREMENTS_ESUMMARY_LINKS
    - {"PIXEL_FAILURE_ANALYSIS"},
}


def _only_if_latest_stage_test_run(*, top_component, test_run):
    """
    Skip a check if the stage of the test run is not the stage of the top-level component.
    """
    if top_component.current_stage != test_run.stage:
        msg = f"Skipping as test run is at {test_run.stage} != {top_component.current_stage}"
        raise SkipCheck(msg)


def _generate_esummary_links_table_docstring(indent=4):
    """
    This function is used internally to generate docstrings for check_missing_links_esummary.
    """
    # NB: the "\n" is very important to render docstrings properly
    docstring = """\n| Institute | Stage | Required Links |
| --------- | ----- | -------------- |
"""
    for (
        institute_code,
        stage_code,
    ), skipped_links in REQUIREMENTS_ESUMMARY_SKIP.items():
        required_links = REQUIREMENTS_ESUMMARY_LINKS - skipped_links
        required_links_str = (
            f"`{'`, `'.join(required_links)}`" if required_links else "None"
        )
        docstring += f"| `{institute_code}` | `{stage_code}` | {required_links_str} |\n"

    indent_str = " " * indent
    return indent_str + (f"\n{indent_str}").join(docstring.splitlines())


@checker
def check_same_stage(top_component, component):
    """
    !!! success

        All child components are the same stage as the top-level component.

    !!! info "Resolution"

        First, understand why the stages are decoupled and then, if necessary, fix using [`mqdbt sync-component-stages`][mqdbt-sync-component-stages].

    Ensure that stage coherency is respected for pixel modules.
    """
    assert top_component.current_stage == component.current_stage, (
        f"Component {component.serial_number} is not at the same stage of the top component: {top_component.current_stage} != {component.current_stage}"
    )


@checker
@onlyif("component", lambda x: x.component_type == "FE_CHIP", "not a front-end chip")
def check_chip_configs(component):
    """
    !!! success

        Every front-end chip has the required chip configs uploaded:

        - warm config
        - cold config
        - LP config

    !!! info "Resolution"

        Upload the missing chip configurations to the front-end chips.
    """
    assert len(component.attachments) == 3, (
        "must have three chip configs (warm, cold, LP)"
    )
    for title in ["warm", "cold", "LP"]:
        assert any(
            attachment.title.endswith(f"{title}.json")
            for attachment in component.attachments
        ), f"missing {title} attachment"


@checker
@onlyif(
    "test_run",
    lambda x: x.test_type in REQUIREMENTS_ELECTRICAL_TESTS,
    "not an electrical test",
)
@onlyif("component", lambda x: x.component_type == "FE_CHIP", "not a front-end chip")
def check_attachments_exist_electrical(test_run, component):  # noqa: ARG001  # pylint: disable=unused-argument
    """
    !!! success

        Electrical QC tests have the necessary attachments:

        - `RAW` attachments
        - `Attachment_Pack.zip` attachments

    !!! info "Resolution"

        Upload the missing attachments to the corresponding tests.
    """
    titles = [attachment.title for attachment in test_run.attachments]
    if test_run.test_type not in [
        "MIN_HEALTH_TEST",
        "PIXEL_FAILURE_ANALYSIS",
        "TUNING",
    ]:
        assert "RAW" in titles, "Missing RAW attachment"
    assert any(title.endswith("Attachment_Pack.zip") for title in titles), (
        "Missing Attachment Pack attachment"
    )


@checker
@onlyif(
    "test_run", lambda x: x.test_type == "VISUAL_INSPECTION", "not visual inspection"
)
def check_attachments_exist_vis_inspect(test_run):
    """
    !!! success

        Visual inspect tests have the necessary attachments: `front_image`, `back_image`.

    !!! info "Resolution"

        Upload the missing attachments to the corresponding tests.

    Visual inspection tests all require `front_image` (as determined from [mqneg][]), however only the following component types and stages require the `back_image`:

    | Component Type | Stage Name                   | `back_image`     |
    | -------------- | ---------------------------- | ---------------- |
    | `MODULE`       | `MODULE/ASSEMBLY`            | :material-check: |
    | `MODULE`       | `MODULE/PARYLENE_COATING`    |                  |
    | `MODULE`       | `MODULE/PARYLENE_MASKING`    | :material-check: |
    | `MODULE`       | `MODULE/PARYLENE_UNMASKING`  | :material-check: |
    | `MODULE`       | `MODULE/POST_PARYLENE_WARM`  |                  |
    | `MODULE`       | `MODULE/THERMAL_CYCLES`      | :material-check: |
    | `MODULE`       | `MODULE/WIREBONDING`         |                  |
    | `MODULE`       | `MODULE/WIREBOND_PROTECTION` |                  |
    | `PCB`          | `PCB_POPULATION`             |                  |
    | `PCB`          | `PCB_RECEPTION`              |                  |
    | `PCB`          | `PCB_RECEPTION_MODULE_SITE`  | :material-check: |
    | `BARE_MODULE`  | `BAREMODULERECEPTION`        | :material-check: |
    """
    titles = [attachment.title for attachment in test_run.attachments]
    required_attachments = ["front_image", "back_image"]
    if test_run.components[0].tested_at_stage in [
        "MODULE/POST_PARYLENE_WARM",
        "MODULE/PARYLENE_COATING",
        "MODULE/WIREBONDING",
        "MODULE/WIREBOND_PROTECTION",
        "PCB_POPULATION",
        "PCB_RECEPTION",
    ]:
        required_attachments.remove("back_image")

    for req in required_attachments:
        assert req in titles, f"Missing {req} attachment"


@checker
@onlyif(
    "test_run",
    lambda x: x.test_type in REQUIREMENTS_ELECTRICAL_TESTS,
    "not an electrical test",
)
@onlyif("component", lambda x: x.component_type == "FE_CHIP", "not a front-end chip")
def check_mqt_version(top_component, component, test_run):  # noqa: ARG001  # pylint: disable=unused-argument
    """
    Enforce a minimum required [mqt][] version or [yarr][] version.

    !!! success

        The minimum required versions are:

        - module-qc-tools: `v{required_mqt}`
        - yarr: `v{required_yarr}`

    !!! info "Resolution"

        There is no known resolution for right now. This will be expected to fail.
    """
    _only_if_latest_stage_test_run(top_component=top_component, test_run=test_run)
    if test_run.test_type not in [
        "MIN_HEALTH_TEST",
        "PIXEL_FAILURE_ANALYSIS",
        "TUNING",
    ]:
        measurement_version = test_run.properties.get("MEASUREMENT_VERSION")
        assert measurement_version, "Measurement version is not defined"
        assert Version(measurement_version) >= Version(REQUIREMENTS_MQT), (
            f"{measurement_version} is not at least {REQUIREMENTS_MQT}"
        )

    else:
        yarr_version = test_run.properties.get("YARR_VERSION")
        assert yarr_version, "YARR version is not defined"
        assert Version(yarr_version) >= Version(REQUIREMENTS_YARR), (
            f"{yarr_version} is not at least {REQUIREMENTS_YARR}"
        )


check_mqt_version.__doc__ = check_mqt_version.__doc__.format(
    required_mqt=REQUIREMENTS_MQT, required_yarr=REQUIREMENTS_YARR
)


@checker
@onlyif(
    "test_run",
    lambda x: x.test_type in REQUIREMENTS_ELECTRICAL_TESTS,
    "not an electrical test",
)
@onlyif("component", lambda x: x.component_type == "FE_CHIP", "not a front-end chip")
def check_mqat_version(top_component, component, test_run):  # noqa: ARG001  # pylint: disable=unused-argument
    """
    Enforce a minimum required [mqat][] version.

    !!! success

        The minimum required version for module-qc-analysis-tools is `v{required_mqat}`.

    !!! info "Resolution"

        Recycle (_regrade_) the test run using a newer version of [mqat][].
    """
    _only_if_latest_stage_test_run(top_component=top_component, test_run=test_run)
    analysis_version = test_run.properties["ANALYSIS_VERSION"]
    assert Version(analysis_version) >= Version(REQUIREMENTS_MQAT), (
        f"{analysis_version} is not at least {REQUIREMENTS_MQAT}"
    )


check_mqat_version.__doc__ = check_mqat_version.__doc__.format(
    required_mqat=REQUIREMENTS_MQAT
)


@checker
@onlyif("component", lambda x: x.component_type == "SENSOR_TILE", "not a sensor tile")
def check_iv_measure_sensor_tile(component):
    """
    !!! success

        Sensor tile components have an IV measurement test run.

    !!! info "Resolution"

        Identify the institute responsible for the sensor tile and make sure they upload the IV measurement.

    The IV measurement is needed on the sensor tile in order to perform the QA of module IV measurements.
    """
    assert "IV_MEASURE" in [test_run.test_type for test_run in component.test_runs], (
        "No IV Measurement"
    )


@checker
@onlyif("component", lambda x: x.component_type == "BARE_MODULE", "not a bare module")
def check_iv_measure_bare_module(component):
    """
    !!! success

        Bare modules have a sensor tile and link to the correct sensor tile IV measurement from `BARE_MODULE_SENSOR_IV`.

    !!! info "Resolution"

        Identify the institute responsible for the bare module and make sure they either:

        - upload a `BARE_MODULE_SENSOR_IV` test run to the bare module
        - ensure the link from the `BARE_MODULE_SENSOR_IV` test run links to the right IV measurement on the sensor tile
    """
    bare_module_sensor_ivs = [
        test_run
        for test_run in component.test_runs
        if test_run.test_type == "BARE_MODULE_SENSOR_IV"
    ]
    assert bare_module_sensor_ivs, "No BARE_MODULE_SENSOR_IV test run found"
    assert len(bare_module_sensor_ivs) == 1, (
        "Multiple BARE_MODULE_SENSOR_IV test runs found"
    )
    bare_module_sensor_iv = bare_module_sensor_ivs[0]
    link_sensor_iv = bare_module_sensor_iv.results["LINK_TO_SENSOR_IV_TEST"]
    assert link_sensor_iv is not None, "Link is not set for sensor IV"
    assert isinstance(link_sensor_iv, dict), "Unknown value for sensor IV link"

    sensor_tiles = [
        child for child in component.children if child.component_type == "SENSOR_TILE"
    ]
    assert sensor_tiles, "No sensor tile component"
    assert len(sensor_tiles) == 1, "Multiple sensor tiles found"
    sensor_tile = sensor_tiles[0]

    sensor_iv_ids = [
        test_run.id
        for test_run in sensor_tile.test_runs
        if test_run.test_type == "IV_MEASURE"
    ]
    assert link_sensor_iv["id"] in sensor_iv_ids, (
        f"BARE_MODULE_SENSOR_IV is not correctly linked to its child SENSOR_TILE IV_MEASUREMENT. It has '{link_sensor_iv['id']}' which does not match one of {sensor_iv_ids}"
    )


@checker
@onlyif("test_run", lambda x: x.test_type == "E_SUMMARY", "not an E_SUMMARY")
def check_missing_links_esummary(test_run):
    """
    !!! success

        E-Summary has all test run links filled out correctly.

    !!! info "Resolution"

        There are two scenarios that will occur:

        1. If your institute representative has not talked with the Module QC experts on the appropriate stage/testing flow for your site, please do so first.
        2. Otherwise, please create an E-Summary with the missing tests linked correctly using [mqat][].

    The requirements will be a combination of site/stage as needed.

    All E-Summaries are required to have the following links:

    {required_links}

    Some exceptions are agreed upon between the Module QC experts and the site based on the following table:

    {required_table}
    """
    skipped_links = REQUIREMENTS_ESUMMARY_SKIP.get(
        (test_run.institution, test_run.stage), set()
    )
    required_links = REQUIREMENTS_ESUMMARY_LINKS - skipped_links

    for key, result in test_run.results.items():
        if "_LINK_" not in key:
            continue
        if not any(skip_link in key for skip_link in required_links):
            continue
        assert result is not None, f"Link is not set for {key}"
        assert isinstance(result, dict), f"Unknown value for link {key}"


check_missing_links_esummary.__doc__ = check_missing_links_esummary.__doc__.format(
    required_links="- `" + "`\n    - `".join(sorted(REQUIREMENTS_ESUMMARY_LINKS)) + "`",
    required_table=_generate_esummary_links_table_docstring(),
)


@checker
def check_duplicate_attachment_titles(test_run):
    """
    !!! success

        Test runs have attachments with unique titles.

    !!! info "Resolution"

        Please use [itkdb][] to fix your attachment titles manually for the affected components:

        ```python
        import itkdb

        c = itkdb.Client()

        c.post(
            "updateTestRunAttachment",
            json={
                "testRun": "01aacb...fe",  # (1)!
                "code": "68af1e...12",  # (2)!
                "title": "theNewTitle",  # (3)!
            },
        )
        ```

        1. The code of the test run
        2. The code of the attachment
        3. The new title to set for the attachment

        For more information on this API command, see [updateTestRunAttachment](https://uuapp.plus4u.net/uu-bookkit-maing01/41f76117152c4c6e947f498339998055/book/page?code=96624033) in the production database.
    """
    attachment_titles = [attachment.title for attachment in test_run.attachments]
    assert len(attachment_titles) == len(set(attachment_titles)), (
        "Test run has attachments with duplicate titles"
    )


@checker
@onlyif("test_run", lambda x: x.test_type == "FECHIP_TEST", "not a front-end chip test")
@onlyif("test_run", lambda x: x.stage == "TESTONWAFER", "not testing on wafer")
def check_missing_fechip_test_data(test_run):
    """
    !!! success

        No required FE Chip Wafer Probing data is missing.

    !!! info "Resolution"

        Please contact experts if data is missing. The corresponding front-end chip should not be considered "green" for the purposes of production.

    !!! info "Obsoleted Keys"

        Some keys are obsoleted. [June 4th 2025)(https://indico.cern.ch/event/1556173/contributions/6552326/attachments/3080812/5453178/250604_Waferprobing-Meeting.pdf) presentation obsoleted the following:
        - `I_TOT_CONF_VALUE`
        - `I_VINA_CONF_VALUE`
        - `I_VIND_CONF_VALUE`
        - `RESISTOR`
        - `NOCCSCAN_VALUE`
        - `PIXEL_REGISTER_TEST`
        - `VREF_ADC_TRIM`
        - `VREF_ADC_TRIM_VALUE`

    """

    potential_missing_keys = set()
    for key, result in test_run.results.items():
        if result not in ["-1", -1]:
            continue
        potential_missing_keys.add(key)

    veto_keys = {
        "I_TOT_CONF_VALUE",
        "I_VINA_CONF_VALUE",
        "I_VIND_CONF_VALUE",
        "RESISTOR",
        "NOCCSCAN_VALUE",
        "PIXEL_REGISTER_TEST",
        "VREF_ADC_TRIM",
        "VREF_ADC_TRIM_VALUE",
    }

    missing_keys = potential_missing_keys - veto_keys
    assert len(missing_keys) == 0, f"Keys are missing: {missing_keys}"


__all__ = ("checker",)
