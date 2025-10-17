#################################
# Author: Arisa Kubota
# Email: arisa.kubota at cern.ch
# Date: July 2019
# Project: Local Database for YARR
#################################

# Common
from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
import pprint
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

import gridfs
from bson.objectid import ObjectId
from pymongo import DESCENDING

from module_qc_database_tools import exceptions
from module_qc_database_tools.yarr.common import readJson

logger = logging.getLogger("Log").getChild("Register")


def get_function_name():
    return traceback.extract_stack(None, 2)[0][2]


home = os.environ["HOME"]
hostname = os.environ.get("HOSTNAME", "default_host")


class RegisterData:
    def __init__(self):
        self.logger = logging.getLogger("Log").getChild("Register")
        # handler = logging.StreamHandler()
        # handler.setLevel(logging.DEBUG)
        # self.logger.setLevel(logging.DEBUG)
        # self.logger.addHandler(handler)
        self.logger.debug(
            "RegisterData.%s: Initialize register function", get_function_name()
        )
        self.dbstatus = False
        self.updated = {}
        self.db_version = 1.01
        self.tr_oids = []

        self.chip_type = None
        self.user_json = {
            "userName": os.environ["USER"],
            "institution": hostname,
            "description": "default",
            "USER": os.environ["USER"],
            "HOSTNAME": hostname,
        }
        self.site_json = {
            "address": ":".join(
                [f"{(uuid.getnode() >> ele) & 0xFF:02x}" for ele in range(0, 8 * 6, 8)][
                    ::-1
                ]
            ),
            "HOSTNAME": hostname,
            "institution": hostname,
        }
        self.conns = []

    def setDb(self, i_cfg, i_localdb, i_toolsdb):
        self.db_cfg = i_cfg
        self.localdb = i_localdb
        self.toolsdb = i_toolsdb
        self.localfs = gridfs.GridFS(self.localdb)

        self.localdb["fs.files"].create_index(
            [("hash", DESCENDING), ("_id", DESCENDING)]
        )
        self.localdb["component"].create_index([("serialNumber", DESCENDING)])
        self.localdb["testRun"].create_index(
            [
                ("startTime", DESCENDING),
                ("user_id", DESCENDING),
                ("address", DESCENDING),
            ]
        )
        self.localdb["componentTestRun"].create_index(
            [("name", DESCENDING), ("testRun", DESCENDING)]
        )
        self.dbstatus = True

        self.db_list = {}
        keys = ["environment"]
        for key in keys:
            self.db_list.update({key: []})
            for value in i_cfg.get(key, []):
                self.db_list[key].append(value.lower().replace(" ", "_"))

    def setUser(self, i_json):
        self.logger.debug("RegisterData.%s: Set User", get_function_name())
        self.user_json.update(i_json)

    def setSite(self, i_json):
        self.logger.debug("RegisterData.%s: Set Site", get_function_name())
        self.site_json.update(i_json)

    def setConnCfg(self, i_conn, i_cache_dir="", conn_dir="."):
        self.logger.debug(
            "RegisterData.%s: Set Connectivity Config", get_function_name()
        )
        if i_conn == {}:
            return i_conn

        # chip type
        self._check_empty(i_conn, "chipType", "connectivity config")
        self.chip_type = i_conn["chipType"]
        if self.chip_type == "FEI4B":
            self.chip_type = "FE-I4B"

        conn = {"module": {}, "chips": []}

        # chips
        for i, chip_json in enumerate(i_conn["chips"]):
            if chip_json.get("enable", 1) == 0:  # disabled chip #TODO
                # only adapting to RD53B case
                cfg_file = chip_json["config"]

                chip_json["hexSN"] = cfg_file[cfg_file.find("0x") :].split("_")[0]
                chip_json["serialNumber"] = "20UPGFC" + str(
                    int(chip_json.get("hexSN"), 16)
                ).zfill(7)

            else:  # enabled chip
                if i_cache_dir != "":
                    chip_json["config"] = chip_json["config"].split("/")[
                        len(chip_json["config"].split("/")) - 1
                    ]
                    path = f"{i_cache_dir}/{chip_json['config']}.before"
                else:
                    path = chip_json["config"]

                if conn_dir != "":
                    path = str(Path(conn_dir) / path)

                chip_cfg_json = readJson(path)
                if self.chip_type not in chip_cfg_json:
                    self.logger.info(
                        "Not found %s in chip config file: %s", self.chip_type, path
                    )
                    # raise exceptions.RegisterError()
                if "name" in chip_cfg_json[self.chip_type]:  # for FEI4B
                    chip_json["name"] = chip_cfg_json[self.chip_type]["name"]
                    chip_json["chipId"] = chip_cfg_json[self.chip_type]["Parameter"][
                        "chipId"
                    ]
                elif "Name" in chip_cfg_json[self.chip_type].get(
                    "Parameter", {}
                ):  # for RD53A
                    chip_json["hexSN"] = chip_cfg_json[self.chip_type]["Parameter"][
                        "Name"
                    ]
                    chip_json["serialNumber"] = "20UPGFC" + str(
                        int(chip_json.get("hexSN"), 16)
                    ).zfill(7)

                else:  # TODO
                    chip_json["name"] = f"UnnamedChip_{i}"
                    chip_json["chipId"] = -1
            chip_json["componentType"] = chip_json.get(
                "componentType", "front-end_chip"
            )
            chip_json["geomId"] = chip_json.get("geomId", i)
            conn["chips"].append(chip_json)

        try:
            self.logger.info(
                "RegisterData.%s: constructing module SN from chips information",
                get_function_name(),
            )
            chip_SNs = [
                chip_json.get("serialNumber") for chip_json in conn.get("chips")
            ]

            module_SNs = []
            stages = []
            for chip_SN in chip_SNs:
                chip_doc = self.localdb.component.find_one({"serialNumber": chip_SN})
                if chip_doc is None:
                    continue
                parents = [
                    cpr.get("parent")
                    for cpr in self.localdb.childParentRelation.find(
                        {"child": str(chip_doc.get("_id"))}
                    )
                ]

                for parent in parents:
                    parent_doc = self.localdb.component.find_one(
                        {"_id": ObjectId(parent), "componentType": "module"}
                    )
                    if parent_doc is not None:
                        module_SNs += [parent_doc.get("serialNumber")]
                        stage_doc = self.localdb.QC.module.status.find_one(
                            {"component": parent}
                        )
                        stages += [stage_doc.get("stage")]

            # self.logger.info( f'chip_SNs = {chip_SNs}' )
            # self.logger.info( f'module_SNs = {module_SNs}' )
            # self.logger.info( f'stages = {stages}' )

            assert module_SNs
            assert all(sn == module_SNs[0] for sn in module_SNs)
            assert all(stage == stages[0] for stage in stages)

            conn["module"] = {"serialNumber": module_SNs[0]}
            conn["stage"] = stages[0]

            if conn["stage"] in ["MODULE/ASSEMBLY", "MODULE/WIREBONDING"]:
                msg = f"The stage of the module {conn['module']['serialNumber']} is still {conn['stage']} and not adequate to push scan results to LocalDB"
                raise Exception(msg)

            parent_doc = self.localdb.component.find_one(
                {"serialNumber": conn.get("module").get("serialNumber")}
            )

            if parent_doc is None:
                msg = f"module doc for {conn.get('module').get('serialNumber')} is somehow missing in LocalDB??"
                raise Exception(msg)

            if parent_doc.get("isConfigGenerated", False) is False:
                msgs = [
                    f"The initial config for the module {conn['module']['serialNumber']} is not generated",
                    "LocalDB cannot store YARR scans at this moment.",
                    "Please generate it first via LocalDB web interface.",
                    "(you are redirected to do this when you switch to the stage MODULE/INITIAL_WARM)",
                ]
                for msg in msgs:
                    self.logger.error(msg)

                msg = "Initial config is not generated"
                raise Exception(msg)

        except Exception:
            self.logger.exception("Unknown exception occurred")
            raise

        self.conns.append(conn)
        return conn

    def _update_sys(self, i_oid, i_col):
        """
        i_col: collection name in localdb
        """

        self.logger.debug(
            "RegisterData.%s: \t\t\tUpdate system information: %s in %s",
            get_function_name(),
            i_oid,
            i_col,
        )
        if i_oid in self.updated.get(i_col, []):
            self.logger.debug(
                "RegisterData.%s: \t\t\t%s is already in in %s",
                get_function_name(),
                i_oid,
                i_col,
            )
            return
        query = {"_id": ObjectId(i_oid), "dbVersion": self.db_version}
        this = self.localdb[i_col].find_one(query)
        now = datetime.now(timezone.utc)
        if not this:
            return
        if this.get("sys", {}) == {}:
            doc_value = {"$set": {"sys": {"cts": now, "mts": now, "rev": 0}}}
        else:
            doc_value = {
                "$set": {
                    "sys": {
                        "cts": this["sys"].get("cts", now),
                        "mts": now,
                        "rev": this["sys"].get("rev", 0) + 1,
                    }
                }
            }
        self.localdb[i_col].update_one(query, doc_value)

        if i_col not in self.updated:
            self.updated.update({i_col: []})
        self.updated[i_col].append(i_oid)

        self.logger.debug("RegisterData.%s: done.", get_function_name())

    def _add_value(self, i_oid, i_col, i_key, i_value, i_type="string"):
        self.logger.debug(
            "RegisterData.%s: \t\t\tAdd document: %s to %s",
            get_function_name(),
            i_key,
            i_col,
        )
        if i_type == "string":
            i_value = str(i_value)
        elif i_type == "bool":
            i_value = i_value.lower() == "true"
        elif i_type == "int":
            i_value = int(i_value)
        query = {"_id": ObjectId(i_oid)}
        doc_value = {"$set": {i_key: i_value}}
        self.localdb[i_col].update_one(query, doc_value)

    def _get_hash(self, i_file_data, i_type="json"):
        self.logger.debug(
            "RegisterData.%s: \t\t\tGet Hash Code from File", get_function_name()
        )
        if i_type == "json":
            shaHashed = hashlib.sha256(
                json.dumps(i_file_data, indent=4).encode("utf-8")
            ).hexdigest()
        elif i_type == "dat":
            with Path(i_file_data).open("rb") as f:
                binary = f.read()
            shaHashed = hashlib.sha256(binary).hexdigest()
        return shaHashed

    def _check_empty(self, i_json, i_key, i_filename):
        self.logger.debug("RegisterData.%s: \tCheck Empty:", get_function_name())
        self.logger.debug("RegisterData.%s: \t- key: %s", get_function_name(), i_key)
        self.logger.debug(
            "RegisterData.%s: \t- file: %s", get_function_name(), i_filename
        )
        if isinstance(i_key, list):
            if not (set(i_key) & set(i_json)):
                self.logger.error(
                    "Found an empty field in json file.\n\tfile: %s  key: %s",
                    i_filename,
                    " or ".join(map(str, i_key)),
                )
                raise exceptions.RegisterError()
        elif i_key not in i_json:
            self.logger.error(
                "Found an empty field in json file.\n\tfile: %s key: %s",
                i_filename,
                i_key,
            )
            raise exceptions.RegisterError()

    def _check_number(self, i_json, i_key, i_filename):
        self.logger.debug("RegisterData.%s: \tCheck Number:", get_function_name())
        self.logger.debug("RegisterData.%s: \t- key: %s", get_function_name(), i_key)
        self.logger.debug(
            "RegisterData.%s: \t- file: %s", get_function_name(), i_filename
        )
        try:
            float(i_json.get(i_key, ""))
        except ValueError as err:
            self.logger.error(
                "This field must be the number.\n\tfile: %s key: %s", i_filename, i_key
            )
            raise exceptions.RegisterError() from err

    def _check_user(self, i_register=True):
        """
        This function checks user data
        If there is a matching data, return oid
        If there is not a matching data, register user_json and return oid
        """
        self.logger.debug("RegisterData.%s: \tCheck User", get_function_name())
        oid = "null"
        query = {
            "userName": os.environ["USER"],
            "institution": hostname,
            "description": "default",
            "USER": os.environ["USER"],
            "HOSTNAME": hostname,
            "dbVersion": self.db_version,
        }
        if self.user_json != {}:
            query.update(self.user_json)
        query["userName"] = query["userName"].lower().replace(" ", "_")
        query["institution"] = query["institution"].lower().replace(" ", "_")
        self.user_json = query
        this_user = self.localdb.user.find_one(query)
        if this_user:
            oid = str(this_user["_id"])
        elif i_register:
            oid = self.__register_user()
        return oid

    def _check_site(self, i_register=True):
        """
        This function checks site data
        If there is a matching data, return oid
        If there is not a matching data, register site_json and return oid
        """
        self.logger.debug("RegisterData.%s: \tCheck Site", get_function_name())
        oid = "null"
        query = {
            "address": ":".join(
                [f"{(uuid.getnode() >> ele) & 0xFF:02x}" for ele in range(0, 8 * 6, 8)][
                    ::-1
                ]
            ),
            "HOSTNAME": hostname,
            "institution": hostname,
            "dbVersion": self.db_version,
        }
        if self.site_json != {}:
            query.update(self.site_json)
        query["institution"] = query["institution"].lower().replace(" ", "_")
        self.site_json = query
        this_site = self.localdb.institution.find_one(query)
        if this_site:
            oid = str(this_site["_id"])
        elif i_register:
            oid = self.__register_site()
        return oid

    def _check_component(self, i_json):
        """
        This function checks component data
        If there is a matching data, return oid
        If there is not a matching data, return '...'
        """
        self.logger.debug(
            "RegisterData.%s: \tCheck Component: query = %s",
            get_function_name(),
            i_json,
        )

        oid = "..."
        if "serialNumber" not in i_json:
            return oid

        query = {"serialNumber": i_json["serialNumber"]}

        this_cmp = self.localdb.component.find_one(query)
        return str(this_cmp["_id"])

    def _get_chip_serial_number(self, hexstr):
        try:
            return "20UPGFC" + str(int(hexstr, 16)).zfill(7)
        except Exception:
            return hexstr

    def _check_child_parent_relation(self, i_mo_oid, i_ch_oid):
        """
        This function checks childParentRelation data
        If there is a matching data, return oid
        If there is not a matching data, return None
        """
        self.logger.debug(
            "RegisterData.%s: \tCheck Child Parent Relation: module doc %s, fe_chip doc %s",
            get_function_name(),
            i_mo_oid,
            i_ch_oid,
        )
        oid = None
        if i_mo_oid != "..." and i_ch_oid != "...":
            query = {
                "parent": i_mo_oid,
                "child": i_ch_oid,
                "status": "active",
                "dbVersion": self.db_version,
            }
            this_cpr = self.localdb.childParentRelation.find_one(query)
            if this_cpr:
                oid = str(this_cpr["_id"])
        return oid

    def _check_chip(self, i_json, i_register=True):
        """
        This function checks chip data
        If there is a matching data, return oid
        If there is not a matching data, register chip data and return oid
        If chip is disabled, return '...'
        """
        self.logger.debug("RegisterData.%s: \tCheck Chip data:", get_function_name())
        oid = "..."
        query = {"serialNumber": i_json["serialNumber"]}

        this_chip = self.localdb.component.find_one(query)

        self.logger.debug(
            "RegisterData._check_chip(): \tFound chip in localdb: ObjectId = %s",
            this_chip["_id"],
        )

        if this_chip:
            oid = str(this_chip["_id"])
        elif i_register:
            oid = self.__register_chip(i_json)
        return oid

    def _check_test_run(self, i_tr_oid="", i_conn=None, i_timestamp=None):
        """
        This function checks test run data
        """

        if i_conn is None:
            i_conn = {}

        def __run_exist(s, i_run):
            s["_id"].append(str(i_run["_id"]))
            s["passed"].append(i_run.get("passed", False))

        self.logger.debug(
            "RegisterData.%s: \tCheck TestRun: i_tr_oid = %s, i_timestamp = %s",
            get_function_name(),
            i_tr_oid,
            i_timestamp,
        )
        status = {"_id": [], "passed": []}
        if i_tr_oid != "" or i_tr_oid is None:
            query = {"_id": ObjectId(i_tr_oid), "dbVersion": self.db_version}
            this_run = self.localdb.testRun.find_one(query)
            if this_run:
                __run_exist(status, this_run)
        elif i_timestamp:
            query = {
                "address": self.site_oid,
                "user_id": self.user_oid,
                "startTime": datetime.utcfromtimestamp(i_timestamp),
                "dbVersion": self.db_version,
            }
            run_entries = self.localdb.testRun.find(query).sort([("$natural", -1)])
            for this_run in run_entries:
                try:
                    if i_conn != {}:
                        chip_ids = []
                        for chip_json in i_conn["chips"]:
                            if chip_json.get("enable", 1) == 0:
                                continue
                            chip_ids.append({"chip": chip_json["chip"]})
                        query = {
                            "testRun": str(this_run["_id"]),
                            "dbVersion": self.db_version,
                            "$or": chip_ids,
                        }
                        ctr_entries = list(self.localdb.componentTestRun.find(query))
                        if len(ctr_entries) != 0:
                            __run_exist(status, this_run)
                            break
                    else:
                        __run_exist(status, this_run)
                except Exception as e:
                    self.logger.warning(str(e))

        return status

    def _check_list(self, i_value, i_name):
        """
        This function checks if the value is listed
        """
        self.logger.debug("RegisterData.%s: \tCheck List:", get_function_name())
        self.logger.debug(
            "RegisterData.%s: \t- value: %s", get_function_name(), i_value
        )
        self.logger.debug("RegisterData.%s: \t- list: %s", get_function_name(), i_name)
        if i_value.lower().replace(" ", "_") not in self.db_list[i_name]:
            self.logger.error(
                "Not found %s in the %s list in database config file.", i_value, i_name
            )
            raise exceptions.RegisterError()

    def _verify_user(self):
        """
        This function verifies user data
        If there is not a matching data, raise ValidationError
        """
        self.logger.debug("RegisterData.%s: \tVerify User", get_function_name())
        self.logger.debug(
            "RegisterData.%s: Loading user information ...", get_function_name()
        )
        self.logger.debug("RegisterData.%s: ~~~ {", get_function_name())
        self.logger.debug(
            'RegisterData.%s: ~~~     "name": "\033[1;33m%s\033[0m",',
            get_function_name(),
            self.user_json["userName"],
        )
        self.logger.debug(
            'RegisterData.%s: ~~~     "institution": "\033[1;33m%s\033[0m"',
            get_function_name(),
            self.user_json["institution"],
        )
        self.logger.debug("RegisterData.%s: ~~~ }}", get_function_name())

    def _verify_site(self):
        """
        This function verifies site data
        If there is not a matching data, raise ValidationError
        """
        self.logger.debug("RegisterData.%s: \tVerify Site", get_function_name())
        self.logger.debug(
            "RegisterData.%s: Loading site information ...", get_function_name()
        )
        self.logger.debug("RegisterData.%s: ~~~ {", get_function_name())
        self.logger.debug(
            'RegisterData.%s: ~~~     "institution": "\033[1;33m%s\033[0m"',
            get_function_name(),
            self.site_json["institution"],
        )
        self.logger.debug("RegisterData.%s: ~~~ }}", get_function_name())

    def __register_user(self):
        """
        This function registers user data
        All the information in self.user_json is registered
        """
        self.logger.debug("RegisterData.%s: \t\tRegister User", get_function_name())
        doc = self.user_json
        doc.update({"sys": {}, "userType": "readWrite", "dbVersion": self.db_version})
        oid = str(self.localdb.user.insert_one(doc).inserted_id)
        self._update_sys(oid, "user")
        self.logger.debug("RegisterData.%s: \t\tdoc   : %s", get_function_name(), oid)
        return oid

    def __register_site(self):
        """
        All the information in self.site_json is registered.
        """
        self.logger.debug("RegisterData.%s: \t\tRegister Site", get_function_name())
        doc = self.site_json
        doc.update({"sys": {}, "dbVersion": self.db_version})
        oid = str(self.localdb.institution.insert_one(doc).inserted_id)
        self._update_sys(oid, "institution")
        self.logger.debug("RegisterData.%s: \t\tdoc   : %s", get_function_name(), oid)
        return oid

    def __register_chip(self, i_json):
        """
        chip data written in i_json is registered.
        """
        self.logger.warning("\t\tRegister Chip")
        doc = {
            "sys": {},
            "name": i_json.get("name", "..."),
            "chipId": i_json.get("chipId", 0),
            "chipType": self.chip_type,
            "componentType": "front-end_chip",
            "dbVersion": self.db_version,
        }
        oid = str(self.localdb.component.insert_one(doc).inserted_id)
        self.logger.warning(
            "\tregistered a custom FE chip as a component in LocalDB: %s", doc
        )
        self._update_sys(oid, "chip")
        self.logger.debug("RegisterData.%s: \t\tdoc   : %s", get_function_name(), oid)
        return oid


