from __future__ import annotations

import copy
import json
import logging
import math
import sys
from pathlib import Path

import pandas as pd
import pymongo.database
from bson.objectid import ObjectId
from module_qc_data_tools.utils import (
    chip_serial_number_to_uid,
    get_chip_type_from_serial_number,
)

from module_qc_database_tools.chip_config_api import ChipConfigAPI
from module_qc_database_tools.typing_compat import ModuleType
from module_qc_database_tools.utils import (
    ComponentType,
    DataMergingMode,
    DPPort,
    get_chip_connectivity,
    get_component_type,
)

log = logging.getLogger(__name__)


class Module:
    """
    Module class. Also works with bare module and FE chip.
    """

    def __init__(self, client, serial_number, no_eos_token=False, name=None):
        self.client = client
        self.serial_number = serial_number
        self.name = name if name else self.serial_number
        self.chip_type = get_chip_type_from_serial_number(self.serial_number)
        self.module = None
        self.bare_modules = []
        self.chips = []
        self.sensors = []
        self.orientation = True
        self.sensor_vendor = None
        self.module_type: ModuleType = "quad"
        self.component_type = get_component_type(self.serial_number)

        if self.component_type == ComponentType.FeChip:
            self.chips.append(
                Chip(
                    client,
                    self.serial_number,
                    no_eos_token=no_eos_token,
                    module_name=self.name,
                )
            )
        elif self.component_type == ComponentType.BareModule:
            self.module = client.get("getComponent", json={"component": serial_number})
            for child in self.module["children"]:
                if (
                    child["componentType"]["code"] == "FE_CHIP"
                    and child["component"] is not None
                ):
                    self.chips.append(
                        Chip(
                            client,
                            child["component"]["serialNumber"],
                            no_eos_token=no_eos_token,
                            module_name=self.name,
                        )
                    )
                elif (
                    child["componentType"]["code"] == "SENSOR_TILE"
                    and child["component"] is not None
                ):
                    self.sensors.append(
                        Sensor(
                            client,
                            child["component"]["serialNumber"],
                            no_eos_token=no_eos_token,
                            module_name=self.name,
                        )
                    )
        else:
            self.module = client.get("getComponent", json={"component": serial_number})
            for _property in self.module["properties"]:
                if _property["code"] == "ORIENTATION":
                    self.orientation = _property["value"]
            for child in self.module["children"]:
                if child["componentType"]["code"] == "BARE_MODULE":
                    self.bare_modules.append(
                        client.get(
                            "getComponent",
                            json={"component": child["component"]["serialNumber"]},
                        )
                    )

            _chips = []
            for bare_module in self.bare_modules:
                for child in bare_module["children"]:
                    if (
                        child["componentType"]["code"] == "FE_CHIP"
                        and child["component"] is not None
                    ):
                        _chips.append(
                            Chip(
                                client,
                                child["component"]["serialNumber"],
                                no_eos_token=no_eos_token,
                                module_name=self.name,
                            )
                        )
                    elif (
                        child["componentType"]["code"] == "SENSOR_TILE"
                        and child["component"] is not None
                    ):
                        self.sensors.append(
                            Sensor(
                                client,
                                child["component"]["serialNumber"],
                                no_eos_token=no_eos_token,
                                module_name=self.name,
                            )
                        )
                if len(self.bare_modules) != 3 and not self.orientation:
                    log.info("PCB - bare module orientation is not normal.")
                    self.chips.append(_chips[2])
                    self.chips.append(_chips[3])
                    self.chips.append(_chips[0])
                    self.chips.append(_chips[1])
                else:
                    self.chips = _chips

        if len(self.chips) == 1:
            self.module_type = "single"
            log.info("single bare %s initiated.", self.serial_number)
        elif len(self.bare_modules) == 3 and len(self.chips) == 3:
            self.module_type = "triplet"
            log.info("triplet %s initiated.", self.serial_number)
        elif len(self.bare_modules) == 1 and len(self.chips) == 4:
            self.module_type = "quad"
            log.info("quad module %s initiated.", self.serial_number)
            if len(self.sensors) == 1:
                self.sensor_vendor = self.sensors[0].get_vendor()
        else:
            log.error(
                "Serial number or bare module type is incorrect, please check in the production database!"
            )

    def generate_config(
        self,
        chip_template,
        layer_config,
        dp_port: DPPort,
        suffix,
        version,
        speed=1280,
        reverse=False,
    ):
        """
        Generate module config.
        """
        log.info(
            "Generating module config for module %s with %s from %s version for %i MHz.",
            self.serial_number,
            layer_config,
            version,
            speed,
        )
        if self.module_type == "triplet" and reverse:
            log.info("Orientation is reverse!")

        configs = {"module": {"chipType": self.chip_type, "chips": []}, "chips": []}

        # suffix is warm or warm_4-to-1 (with data merging)
        data_merging = None
        for dm in DataMergingMode:
            if dm.value in suffix:
                data_merging = dm
        for chip_index, chip in enumerate(self.chips):
            tx, rx = get_chip_connectivity(
                dp_port, chip_index, self.module_type, reverse, data_merging
            )

            try:
                configs["chips"].append(
                    chip.generate_config(
                        copy.deepcopy(
                            chip_template
                        ),  # NB: make sure we copy as Chip::generate_config modifies this in-place
                        self.chip_type,
                        chip_index,
                        layer_config,
                        self.module_type,
                        suffix=suffix,
                        speed=speed,
                        version=version,
                        sensor_vendor=self.sensor_vendor,
                    )
                )
            except RuntimeError as snake:
                log.warning(snake)
                continue
            # relative path: e.g. L2_warm/0x15499_L2_warm.json
            chip_config_path = (
                Path(f"{layer_config}{'_' + suffix if suffix else ''}")
                / f"{chip.uid}_{layer_config}{'_' + suffix if suffix else ''}.json"
            )

            configs["module"]["chips"].append(
                {
                    "config": str(chip_config_path),
                    "path": "relToCon",
                    "tx": tx,
                    "rx": rx,
                    "enable": 1,
                    "locked": 0,
                }
            )

        return configs