class ScanData(RegisterData):
    def __init__(self):
        super().__init__()

    ##########
    # public #
    ##########

    def setTestRun(self, i_log):
        self.logger.debug("RegisterData.%s: Set TestRun", get_function_name())
        # user
        self.user_oid = self._check_user()

        # site
        self.site_oid = self._check_site()

        # connectivity
        self.__check_conn()

        # testRun and componentTestRun
        self.histo_names = []
        for i, conn in enumerate(self.conns):
            status = self._check_test_run("", conn, i_log["startTime"])
            status_id = None
            if status["_id"]:
                status_id = status["_id"][0]
            if status["passed"] and status["passed"][0]:
                msg = "This scan was already registered on LocalDB, skipping."
                raise Exception(msg)

            tr_oid = self.__register_test_run(
                i_log, conn.get("stage", "..."), status_id
            )
            conn["testRun"] = tr_oid
            if "module" in conn:
                self.__check_component_test_run(conn["module"], tr_oid)

            for chip_json in conn["chips"]:
                if "name" in chip_json:
                    chip_json["serialNumber"] = self._get_chip_serial_number(
                        chip_json["name"]
                    )
                self.__check_component_test_run(chip_json, tr_oid)
            self.conns[i] = conn
            query = {"_id": ObjectId(tr_oid)}
            this_run = self.localdb.testRun.find_one(query)
            if this_run and this_run.get("plots", []) != []:
                self.histo_names = this_run["plots"]

        self.logger.debug("RegisterData.%s: done", get_function_name())
        return self.conns

    def completeTestRun(self, i_conns):
        self.logger.debug("RegisterData.%s: Set Test Run (finish)", get_function_name())
        tr_oids = []
        for conn in i_conns:
            tr_oid = conn["testRun"]
            query = {"_id": ObjectId(tr_oid), "dbVersion": self.db_version}
            this_run = self.localdb.testRun.find_one(query)
            doc = {}
            histo_names = list(set(self.histo_names))
            if list(set(this_run["plots"])) != histo_names:
                doc.update({"plots": histo_names})
            if this_run["passed"] is not True:
                doc.update({"passed": True})
            if doc != {}:
                self.localdb.testRun.update_one(
                    {"_id": ObjectId(tr_oid)}, {"$set": doc}
                )
                self._update_sys(tr_oid, "testRun")
            tr_oids.append(tr_oid)
        self.tr_oids = tr_oids

    def setConfig(self, i_config_json, i_filename, i_title, i_col, i_chip_json, i_conn):
        self.logger.debug("RegisterData.%s: Set Config Json", get_function_name())
        if i_config_json == {}:
            return
        oid = self.__check_config(
            i_title, i_col, i_conn["testRun"], i_chip_json.get("chip", "...")
        )
        if oid:
            self.__register_config(i_config_json, i_filename, i_title, i_col, oid)

        return

    def setAttachment(self, i_file_path, i_histo_name, i_chip_json, i_conn):
        def is_dat(b):
            try:
                this = bool("Histo" in b.decode("utf-8").split("\n")[0][0:7])
            except Exception:
                this = False
            return this

        def is_json(b):
            try:
                json_data = json.loads(b.decode("utf-8"))
                return "Histo" in json_data.get("Type", "")
            except Exception:
                return False

        if not Path(i_file_path).is_file():
            self.logger.warning("%s was not identified as a file", i_file_path)
            return

        with Path(i_file_path).open("rb") as f:
            binary_data = f.read()
            if is_dat(binary_data):
                data_type = "dat"
            elif is_json(binary_data):
                data_type = "json"
            else:
                return
        self.histo_names.append(i_histo_name)
        oid = self.__check_attachment(
            i_histo_name, i_conn["testRun"], i_chip_json.get("chip", "..."), data_type
        )
        if oid:
            self.__register_attachment(i_file_path, i_histo_name, oid, data_type)

        return

    def verifyCfg(self):
        self.logger.debug("RegisterData.%s: begin", get_function_name())
        self._verify_user()
        self._verify_site()
        self.__verify_conn_cfg()
        self.logger.debug("RegisterData.%s: done", get_function_name())

    def __verify_conn_cfg(self):
        """
        This function verifies component data
        If there is not a matching data, raise ValidationError
        """
        self.logger.debug("RegisterData.%s: \tVerify Component", get_function_name())
        if self.conns != []:
            self.logger.debug(
                "RegisterData.%s: Loading component information ...",
                get_function_name(),
            )

        # self.logger.info( '__verify_conn_cfg(): self.conns = ' + pprint.pformat( self.conns ) )

        if True:
            conns = self.conns
            self.conns = []
            for conn in conns:
                # module
                if conn["module"] == {}:
                    self.logger.error(
                        "Found an empty field in connectivity config file."
                    )
                    self.logger.error('Please set "module.serialNumber"')
                    raise exceptions.ValidationError()
                mo_oid = self._check_component(conn["module"])
                if mo_oid == "...":
                    self.logger.error(
                        'Not found component data { "serialNumber": "%s", "componentType": "%s" } registered in Local DB.',
                        conn["module"]["serialNumber"],
                        conn["module"]["componentType"],
                    )
                    self.logger.error(
                        "Please set the serial number of the QC parent component correctly in "
                    )
                    self.logger.error(
                        '{ "module": { "serialNumber": "xxx" } } in connectivity file.'
                    )
                    raise exceptions.ValidationError()
                conn["module"]["component"] = mo_oid

                # chips
                chips_json = conn["chips"]
                conn["chips"] = []
                for i, chip_json in enumerate(chips_json):
                    if "serialNumber" not in chip_json and "name" not in chip_json:
                        self.logger.error(
                            "Found an empty field in connectivity config file."
                        )
                        self.logger.error('Please set "chip.%d.serialNumber"', i)
                        raise exceptions.ValidationError()
                    if "serialNumber" not in chip_json:
                        chip_json["serialNumber"] = chip_json["name"]
                    chip_json["name"] = chip_json["serialNumber"]
                    ch_oid = self._check_component(chip_json)
                    if ch_oid == "...":
                        self.logger.error(
                            'Not found component data { "serialNumber": "%s", "componentType": "%s" }} registered in Local DB.',
                            chip_json["serialNumber"],
                            chip_json["componentType"],
                        )
                        self.logger.error(
                            "Please set the serial number of the QC child component correctly in "
                        )
                        self.logger.error(
                            '{{ "serialNumber": "xxx" }} in connectivity file.'
                        )
                        raise exceptions.ValidationError()
                    chip_json["component"] = ch_oid
                    cpr_oid = self._check_child_parent_relation(mo_oid, ch_oid)
                    if not cpr_oid:
                        self.logger.error(
                            'Not found childParentRelation data for { "module": "%s", "FE chip": "%s" } registered in Local DB.',
                            conn["module"]["serialNumber"],
                            self._get_chip_serial_number(chip_json["serialNumber"]),
                        )
                        self.logger.error(
                            "Please check the parent and children are set in the correct relationship."
                        )
                        raise exceptions.ValidationError()
                    chip_json["cpr"] = cpr_oid
                    conn["chips"].append(chip_json)
                # stage -- fetch the stage from LocalDB
                stage = self.__check_stage(mo_oid)
                conn["stage"] = stage
                self.conns.append(conn)
        for conn in self.conns:
            self.logger.debug("RegisterData.%s: ~~~ {", get_function_name())
            if conn["module"] != {}:
                self.logger.debug(
                    'RegisterData.%s: ~~~     "parent": {', get_function_name()
                )
                self.logger.debug(
                    'RegisterData.%s: ~~~         "serialNumber": "\033[1;33m%s\033[0m",',
                    get_function_name(),
                    conn["module"]["serialNumber"],
                )
                self.logger.debug("RegisterData.%s: ~~~     },", get_function_name())

            self.logger.debug(
                'RegisterData.%s: ~~~     "children": [{', get_function_name()
            )

            for i, chip in enumerate(conn["chips"]):
                if i != 0:
                    self.logger.debug(
                        "RegisterData.%s: ~~~     },{", get_function_name()
                    )
                self.logger.debug(
                    'RegisterData.%s: ~~~         "serialNumber": "\033[1;33m%s\033[0m",\033[1;33m%s\033[0m',
                    get_function_name(),
                    chip.get("serialNumber"),
                    " (disabled)" if chip.get("enable", 1) == 0 else "",
                )
                self.logger.debug(
                    'RegisterData.%s: ~~~         "componentType": "\033[1;33m%s\033[0m",',
                    get_function_name(),
                    chip["componentType"],
                )
            self.logger.debug("RegisterData.%s: ~~~     }],", get_function_name())
            self.logger.debug(
                'RegisterData.%s: ~~~     "stage": "\033[1;33m%s\033[0m"',
                get_function_name(),
                conn.get("stage", "..."),
            )
            self.logger.debug("RegisterData.%s: ~~~ }}", get_function_name())
            self.logger.debug("RegisterData.%s: done.", get_function_name())

    def __check_conn(self):
        """
        This function checks connectivity data
        """
        self.logger.debug("RegisterData.__check_conn(): \tCheck Conn")
        conns = self.conns
        self.logger.debug(
            "RegisterData.__check_conn(): input conns = %s", pprint.pformat(conns)
        )

        self.conns = []
        for conn in conns:
            # module
            if conn["module"] != {}:
                if conn["module"].get("component", "...") == "...":
                    mo_oid = self._check_component(conn["module"])
                    conn["module"]["component"] = mo_oid
                if "serialNumber" in conn["module"]:
                    del conn["module"]["serialNumber"]
                if "componentType" in conn["module"]:
                    del conn["module"]["componentType"]
            # chips
            chips_json = conn["chips"]
            conn["chips"] = []
            for _i, chip_json in enumerate(chips_json):
                if conn["module"].get(
                    "component", "..."
                ) != "..." and not chip_json.get("cpr"):
                    ch_oid = self._check_component(chip_json)
                    cpr_oid = self._check_child_parent_relation(mo_oid, ch_oid)
                    chip_json["cpr"] = cpr_oid
                if not chip_json.get("cpr"):
                    conn["module"] = {}
                chip_json["chip"] = self._check_chip(chip_json)
                chip_json["component"] = chip_json["chip"]
                if "serialNumber" in chip_json:
                    del chip_json["serialNumber"]
                if "componentType" in chip_json:
                    del chip_json["componentType"]
                if "chipId" in chip_json:
                    del chip_json["chipId"]
                if "cpr" in chip_json:
                    del chip_json["cpr"]
                conn["chips"].append(chip_json)
            self.conns.append(conn)

        self.logger.debug(
            "RegisterData.__check_conn(): output conns = %s", pprint.pformat(self.conns)
        )

    def __check_stage(self, i_mo_oid):
        """
        This function checks current stage
        If there is a matching data, return stage
        If there is not a matching data, return '...'
        """
        self.logger.debug("RegisterData.%s: \tCheck Stage", get_function_name())
        stage = "..."
        if i_mo_oid:
            query = {"component": i_mo_oid}
            this = self.localdb.QC.module.status.find_one(query)
            if this:
                stage = this["stage"]
        return stage

    def __check_component_test_run(self, i_json, i_tr_oid):
        """
        This function checks test run data
        """
        self.logger.debug(
            "RegisterData.%s: \tCheck Component-TestRun", get_function_name()
        )
        self.logger.debug("RegisterData.%s: i_json = %s", get_function_name(), i_json)

        component_doc = self.localdb.component.find_one(
            {"_id": ObjectId(i_json.get("component"))}
        )

        i_json["name"] = component_doc.get("name")
        i_json["serialNumber"] = component_doc.get("serialNumber")
        i_json["componentType"] = component_doc.get("componentType")

        oid = None
        query = {
            "chip": i_json.get("chip", "module"),
            "component": i_json.get("component", "..."),
            "testRun": i_tr_oid,
            "tx": i_json.get("tx", -1),
            "rx": i_json.get("rx", -1),
            "dbVersion": self.db_version,
        }
        this_ctr = self.localdb.componentTestRun.find_one(query)
        if this_ctr:
            oid = str(this_ctr["_id"])
        else:
            i_json.update(query)
            oid = self.__register_component_test_run(i_json)
        return oid

    def __check_config(self, i_title, i_col, i_tr_oid, i_chip_oid):
        self.logger.debug("RegisterData.%s: \tCheck Config Json:", get_function_name())
        oid = None
        if i_col == "testRun":
            query = {"_id": ObjectId(i_tr_oid), "dbVersion": self.db_version}
        elif i_col == "componentTestRun":
            query = {
                "testRun": i_tr_oid,
                "chip": i_chip_oid,
                "dbVersion": self.db_version,
            }
        this = self.localdb[i_col].find_one(query)
        if this.get(i_title, "...") == "...":
            oid = str(this["_id"])

        return oid

    def __check_attachment(self, i_histo_name, i_tr_oid, i_chip_oid, i_type):
        self.logger.debug("RegisterData.%s: \tCheck Attachment:", get_function_name())
        oid = None
        query = {"testRun": i_tr_oid, "chip": i_chip_oid, "dbVersion": self.db_version}
        this_ctr = self.localdb.componentTestRun.find_one(query)
        filenames = []
        for attachment in this_ctr.get("attachments", []):
            filenames.append(attachment["filename"])
        if f"{i_histo_name}.{i_type}" not in filenames:
            oid = str(this_ctr["_id"])
        return oid

    def __check_gridfs(self, i_hash_code):
        self.logger.debug(
            "RegisterData.%s: \t\t\tCheck Json File by Hash", get_function_name()
        )
        oid = None
        query = {"hash": i_hash_code, "dbVersion": self.db_version}
        this_file = self.localdb.fs.files.find_one(query, {"_id": 1})
        if this_file:
            oid = str(this_file["_id"])
        return oid

    def __register_test_run(self, i_json, i_stage, i_tr_oid):
        """
        Almost all the information in i_json is registered.
        """
        self.logger.debug("RegisterData.%s: \t\tRegister Test Run", get_function_name())
        doc = {}
        for key in i_json:
            if (
                key not in {"connectivity", "startTime", "finishTime"}
                and "Cfg" not in key
            ):
                doc[key] = i_json[key]
        doc.update(
            {
                "testType": i_json.get("testType", "..."),
                "runNumber": i_json.get("runNumber", -1),
                "stage": i_stage,
                "chipType": self.chip_type,
                "address": self.site_oid,
                "user_id": self.user_oid,
                "dbVersion": self.db_version,
            }
        )
        if not i_tr_oid:
            doc.update(
                {
                    "sys": {},
                    "environment": False,
                    "plots": [],
                    "passed": False,
                    "startTime": datetime.utcfromtimestamp(i_json["startTime"]),
                    "finishTime": datetime.utcfromtimestamp(i_json["finishTime"]),
                }
            )
            oid = str(self.localdb.testRun.insert_one(doc).inserted_id)

            now = datetime.now(timezone.utc)

            self.logger.info(
                "RegisterData.%s: \t\tAdding tags to TestRun. Tags = %s",
                get_function_name(),
                self.tags,
            )

            for tag in self.tags:
                if not self.toolsdb.viewer.tag.categories.find_one({"name": tag}):
                    self.toolsdb.viewer.tag.categories.insert_one(
                        {
                            "name": tag,
                            "class": "scan",
                            "sys": {"cts": now, "mts": now, "rev": 0},
                        }
                    )

                if not self.toolsdb.viewer.tag.docs.find_one(
                    {"runId": str(oid), "name": tag}
                ):
                    self.toolsdb.viewer.tag.docs.insert_one(
                        {
                            "runId": str(oid),
                            "name": tag,
                            "sys": {"cts": now, "mts": now, "rev": 0},
                        }
                    )
                    self.logger.info(
                        "RegisterData.%s: \t\tAdded a new tag %s to TestRun.",
                        get_function_name(),
                        tag,
                    )

        else:
            self.logger.info(
                "RegisterData.%s: \t\tnon-blank i_tr_oid = %s.",
                get_function_name(),
                i_tr_oid,
            )
            oid = i_tr_oid
            query = {"_id": ObjectId(i_tr_oid)}
            self.localdb.testRun.update_one(query, {"$set": doc})

        self.logger.debug(
            "RegisterData.%s: \t\tupdating sys for oid = %s...",
            get_function_name(),
            oid,
        )
        self._update_sys(oid, "testRun")
        self.logger.debug("RegisterData.%s: \t\tdoc   : %s", get_function_name(), oid)
        return oid

    def __register_component_test_run(self, i_json):
        """
        Almost all the information in i_json is registered.
        """
        self.logger.debug(
            "RegisterData.%s: \t\tRegister Component-TestRun", get_function_name()
        )
        doc = i_json
        doc.update(
            {
                "sys": {},
                "attachments": [],
                "environment": "...",
                "dbVersion": self.db_version,
            }
        )
        oid = str(self.localdb.componentTestRun.insert_one(doc).inserted_id)
        self._update_sys(oid, "componentTestRun")
        self.logger.debug("RegisterData.%s: \t\tdoc   : %s", get_function_name(), oid)
        return oid

    def __register_config(self, i_file_json, i_filename, i_title, i_col, i_oid):
        self.logger.debug(
            'RegisterData.%s: \t\tRegister Config Json: i_filename="%s", i_title="%s", i_col = "%s", i_oid="%s"',
            get_function_name(),
            i_filename,
            i_title,
            i_col,
            i_oid,
        )

        data = pickle.dumps(i_file_json)
        hash_code = hashlib.md5(data).hexdigest()
        self.logger.debug(
            "RegisterData.%s: \t\thash_code = %s", get_function_name(), hash_code
        )

        data_id = self.__check_gridfs(hash_code)
        self.logger.debug(
            "RegisterData.%s: \t\tdata_id = %s", get_function_name(), data_id
        )

        if not data_id:
            data_id = self.__register_grid_fs_file(
                data, None, i_filename + ".pickle", hash_code
            )

        doc = {
            "sys": {},
            "filename": i_filename + ".pickle",
            "chipType": self.chip_type,
            "title": i_title,
            "format": "fs.files",
            "data_id": data_id,
            "dbVersion": self.db_version,
        }
        oid = str(self.localdb.config.insert_one(doc).inserted_id)
        self._update_sys(oid, "config")
        self._add_value(i_oid, i_col, i_title, oid)
        self._update_sys(i_oid, i_col)
        self.logger.debug("RegisterData.%s: \t\tdoc   : %s", get_function_name(), i_oid)
        self.logger.debug("RegisterData.%s: \t\tconfig: %s", get_function_name(), oid)
        self.logger.debug(
            "RegisterData.%s: \t\tdata  : %s", get_function_name(), data_id
        )
        return oid

    def __register_attachment(self, i_file_path, i_histo_name, i_oid, i_type):
        self.logger.debug(
            'RegisterData.%s: \t\tRegister Attachment: i_file_path="%s", i_histo_name="%s", i_oid="%s", i_type="%s"',
            get_function_name(),
            i_file_path,
            i_histo_name,
            i_oid,
            i_type,
        )
        if i_type == "json":
            with Path(i_file_path).open("rb") as f:
                binary_data = f.read()
                json_data = json.loads(binary_data.decode("utf-8"))
                pickle_data = pickle.dumps(json_data)
                i_type = "pickle"
            hash_code = hashlib.md5(pickle_data).hexdigest()
            oid = self.__check_gridfs(hash_code)
            if not oid:
                oid = self.__register_grid_fs_file(
                    pickle_data, None, f"{i_histo_name}.{i_type}", hash_code
                )
        else:
            hash_code = self._get_hash(i_file_path)
            oid = self.__check_gridfs(hash_code)
            if not oid:
                oid = self.__register_grid_fs_file(
                    None, i_file_path, f"{i_histo_name}.{i_type}", None
                )
        self.localdb.componentTestRun.update_one(
            {"_id": ObjectId(i_oid)},
            {
                "$push": {
                    "attachments": {
                        "code": oid,
                        "dateTime": datetime.now(timezone.utc),
                        "title": i_histo_name,
                        "description": "describe",
                        "contentType": i_type,
                        "filename": f"{i_histo_name}.{i_type}",
                    }
                }
            },
        )
        self._update_sys(i_oid, "componentTestRun")
        self.logger.debug("RegisterData.%s: \t\tdoc   : %s", get_function_name(), i_oid)
        self.logger.debug("RegisterData.%s: \t\tdata  : %s", get_function_name(), oid)
        return oid

    def __register_grid_fs_file(self, data, i_file_path, i_filename, i_hash):
        self.logger.debug(
            'RegisterData.%s: \t\t\tWrite File by GridFS: i_file_path = "%s", i_filename="%s", i_hash="%s"',
            get_function_name(),
            i_file_path,
            i_filename,
            i_hash,
        )

        if data is None:
            with Path(i_file_path, "rb").open() as f:
                binary = f.read()
        else:
            binary = data

        md5 = hashlib.md5(binary).hexdigest()

        duplicated = self.localdb.fs.files.find_one({"md5": md5})

        if duplicated:
            duplicated_oid = str(duplicated.get("_id"))
            self.logger.info(
                "RegisterData.%s: \t\t\tIdentical data was found on gidfs, not submitting. Reusing oid = %s",
                get_function_name(),
                duplicated_oid,
            )
            self._update_sys(duplicated_oid, "fs.files")
            return duplicated_oid

        oid = str(
            self.localfs.put(binary, filename=i_filename, dbVersion=self.db_version)
        )
        self._update_sys(oid, "fs.files")

        self.logger.info(
            "RegisterData.%s: \t\t\tSubmitted the data to gridfs. oid = %s",
            get_function_name(),
            oid,
        )

        return oid


class DcsData(RegisterData):
    def __init__(self):
        super().__init__()
        self.ctr_oids = []

    def verifyCfg(self, i_log):
        self.__verify_dcs_log_format(i_log)
        self.__verify_test_data(i_log)

    def __verify_dcs_log_format(self, i_log):
        """
        This function verifies DCS log file
        If the format is unreadable, raise RegisterError
        """
        self.logger.debug("RegisterData.%s: \tVerify DCS Log", get_function_name())
        for i, env_j in enumerate(i_log["environments"]):
            filename = f"environments.{i} in DCS log file"
            self._check_empty(env_j, "status", filename)
            if env_j["status"] != "enabled":
                continue
            self._check_empty(env_j, "key", filename)
            self._check_list(env_j["key"], "environment")
            self._check_empty(env_j, "description", filename)
            self._check_empty(env_j, "num", filename)
            self._check_number(env_j, "num", filename)
            self._check_empty(env_j, ["path", "value"], filename)
            if "path" in env_j:
                try:
                    self.__read_dcs_data(env_j["path"], env_j["key"], env_j["num"])
                except Exception as err:
                    raise exceptions.RegisterError() from err
                if "margin" in env_j:
                    self._check_number(env_j, "margin", filename)

    def __verify_test_data(self, i_log):
        """
        This function verifies scan data
        If the data is not registered, raise ValidationError
        """
        self.user_oid = self._check_user(False)
        self.site_oid = self._check_site(False)
        self.__check_conn()
        tr_oids = []
        if self.conns == []:
            self.conns = [{}]
        for conn in self.conns:
            status = self._check_test_run(i_log.get("id", ""), conn, i_log["timestamp"])
            for i, tr_oid in enumerate(status["_id"]):
                if status["passed"][i]:
                    tr_oids.append(tr_oid)
        if tr_oids == []:
            self.logger.error("Not found relational test run data in DB")
            self.logger.error("The scan data may not have been uploaded.")
            self.logger.error(
                "Please make sure it is uploaded and try to upload DCS data again."
            )
            raise exceptions.ValidationError()
        self.dcs_tr_oids = tr_oids

    def verifyDcsData(self, i_env):
        """
        This function verifies DCS data associated to scan data
        If the data is already registered, return warning
        """
        ctr_oids = []
        registered_oids = []
        chips = []
        registered_chips = []
        if i_env["status"] == "enabled":
            env_key = i_env["key"].lower().replace(" ", "_")
            for tr_oid in self.dcs_tr_oids:
                query = {"testRun": tr_oid, "dbVersion": self.db_version}
                if i_env.get("chip", None):
                    query.update({"name": i_env["chip"]})
                ctr_entries = self.localdb.componentTestRun.find(query)
                for this_ctr in ctr_entries:
                    ctr_oid = self._check_dcs(
                        str(this_ctr["_id"]),
                        env_key,
                        i_env["num"],
                        i_env["description"],
                    )
                    if ctr_oid:
                        registered_oids.append(str(this_ctr["_id"]))
                        registered_chips.append('"\033[1;33m{this_ctr["name"]}\033[0m"')
                    else:
                        ctr_oids.append(str(this_ctr["_id"]))
                        chips.append('\033[1;33m"{this_ctr["name"]}"\033[0m')
        i_env.update(
            {
                "registered_oids": registered_oids,
                "ctr_oids": ctr_oids,
                "chips": chips,
                "registered_chips": registered_chips,
            }
        )
        return i_env

    def confirmDcsData(self, i_env):
        """
        This function display DCS configuration
        """
        self.logger.debug("RegisterData.%s: ~~~ {", get_function_name())
        self.logger.debug(
            'RegisterData.%s: ~~~     "key": "\033[1;33m%s\033[0m",',
            get_function_name(),
            i_env["key"],
        )
        self.logger.debug(
            'RegisterData.%s: ~~~     "description": "\033[1;33m%s\033[0m",',
            get_function_name(),
            i_env["description"],
        )
        self.logger.debug(
            'RegisterData.%s: ~~~     "num": "\033[1;33m%s\033[0m",',
            get_function_name(),
            i_env["num"],
        )
        if "path" in i_env:
            self.logger.debug(
                'RegisterData.%s: ~~~     "path": "\033[1;33m%s\033[0m",',
                get_function_name(),
                i_env["path"],
            )
            if "margin" in i_env:
                self.logger.debug(
                    'RegisterData.%s: ~~~     "margin": "\033[1;33m%s\033[0m",',
                    get_function_name(),
                    i_env["margin"],
                )
        elif "value" in i_env:
            self.logger.debug(
                'RegisterData.%s: ~~~     "value": "\033[1;33m%s\033[0m",',
                get_function_name(),
                i_env["value"],
            )
        if i_env.get("chips", []) != []:
            self.logger.debug(
                'RegisterData.%s: ~~~     "chips": %s',
                get_function_name(),
                ", ".join(i_env["chips"]),
            )
        if i_env.get("registered_chips", []) != []:
            self.logger.debug(
                'RegisterData.%s: ~~~     "\033[1;31mchips with registered DCS data\033[0m": %s',
                get_function_name(),
                ", ".join(i_env["registered_chips"]),
            )
        self.logger.debug("RegisterData.%s: ~~~ }}", get_function_name())

    def setDcs(self):
        self.logger.debug("RegisterData.%s: \t\tSet DCS", get_function_name())
        environments = self.environments
        for env_j in environments:
            env_key = env_j["key"].lower().replace(" ", "_")
            ctr_oids = env_j.get("registered_oids", [])
            for ctr_oid in ctr_oids:
                self.ctr_oids.append(
                    {
                        "ctr_oid": ctr_oid,
                        "key": env_key,
                        "num": env_j["num"],
                        "description": env_j["description"],
                    }
                )
            ctr_oids = env_j.get("ctr_oids", [])
            if "ctr_oids" in env_j:
                del env_j["ctr_oids"]
            if "registered_oids" in env_j:
                del env_j["registered_oids"]
            if "chips" in env_j:
                del env_j["chips"]
            if "registered_chips" in env_j:
                del env_j["registered_chips"]
            for ctr_oid in ctr_oids:
                self.__register_dcs(ctr_oid, env_key, env_j)
                self.ctr_oids.append(
                    {
                        "ctr_oid": ctr_oid,
                        "key": env_key,
                        "num": env_j["num"],
                        "description": env_j["description"],
                    }
                )

    def __check_conn(self):
        """
        This function checks connectivity data
        """
        self.logger.debug("RegisterData.%s: \tCheck Conn", get_function_name())
        conns = self.conns
        self.conns = []
        for conn in conns:
            # chips
            chips_json = conn["chips"]
            conn["chips"] = []
            for _i, chip_json in enumerate(chips_json):
                chip_oid = self._check_chip(chip_json, False)
                chip_json["chip"] = chip_oid
                conn["chips"].append(chip_json)
            self.conns.append(conn)

    def _check_dcs(self, i_ctr_oid, i_key, i_num, i_description):
        self.logger.debug("RegisterData.%s: \tCheck DCS", get_function_name())
        ctr_oid = None
        query = {"_id": ObjectId(i_ctr_oid), "dbVersion": self.db_version}
        this_ctr = self.localdb.componentTestRun.find_one(query)
        if this_ctr.get("environment", "...") != "...":
            query = {
                "_id": ObjectId(this_ctr["environment"]),
                "dbVersion": self.db_version,
            }
            this_dcs = self.localdb.environment.find_one(query)
            for this_data in this_dcs.get(i_key, []):
                if (
                    str(this_data["num"]) == str(i_num)
                    and this_data["description"] == i_description
                ):
                    ctr_oid = i_ctr_oid
                    break
        return ctr_oid

    def __register_dcs(self, i_ctr_oid, i_env_key, i_env_j):
        self.logger.debug("RegisterData.%s: \t\tRegister DCS", get_function_name())
        query = {"_id": ObjectId(i_ctr_oid), "dbVersion": self.db_version}
        this_ctr = self.localdb.componentTestRun.find_one(query)
        tr_oid = this_ctr["testRun"]
        query = {"_id": ObjectId(tr_oid), "dbVersion": self.db_version}
        this_tr = self.localdb.testRun.find_one(query)
        array = []
        if i_env_j.get("path", "null") != "null":
            starttime = None
            finishtime = None
            if "margin" in i_env_j:
                starttime = this_tr["startTime"].timestamp() - i_env_j["margin"]
                finishtime = this_tr["finishTime"].timestamp() + i_env_j["margin"]
            try:
                array = self.__read_dcs_data(
                    i_env_j["path"], i_env_key, i_env_j["num"], starttime, finishtime
                )
            except exceptions.DcsDataError:
                return
        else:
            array.append({"date": this_tr["startTime"], "value": i_env_j["value"]})
        i_env_j.update({"data": array})
        if this_ctr.get("environment", "...") == "...":
            doc_value = {"sys": {}, i_env_key: [i_env_j], "dbVersion": self.db_version}
            oid = str(self.localdb.environment.insert_one(doc_value).inserted_id)
            self._add_value(i_ctr_oid, "componentTestRun", "environment", oid)
            self._update_sys(i_ctr_oid, "componentTestRun")
        else:
            oid = this_ctr["environment"]
            doc_value = {"$push": {i_env_key: i_env_j}}
            query = {"_id": ObjectId(oid)}
            self.localdb.environment.update_one(query, doc_value)

        self._update_sys(oid, "environment")
        self._add_value(tr_oid, "testRun", "environment", True)
        self._update_sys(tr_oid, "testRun")
        self.tr_oids.append(tr_oid)

    def __read_dcs_data(self, i_path, i_key, i_num, i_start=None, i_finish=None):
        self.logger.debug("RegisterData.%s: \t\tRead DCS data", get_function_name())
        env_key = i_key.lower().replace(" ", "_")
        extension = i_path.split(".")[len(i_path.split(".")) - 1]
        if extension == "dat":
            separator = " "
        elif extension == "csv":
            separator = ","
        else:
            self.logger.error("No supported DCS data.")
            self.logger.error("\tfile: %s  extension: %s", i_path, extension)
            self.logger.error('\tSet to "dat" or "csv".')
            raise exceptions.DcsDataError()
        if not Path(i_path).is_file():
            self.logger.error("Not found DCS data file.")
            self.logger.error("\tfile: %s", i_path)
            raise exceptions.DcsDataError()

        with Path(i_path).open() as data:
            # key and num
            key_lines = data.readline().splitlines()
            if not key_lines:
                self.logger.error("Not found DCS keys in the 1st line.")
                self.logger.error("\tfile: %s", i_path)
                raise exceptions.DcsDataError()

            num_lines = data.readline().splitlines()
            if not num_lines:
                self.logger.error("Not found DCS nums in the 2nd line.")
                self.logger.error("\tfile: %s", i_path)
                raise exceptions.DcsDataError()

            setting_lines = data.readline().splitlines()
            if not setting_lines:
                self.logger.error("Not found DCS nums in the 3rd line.")
                self.logger.error("\tfile: %s", i_path)
                raise exceptions.DcsDataError()

            key = -1
            for j, tmp_key in enumerate(key_lines[0].split(separator)):
                tmp_num = num_lines[0].split(separator)[j]
                if str(env_key) == str(tmp_key.lower().replace(" ", "_")) and str(
                    i_num
                ) == str(tmp_num):
                    key = j
                    break
            if key == -1:
                self.logger.error("Not found specified DCS data.")
                self.logger.error("\tfile: %s", i_path)
                self.logger.error("\tkey: %s  num: %s", env_key, i_num)
                self.logger.error(
                    "Please check the key and num given in the DCS config file are set in the DCS data file."
                )
                raise exceptions.DcsDataError()

            # value
            env_lines = data.readline().splitlines()
            if not env_lines:
                self.logger.error("Not found DCS values from the 4th line.")
                self.logger.error("\tfile: %s", i_path)
                raise exceptions.DcsDataError()

            array = []
            line_i = 3
            while env_lines:
                if len(env_lines[0].split(separator)) < key:
                    break
                try:
                    date = int(env_lines[0].split(separator)[1])
                except Exception as err:
                    self.logger.error(
                        'Invalid value: Unixtime must be "int".\n\tfile: %s  line: %s  text: %s',
                        i_path,
                        line_i,
                        data,
                    )
                    raise exceptions.DcsDataError() from err
                value = env_lines[0].split(separator)[key]
                if value != "null":
                    try:
                        value = float(value)
                    except Exception as err:
                        self.logger.error(
                            'Invalid value: DCS data must be "float" or "null".\tfile: %s  line: %s  text: %s',
                            i_path,
                            line_i,
                            data,
                        )
                        raise exceptions.DcsDataError() from err
                    if (i_start and date < i_start) or (i_finish and data > i_finish):
                        pass
                    else:
                        array.append(
                            {"date": datetime.utcfromtimestamp(date), "value": value}
                        )
                env_lines = data.readline().splitlines()
                line_i = line_i + 1
            return array