class Chip:
    """
    Chip class.
    """

    def __init__(self, client, serial_number, no_eos_token=False, module_name=None):
        self.client = client
        self.serial_number = serial_number
        self.uid = chip_serial_number_to_uid(serial_number)
        self.chip_type = get_chip_type_from_serial_number(self.serial_number)
        self.module_name = module_name or self.serial_number
        self.chip = client.get(
            "getComponent",
            json={"component": serial_number, "noEosToken": no_eos_token},
        )
        self.attachments = list(self.chip["attachments"])
        self.test_run = None

        self.ratio_kshunt_kin = 21600 / 21000
        self.target_iref_trim = None

        log.info("chip %s initiated.", self.uid)

        if self.chip["flags"] is not None and len(self.chip["flags"]) > 0:
            log.warning(
                "This chip %s might be problematic, please check the flags in the production database for more info!",
                self.serial_number,
            )
        for prop in self.chip["properties"]:
            if prop["code"] == ["TARGET_IREF_TRIM"]:
                self.target_iref_trim = prop["value"]

    def get_latest_configs(self, item, speed=1280):
        """
        use title for filename:
        'title': '0x12345_<layer_config>_<suffix>.json'
        'title': '0x12345_<layer_config>_<suffix>_<datamerging>.json'
        """
        if item.get("type") == "eos":
            infile = self.client.get(item["url"])
        else:
            comp = self.client.get(
                "getComponent", json={"component": self.serial_number}
            )
            infile = self.client.get(
                "getComponentAttachment",
                json={"component": comp["code"], "code": item["code"]},
            )

        with Path(infile.filename).open(mode="r", encoding="UTF-8") as confjson:
            try:
                tmp_conf = json.loads(confjson.read())
            except json.JSONDecodeError:
                msg = f"Unable to get component attachment for component {self.serial_number} with code {item['code']} as it is not JSON-formatted."
                log.error(msg)
                return {}

            try:
                global_config = tmp_conf[self.chip_type]
            except KeyError:
                log.error(
                    "Chip configuration for %r is not valid. It seems the configuration is for chip type %r.",
                    self.chip_type,
                    next(iter(tmp_conf)),
                )
                sys.exit(1)
            try:
                log.info("Generating chip config for readout at %i MHz.", speed)
                global_config["GlobalConfig"]["CdrClkSel"] = {
                    1280: 0,
                    640: 1,
                    320: 2,
                    160: 3,
                }[speed]
            except KeyError as err:
                log.error(
                    "Readout speed not valid. Possible choices: [1280, 640, 320, 160] MHz. %s",
                    err,
                )
                sys.exit(1)
            return tmp_conf

    def load_wafer_probing_data(self):
        """
        Load chip wafer probing data.
        """
        test_id = None
        tests = pd.DataFrame(self.chip["tests"])
        if len(tests) == 0:
            msg = f"There are no tests in production DB for chip {self.serial_number}!"
            raise RuntimeError(msg)
        if len(tests[tests["code"] == "FECHIP_TEST"]) > 0:
            test_id = tests[tests["code"] == "FECHIP_TEST"]["testRuns"].iloc[-1][-1][
                "id"
            ]
        if not test_id:
            msg = f"There are no wafer probing data in production DB for chip {self.serial_number}!"
            raise RuntimeError(msg)
        self.test_run = TestRun(self.client, test_id)

    def generate_config(
        self,
        chip_template,
        chip_type,
        chip_index,
        layer_config,
        module_type,
        suffix="",
        version="latest",
        speed=1280,
        sensor_vendor=None,
    ):
        """
        Generate chip config.
        """
        try:
            chip_template = {chip_type: chip_template.get("chip_type")}
        except KeyError:
            log.error("Chip template incompatible: no 'chip_type' found!")
            sys.exit(1)

        data_merging = None
        ## warm or warm_4-to-1
        if suffix.count("_") == 1 and "-to-" in suffix:
            _parts = suffix.split("_")
            data_merging = _parts[1]
            suffix = _parts[0]

        if data_merging and data_merging not in ["4-to-1", "2-to-1"]:
            log.error(
                "Data merging mode (%s) unknown, please use '4-to-1' or '2-to-1'.",
                data_merging,
            )
            sys.exit(1)

        if version == "latest" and len(self.attachments) >= 3:
            checklist = [".json", layer_config, suffix]
            for item in self.attachments:
                title = item["title"] or ""
                if all(check in title for check in checklist):
                    log.info(
                        "Latest chip configs found for FE%i (chip %s) %s %s!",
                        chip_index + 1,
                        self.uid,
                        layer_config,
                        suffix,
                    )
                    try:
                        chip_template = self.get_latest_configs(item, speed)
                    except RuntimeError as esnake:
                        log.warning(
                            "Unable to find latest config for FE%i (chip %s): %s. Make sure all sets of configs are present in the database.",
                            chip_index + 1,
                            self.uid,
                            esnake,
                        )
                        continue
                elif not any(check in title for check in checklist):
                    log.warning(
                        "No layer_config %s or suffix %s found in %s",
                        layer_config,
                        suffix,
                        item["title"],
                    )
                else:
                    log.debug(
                        "No layer_config %s or suffix %s found in %s",
                        layer_config,
                        suffix,
                        item["title"],
                    )
                    continue
        elif version == "TESTONWAFER" or len(self.attachments) == 0:
            log.info(
                "Generating chip config for FE%i (chip %s) with %s from wafer probing.",
                chip_index + 1,
                self.uid,
                layer_config,
            )
            power_config = "LP" if suffix == "LP" else layer_config
            try:
                global_config = chip_template[chip_type]
            except KeyError:
                log.error(
                    "Chip configuration for %r is not valid. It seems the configuration is for chip type %r.",
                    chip_type,
                    next(iter(chip_template)),
                )
                sys.exit(1)
            try:
                log.info("Generating chip config for readout at %i MHz.", speed)
                global_config["GlobalConfig"]["CdrClkSel"] = {
                    1280: 0,
                    640: 1,
                    320: 2,
                    160: 4,
                }[speed]
            except KeyError as err:
                log.error(
                    "Readout speed not valid. Possible choices: [1280, 640, 320, 160] MHz. %s",
                    err,
                )
                sys.exit(1)

            if sensor_vendor == 3:  ## HPK
                chip_template[chip_type]["GlobalConfig"]["DiffLcc"] = 200
                chip_template[chip_type]["GlobalConfig"]["DiffLccEn"] = 1

            chip_template[chip_type]["GlobalConfig"]["DiffPreComp"] = {
                "R0": 350,
                "R0.5": 350,
                "L0": 350,
                "L1": 350,
                "L2": 350,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["DiffPreampL"] = {
                "R0": 900,
                "R0.5": 900,
                "L0": 900,
                "L1": 730,
                "L2": 550,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["DiffPreampM"] = {
                "R0": 900,
                "R0.5": 900,
                "L0": 900,
                "L1": 730,
                "L2": 550,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["DiffPreampR"] = {
                "R0": 900,
                "R0.5": 900,
                "L0": 900,
                "L1": 730,
                "L2": 550,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["DiffPreampT"] = {
                "R0": 900,
                "R0.5": 900,
                "L0": 900,
                "L1": 730,
                "L2": 550,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["DiffPreampTL"] = {
                "R0": 900,
                "R0.5": 900,
                "L0": 900,
                "L1": 730,
                "L2": 550,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["DiffPreampTR"] = {
                "R0": 900,
                "R0.5": 900,
                "L0": 900,
                "L1": 730,
                "L2": 550,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["DiffVff"] = {
                "R0": 150,
                "R0.5": 150,
                "L0": 150,
                "L1": 150,
                "L2": 60,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["EnCoreCol0"] = {
                "R0": 65535,
                "R0.5": 65535,
                "L0": 65535,
                "L1": 65535,
                "L2": 65535,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["EnCoreCol1"] = {
                "R0": 65535,
                "R0.5": 65535,
                "L0": 65535,
                "L1": 65535,
                "L2": 65535,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["EnCoreCol2"] = {
                "R0": 65535,
                "R0.5": 65535,
                "L0": 65535,
                "L1": 65535,
                "L2": 65535,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["GlobalConfig"]["EnCoreCol3"] = {
                "R0": 63,
                "R0.5": 63,
                "L0": 63,
                "L1": 63,
                "L2": 63,
                "LP": 0,
            }[power_config]
            chip_template[chip_type]["Parameter"]["Name"] = self.uid

            if module_type == "triplet":
                chip_template[chip_type]["Parameter"]["ChipId"] = chip_index + 1
                chip_template[chip_type]["GlobalConfig"]["AuroraActiveLanes"] = {
                    "R0": 7,
                    "R0.5": 3,
                    "L0": 15,
                }[layer_config]  ## TODO: add source for R0 and R0.5
                # chip_template[chip_type]["GlobalConfig"]["MonitorEnable"] = 0
                # chip_template[chip_type]["GlobalConfig"]["MonitorV"] = 63
                for index in range(4):
                    chip_template[chip_type]["GlobalConfig"][
                        f"DataMergeOutMux{index}"
                    ] = (0 + index) % 4
                chip_template[chip_type]["GlobalConfig"]["SerEnLane"] = {
                    "R0": 7,
                    "R0.5": 3,
                    "L0": 15,
                }[layer_config]
            elif module_type == "quad":
                chip_template[chip_type]["Parameter"]["ChipId"] = 12 + chip_index
                chip_template[chip_type]["GlobalConfig"]["AuroraActiveLanes"] = 1
                for index in range(4):
                    chip_template[chip_type]["GlobalConfig"][
                        f"DataMergeOutMux{index}"
                    ] = ([2, 0, 1, 0][chip_index] + index) % 4
                # Enable all drivers
                chip_template[chip_type]["GlobalConfig"]["SerEnLane"] = [
                    15,
                    15,
                    15,
                    15,
                ][chip_index]
                # Stop datatransmission, end constant 0 on unused links
                for index in range(4):
                    chip_template[chip_type]["GlobalConfig"][f"SerSelOut{index}"] = (
                        1 if ((4 - [2, 0, 1, 0][chip_index]) % 4) == index else 3
                    )

            if not self.test_run:
                try:
                    self.load_wafer_probing_data()
                except RuntimeError as err:
                    log.warning("[red]%s Will generate default config.[/]", err)

            if self.test_run:
                chip_template[chip_type]["GlobalConfig"]["SldoTrimA"] = (
                    self.test_run.get_result("VDDA_TRIM")
                )
                chip_template[chip_type]["GlobalConfig"]["SldoTrimD"] = (
                    self.test_run.get_result("VDDD_TRIM")
                )
                chip_template[chip_type]["Parameter"]["ADCcalPar"][0] = (
                    self.test_run.get_result("ADC_OFFSET") * 1000
                )
                chip_template[chip_type]["Parameter"]["ADCcalPar"][1] = (
                    self.test_run.get_result("ADC_SLOPE") * 1000
                )
                # Check InjCap is actually measured during wafer probing, otherwise leave empty and use default value from chip template
                # In case no InjCap is measured, the value in the PDB is -1*scaling so -1e-15
                # Example here: https://itkpd-test.unicorncollege.cz/testRunView?id=6435cb450ca03e00364c0cae
                _injcap = self.test_run.get_result("InjectionCapacitance") or -1e-15
                if _injcap != -1e-15:
                    chip_template[chip_type]["Parameter"]["InjCap"] = _injcap * (10**15)

                # For transistor sensors calibration, the ideality factor is calculated following the presentation:
                # https://indico.cern.ch/event/1011941/contributions/4278988/attachments/2210633/3741190/RD53B_calibatrion_sensor_temperature.pdf
                e_charge = 1.602e-19
                kB = 1.38064852e-23
                PC_NTC = self.test_run.get_result("PC_NTC") + 273
                DeltaT = 2  # 2 degree difference between PC NTC and transistor sensors
                chip_template[chip_type]["Parameter"]["NfDSLDO"] = (
                    self.test_run.get_result("TEMPERATURE_D")
                    * e_charge
                    / (kB * math.log(15) * (PC_NTC + DeltaT))
                )
                chip_template[chip_type]["Parameter"]["NfASLDO"] = (
                    self.test_run.get_result("TEMPERATURE_A")
                    * e_charge
                    / (kB * math.log(15) * (PC_NTC + DeltaT))
                )
                chip_template[chip_type]["Parameter"]["NfACB"] = (
                    self.test_run.get_result("TEMPERATURE_C")
                    * e_charge
                    / (kB * math.log(15) * (PC_NTC + DeltaT))
                )

                chip_template[chip_type]["Parameter"]["VcalPar"] = [
                    abs(
                        self.test_run.get_result("VCAL_HIGH_LARGE_RANGE_OFFSET") * 1000
                    ),
                    self.test_run.get_result("VCAL_HIGH_LARGE_RANGE_SLOPE") * 1000,
                ]
                chip_template[chip_type]["Parameter"]["IrefTrim"] = (
                    self.target_iref_trim or self.test_run.get_result("IREF_TRIM")
                )

                if not self.target_iref_trim:
                    log.warning(
                        "Chip property 'TARGET_IREF_TRIM' not filled for FE%i, please fix this in the PDB: https://itkpd.unicornuniversity.net/componentView?code=%s. Will resort to using wafer probing data.",
                        chip_index + 1,
                        self.serial_number,
                    )

                ## check that the k-factor from wafer probing is valid (-1 means not present)
                ## e.g. "Current multiplication factor" in https://itkpd.unicornuniversity.net/testRunView?id=65d931cdba853e004269a898
                for chipkey, wpkey in {
                    "KSenseInA": "CURR_MULT_FAC_A",
                    "KSenseInD": "CURR_MULT_FAC_D",
                }.items():
                    _kfactor = self.test_run.get_result(wpkey)
                    if _kfactor > 0:
                        chip_template[chip_type]["Parameter"][chipkey] = _kfactor
                    else:
                        log.warning(
                            "Invalid or missing %s in wafer probing data: %0.2f! Using the default of %i for %s.",
                            wpkey,
                            _kfactor,
                            chip_template[chip_type]["Parameter"][chipkey],
                            chipkey,
                        )

                chip_template[chip_type]["Parameter"]["KSenseShuntA"] = round(
                    chip_template[chip_type]["Parameter"]["KSenseInA"]
                    * self.ratio_kshunt_kin,
                    0,
                )
                chip_template[chip_type]["Parameter"]["KSenseShuntD"] = round(
                    chip_template[chip_type]["Parameter"]["KSenseInD"]
                    * self.ratio_kshunt_kin,
                    0,
                )
                chip_template[chip_type]["Parameter"]["KShuntA"] = (
                    self.test_run.get_result("VINA_SHUNT_KFACTOR")
                )
                chip_template[chip_type]["Parameter"]["KShuntD"] = (
                    self.test_run.get_result("VIND_SHUNT_KFACTOR")
                )
        else:
            msg = f"Not able to generate config for chip {self.uid}. Chip configs might not be complete."
            raise RuntimeError(msg)

        if data_merging and module_type == "quad":
            chip_template[chip_type]["GlobalConfig"]["EnChipId"] = 1
            chip_template[chip_type]["GlobalConfig"]["SerEnLane"] = 15
            chip_template[chip_type]["GlobalConfig"]["ServiceBlockEn"] = 1
            chip_id = chip_template[chip_type]["Parameter"]["ChipId"]
            ## quad chip IDs are 12/13/14/15 for FE1/2/3/4
            ## triplet chip IDs are 1/2/3 for FE1/2/3
            ## chip IDs are defined via wirebonds
            ## FEx are "defined" via silkscreen on the flex
            fe = chip_id % 11
            if data_merging == "4-to-1":
                if chip_id in (12, 13, 14):  ## Secondaries
                    chip_template[chip_type]["GlobalConfig"]["CdrClkSel"] = 2
                    chip_template[chip_type]["GlobalConfig"]["CmlBias0"] = 500
                    chip_template[chip_type]["GlobalConfig"]["CmlBias1"] = 0
                    chip_template[chip_type]["GlobalConfig"]["SerEnTap"] = 0
                    chip_template[chip_type]["GlobalConfig"]["SerInvTap"] = 0
                    log.info(
                        "Setting up FE%i (%s) as secondary for 4-to-1 merging",
                        fe,
                        self.uid,
                    )
                    if chip_id == 12:
                        chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux0"] = 3
                        chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux1"] = 0
                        chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux2"] = 1
                        chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux3"] = 2
                        chip_template[chip_type]["GlobalConfig"]["SerSelOut1"] = 1
                    elif chip_id in (13, 14):  ## // Secondary
                        chip_template[chip_type]["GlobalConfig"]["SerSelOut2"] = 1
                        chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux0"] = 2
                        chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux1"] = 3
                        chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux2"] = 0
                        chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux3"] = 1
                elif chip_id == 15:  ##{ // Primary
                    chip_template[chip_type]["GlobalConfig"]["DataMergeEn"] = 13
                    log.info(
                        "Setting up FE%i (%s) as primary for 4-to-1 merging",
                        fe,
                        self.uid,
                    )
                else:
                    log.error(
                        "Non-standard chip IDs found for FE%i (%s); please check your configs! Chip ID: %i",
                        fe,
                        self.uid,
                        chip_id,
                    )
                    return None
            elif data_merging == "2-to-1":
                if chip_id in (12, 14):  ## // Secondaries
                    chip_template[chip_type]["GlobalConfig"]["CdrClkSel"] = 2
                    chip_template[chip_type]["GlobalConfig"]["CmlBias0"] = 500
                    chip_template[chip_type]["GlobalConfig"]["CmlBias1"] = 0
                    chip_template[chip_type]["GlobalConfig"]["SerSelOut0"] = 1
                    chip_template[chip_type]["GlobalConfig"]["SerSelOut1"] = 1
                    chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux0"] = 1
                    chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux1"] = 0
                    chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux2"] = 2
                    chip_template[chip_type]["GlobalConfig"]["DataMergeOutMux3"] = 3
                    log.info(
                        "Setting up FE%i (%s) as secondary for 2-to-1 merging",
                        fe,
                        self.uid,
                    )
                elif chip_id in (13, 15):  ## // Primary
                    chip_template[chip_type]["GlobalConfig"]["DataMergeEn"] = 0
                    chip_template[chip_type]["GlobalConfig"]["DataMergeEnBond"] = 1
                    log.info(
                        "Setting up FE%i (%s) as primary for 2-to-1 merging",
                        fe,
                        self.uid,
                    )
                else:
                    log.error(
                        "Non-standard chip IDs found for FE%i (%s); please check your configs! Chip ID: %i",
                        fe,
                        self.uid,
                        chip_id,
                    )
                    return None

        return chip_template


class Sensor:
    """
    Sensor class.
    """

    def __init__(self, client, serial_number, no_eos_token=False, module_name=None):
        self.client = client
        self.serial_number = serial_number
        self.module_name = module_name or self.serial_number
        self.sensor = client.get(
            "getComponent",
            json={"component": serial_number, "noEosToken": no_eos_token},
        )
        self.attachments = list(self.sensor["attachments"])
        self.test_run = None

        log.info("sensor %s initiated.", self.serial_number)

        if self.sensor["flags"] is not None and (
            any("BAD" in flag for flag in self.sensor["flags"])
            or any("YELLOW" in flag for flag in self.sensor["flags"])
        ):
            log.warning(
                "This sensor %s might be problematic, please check the production database for more info!",
                self.serial_number,
            )

    def get_vendor(self):
        """
        From the serial number document: https://edms.cern.ch/document/2649105/1
        vendor = key+1
        sensor_vendors = {
        0: "ADVACAM",
        1: "HLL",
        2: "FBK",  ## planar
        3: "HPK",
        4: "LFOUNDRY",
        5: "MICRON",
        6: "CNM",
        7: "FBK",  ## 3D
        8: "SINTEF",
        9: "dummy",
        }
        """
        return int(self.serial_number[-7:-6])


class TestRun:
    """
    TestRun class.
    """

    def __init__(self, client, test_run_id):
        self.client = client
        self.identifier = test_run_id
        self.test_run = client.get("getTestRun", json={"testRun": test_run_id})
        if self.test_run["state"] != "ready":
            log.warning(
                "Wrong test run status! Please check the test run %s on the production database.",
                test_run_id,
            )
        self.results = pd.DataFrame(self.test_run["results"])

        log.info("test run %s initiated.", self.identifier)

    def get_result(self, code):
        """
        Get test run result.
        """
        if len(self.results[self.results["code"] == code]) > 0:
            return self.results[self.results["code"] == code]["value"].iloc[-1]
        return None


class LocalModule:
    """
    LocalModule class. Also works with bare module and FE chip.
    """

    def __init__(
        self,
        localdb: pymongo.database.Database,
        serial_number: str,
        name: str | None = None,
    ):
        self.client: pymongo.MongoClient = localdb.client
        self.localdb = localdb
        self.serial_number = serial_number
        self.name = name if name else self.serial_number
        self.chip_type = get_chip_type_from_serial_number(self.serial_number)
        self.module = self.localdb.component.find_one({"serialNumber": serial_number})
        if not self.module:
            msg = f"Component with serial number {serial_number} not found in your localDB"
            raise RuntimeError(msg)

        self.chips = self.get_chips()

        if len(self.chips) == 1:
            self.module_type = "single"
            log.info("single %s initiated.", self.serial_number)
        elif len(self.chips) == 3:
            self.module_type = "triplet"
            log.info("triplet %s initiated.", self.serial_number)
        else:
            self.module_type = "quad"
            log.info("quad module %s initiated.", self.serial_number)

    def get_chips(self):
        """
        Get list of chips on the module.
        """
        chips = []

        if self.module.get("componentType") == "front-end_chip":
            chips.append(self.module.get("serialNumber"))
        else:
            for cpr in self.localdb.childParentRelation.find(
                {"parent": str(self.module.get("_id"))}
            ):
                child_doc = self.localdb.component.find_one(
                    {"_id": ObjectId(cpr.get("child"))}
                )
                if child_doc.get("componentType") == "front-end_chip":
                    chips.append(child_doc.get("serialNumber"))
        return chips

    def get_current_stage(self):
        """
        Get current stage of the module.
        """
        qc_status = self.localdb.QC.module.status.find_one(
            {"component": str(self.module.get("_id"))}
        )

        current_stage = qc_status.get("stage")
        log.info("current_stage: %s", current_stage)

        return current_stage

    # speed and reverse needed to match the non-localDB module generate_config function
    def generate_config(
        self,
        chip_template,
        layer_config,
        dp_port: DPPort,
        suffix,
        version,
        speed=1280,
        reverse=False,
    ):
        """
        Generate module config.
        """
        log.info(
            "Generating module config for module %s with %s from %s version.",
            self.serial_number,
            layer_config,
            version,
        )
        log.debug(
            "Unused variables: chip template: %s, speed: %i MHz, reverse orientation: %s.",
            chip_template,
            speed,
            reverse,
        )

        config_api = ChipConfigAPI(self.client)

        current_stage = self.get_current_stage()

        configs = {"module": {"chipType": self.chip_type, "chips": []}, "chips": []}

        for chip_index, chip in enumerate(self.chips):
            tx, rx = get_chip_connectivity(
                dp_port, chip_index, self.module_type, reverse
            )

            config_id = config_api.checkout(chip, current_stage, suffix)

            if not config_id:
                msg = f"No {suffix} chip configs were found for FE{chip_index + 1} ({chip}) @ {current_stage}"
                raise RuntimeError(msg)

            config_info = config_api.get_info(config_id)
            if not config_info:
                msg = f"Unable to find configuration information for {config_id} for {suffix} chip configs for FE{chip_index + 1} ({chip}) @ {current_stage}"
                raise RuntimeError(msg)

            current_revision_id = str(config_info.get("current_revision_id"))
            config = config_api.get_config(config_id, current_revision_id, True)
            configs["chips"].append(config)

            # relative path: e.g. L2_warm/0x15499_L2_warm.json
            chip_uid = hex(int(chip[-7:]))

            chip_config_path = (
                Path(f"{layer_config}{'_' + suffix if suffix else ''}")
                / f"{chip_uid}_{layer_config}{'_' + suffix if suffix else ''}.json"
            )

            configs["module"]["chips"].append(
                {
                    "config": str(chip_config_path),
                    "path": "relToCon",
                    "tx": tx,
                    "rx": rx,
                    "enable": 1,
                    "locked": 0,
                }
            )

        return configs