class CompData(RegisterData):
    def __init__(self):
        super().__init__()

    def verifyCfg(self):
        self._verify_user()
        self._verify_site()

    def checkConnCfg(self, i_path):
        """
        Check Component Connectivity
        If the components written in the file have not registered,
        Display component information in the console
        """
        self.logger.debug(
            "RegisterData.%s: \tCheck Connectivity config for registration:",
            get_function_name(),
        )
        conn = readJson(i_path)
        self._check_empty(conn, "chipType", "connectivity config")
        if conn["chipType"] == "FEI4B":
            conn["chipType"] = "FE-I4B"
        self.chip_type = conn["chipType"]

        # module
        if "module" in conn:
            self._check_empty(conn["module"], "serialNumber", "connectivity.module")
            conn["module"]["componentType"] = conn["module"].get(
                "componentType", "module"
            )
            conn["module"]["status"] = self.__check_component(conn["module"])
            if conn["module"]["status"] == 2:
                self.logger.error(
                    "Already registered QC component data: %s (%s)",
                    conn["module"]["serialNumber"],
                    conn["module"]["componentType"],
                )
                self.logger.error("QC components cannot be registered by overwriting.")
                raise exceptions.RegisterError()
        # chip
        chips = []
        chipids = []
        for i, chip_conn in enumerate(conn["chips"]):
            self._check_empty(chip_conn, "serialNumber", f"connectivity.chips.{i}")
            self._check_empty(chip_conn, "chipId", f"connectivity.chips.{i}")
            chip_conn["componentType"] = chip_conn.get(
                "componentType", "front-end_chip"
            )
            if chip_conn["chipId"] in chipids:
                self.logger.error("Conflict chip ID: %s", chip_conn["chipId"])
                raise exceptions.RegisterError()
            chipids.append(chip_conn["chipId"])
            chip_conn["status"] = self.__check_component(chip_conn)
            if chip_conn["status"] == 2:
                self.logger.error(
                    "Already registered QC component data: %s (%s)",
                    chip_conn["serialNumber"],
                    chip_conn["componentType"],
                )
                self.logger.error("QC components cannot be registered by overwriting.")
                raise exceptions.RegisterError()
            chips.append(chip_conn)
        conn["chips"] = chips
        if "module" in conn:
            conn["module"]["children"] = len(chips)

        self.logger.debug("RegisterData.%s: Component Data:", get_function_name())
        self.logger.debug(
            "RegisterData.%s:     Chip Type: \033[1;33m%s\033[0m",
            get_function_name(),
            conn["chipType"],
        )
        if "module" in conn:
            self.logger.debug("RegisterData.%s:     Module:", get_function_name())
            self.logger.debug(
                "RegisterData.%s:         serial number: \033[1;33m%s\033[0m %s",
                get_function_name(),
                conn["module"]["serialNumber"],
                "\033[1;31m(data already registered in Local DB)\033[0m"
                if conn["module"]["status"] == 1
                else "",
            )
            self.logger.debug(
                "RegisterData.%s:         component type: \033[1;33m%s\033[0m",
                get_function_name(),
                conn["module"]["componentType"],
            )
            self.logger.debug(
                "RegisterData.%s:         # of chips: \033[1;33m%s\033[0m",
                get_function_name(),
                conn["module"]["children"],
            )
        for i, chip in enumerate(conn["chips"]):
            self.logger.debug(
                "RegisterData.%s:     Chip (%d):", get_function_name(), i + 1
            )
            self.logger.debug(
                "RegisterData.%s:         serial number: \033[1;33m%s\033[0m %s",
                get_function_name(),
                chip["serialNumber"],
                "\033[1;31m(data already registered in Local DB)\033[0m"
                if chip["status"] == 1
                else "",
            )
            self.logger.debug(
                "RegisterData.%s:         component type: \033[1;33m%s\033[0m",
                get_function_name(),
                chip["componentType"],
            )
            self.logger.debug(
                "RegisterData.%s:         chip ID: \033[1;33m%s\033[0m",
                get_function_name(),
                chip["chipId"],
            )

        self.logger.warning(
            "It will be override with the provided information if data already exists in Local DB."
        )
        self.conn = conn

    def setComponent(self):
        """
        [deprecated] This function registers component information from cnnectivity file
        """

        return

    def __check_component(self, i_json):
        """
        This function checks component data
        """
        self.logger.debug("RegisterData.%s: \tCheck Component", get_function_name())
        result = 0
        if i_json != {} and "serialNumber" in i_json and "componentType" in i_json:
            query = {
                "serialNumber": i_json["serialNumber"],
                "componentType": i_json["componentType"].lower().replace(" ", "_"),
                "chipType": self.chip_type,
                "dbVersion": self.db_version,
            }
            this_cmp = self.localdb.component.find_one(query)
            if not this_cmp:
                result = 0
            elif this_cmp.get("proDB", False):
                result = 2
            else:
                result = 1

        return result

    def __register_component(self, i_json, i_oid):
        """
        This function registers Component
        Almost all the information in i_json is registered.
        """
        self.logger.debug(
            "RegisterData.%s: \t\tRegister Component", get_function_name()
        )
        doc = {
            "serialNumber": i_json["serialNumber"],
            "componentType": i_json["componentType"].lower().replace(" ", "_"),
            "chipType": self.chip_type,
            "name": i_json["serialNumber"],
            "chipId": i_json.get("chipId", -1),
            "children": i_json.get("children", -1),
            "proDB": False,
            "dbVersion": self.db_version,
        }
        if i_oid == "...":
            doc.update({"sys": {}, "address": self.site_oid, "user_id": self.user_oid})
            oid = str(self.localdb.component.insert_one(doc).inserted_id)
        else:
            oid = i_oid
            query = {"_id": ObjectId(oid)}
            self.localdb.component.update_one(query, {"$set": doc})
        self._update_sys(oid, "component")
        logger.info("RegisterData.%s: \t\tdoc   : %s", get_function_name(), oid)
        return oid

    def __register_child_parent_relation(
        self, i_parent_oid, i_child_oid, i_chip_id, i_geom_id, i_oid, i_active=True
    ):
        """
        This function registers ChildParentRelation
        """
        self.logger.debug(
            "RegisterData.%s: \t\tRegister Child Parent Relation.", get_function_name()
        )
        doc = {
            "parent": i_parent_oid,
            "child": i_child_oid,
            "chipId": i_chip_id,
            "geomId": i_geom_id,
            "status": "active" if i_active else "dead",
            "dbVersion": self.db_version,
        }
        if not i_oid:
            doc.update({"sys": {}})
            oid = str(self.localdb.childParentRelation.insert_one(doc).inserted_id)
        else:
            oid = i_oid
            query = {"_id": ObjectId(oid)}
            self.localdb.childParentRelation.update_one(query, {"$set": doc})
        self._update_sys(oid, "childParentRelation")
        self.logger.debug("RegisterData.%s: \t\tdoc   : %s", get_function_name(), oid)
        return oid
