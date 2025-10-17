#################################
# Author: Arisa Kubota
# Email: arisa.kubota at cern.ch
# Date: July 2019
# Project: Local Database for YARR
#################################

# Common
from __future__ import annotations

import json
import sys
from datetime import timezone

# log
from logging import getLogger
from pathlib import Path

import gridfs
from bson.objectid import ObjectId
from pymongo import DESCENDING
from tzlocal import get_localzone

logger = getLogger("Log").getChild("sub")
db_version = 1.01

localdb = None
toolsdb = None


###########################
### Set timestamp to string
def setTime(date):
    local_tz = get_localzone()
    converted_time = date.replace(tzinfo=timezone.utc).astimezone(local_tz)
    return converted_time.strftime("%Y/%m/%d %H:%M:%S")


##################################
### Get data document from data_id
def getData(i_type, i_dir, i_filename, i_data, i_bool=False):
    if i_bool:
        data = i_data
    elif i_type == "json":
        fs = gridfs.GridFS(localdb)
        data = json.loads(fs.get(ObjectId(i_data)).read().decode("ascii"))
    else:
        fs = gridfs.GridFS(localdb)
        data = fs.get(ObjectId(i_data)).read().decode("ascii")
    return {"type": i_type, "path": f"{i_dir}/{i_filename}", "data": data}


################
### File to Json
### exist: return {json}
### not exist: return {}
### not json file: error
def toJson(i_file_path):
    logger.debug("\t\t\tConvert to json code from: %s", i_file_path)

    file_json = {}
    if i_file_path and Path(i_file_path).is_file():
        try:
            with Path(i_file_path).open() as f:
                file_json = json.load(f)
        except ValueError:
            logger.exception("Could not parse %s", i_file_path)
            sys.exit(1)

    return file_json


#########################
### Display test data log
### Searchable by
### - chip name (perfect match)
### - user name (partial match)
### - site name (partial match)
def __log(args):
    arg_vars = vars(args)
    run_query = {"dbVersion": db_version}
    log_query = {"$and": [], "dbVersion": db_version}

    chip_name = arg_vars.get("chip", None)
    if chip_name:
        query = {"name": chip_name, "dbVersion": db_version}
        chip_entries = localdb.chip.find(query)
        chip_query = []
        for this_chip in chip_entries:
            chip_query.append({"chip": str(this_chip["_id"])})
        if chip_query == []:
            logger.error("Not found chip data in Local DB: %s", chip_name)
            sys.exit(1)
        else:
            run_query.update({"$or": chip_query})

    if run_query != {}:
        run_entries = localdb.componentTestRun.find(run_query)
        run_oids = []
        for run_entry in run_entries:
            run_oids.append({"_id": ObjectId(run_entry["testRun"])})
        if run_oids != []:
            log_query["$and"].append({"$or": run_oids})

    if arg_vars.get("user", None):
        query = {
            "userName": {"$regex": arg_vars["user"].lower().replace(" ", "_")},
            "dbVersion": db_version,
        }
        entries = localdb.user.find(query)
        if entries.count() == 0:
            logger.error("Not found user data in Local DB: %s", arg_vars["user"])
            sys.exit()
        user_oids = []
        for entry in entries:
            user_oids.append({"user_id": str(entry["_id"])})
        if user_oids != []:
            log_query["$and"].append({"$or": user_oids})
    if arg_vars.get("site", None):
        query = {
            "institution": {"$regex": arg_vars["site"].lower().replace(" ", "_")},
            "dbVersion": db_version,
        }
        entries = localdb.institution.find(query)
        if entries.count() == 0:
            logger.error("Not found site data in Local DB: %s", arg_vars["site"])
            sys.exit()
        site_oids = []
        for entry in entries:
            site_oids.append({"address": str(entry["_id"])})
        if site_oids != []:
            log_query["$and"].append({"$or": site_oids})

    if log_query["$and"] == []:
        log_query = {"dbVersion": db_version}

    run_entries = localdb.testRun.find(log_query).sort([("startTime", DESCENDING)])

    r_json = {"log": []}
    for this_run in run_entries:
        query = {"_id": ObjectId(this_run["user_id"]), "dbVersion": db_version}
        this_user = localdb.user.find_one(query)
        query = {"_id": ObjectId(this_run["address"]), "dbVersion": db_version}
        this_site = localdb.institution.find_one(query)
        query = {"testRun": str(this_run["_id"]), "dbVersion": db_version}
        ctr_entries = localdb.componentTestRun.find(query)
        chips = []
        this_dcs = {}
        for this_ctr in ctr_entries:
            if chip_name and this_ctr["name"] == chip_name:
                chips.append("\033[1;31m{}\033[0m".format(this_ctr["name"]))
            else:
                chips.append(this_ctr["name"])
            if this_ctr.get("environment", "...") != "...":
                this_dcs.update({this_ctr["name"]: []})
                query = {
                    "_id": ObjectId(this_ctr["environment"]),
                    "dbVersion": db_version,
                }
                this_env = localdb.environment.find_one(query)
                for key in this_env:
                    if key not in ("_id", "dbVersion", "sys"):
                        this_dcs[this_ctr["name"]].append(key)
        test_data = {
            "user": this_user["userName"],
            "site": this_site["institution"],
            "datetime": setTime(this_run["startTime"]),
            "runNumber": this_run["runNumber"],
            "testType": this_run["testType"],
            "runId": str(this_run["_id"]),
            "chips": chips,
            "dbVersion": this_run["dbVersion"],
            "environment": this_dcs,
        }
        r_json["log"].append(test_data)

    return r_json


######################
### Retrieve test data
### no input -> latest scan
### input chip name -> latest scan for the chip
### input test data ID -> scan specified by ID
### outputs:
### - test information
### - configs
### - data
def __pull(dir_path, args):
    ###################################
    ### Pull data files from testRun ID
    def __pull_test_run(i_oid, i_chip):
        data_entries = []
        query = {"_id": ObjectId(i_oid), "dbVersion": db_version}
        this_tr = localdb.testRun.find_one(query)
        chip_type = (
            this_tr.get("chipType", "NULL")
            if this_tr.get("chipType", "NULL") != "FE-I4B"
            else "FEI4B"
        )

        ### scanLog
        log_json = {}
        for key in this_tr:
            if "Cfg" in key and this_tr[key] != "...":
                ### config file
                query = {"_id": ObjectId(this_tr[key])}
                this_cfg = localdb.config.find_one(query)
                docs = getData(
                    "json", dir_path, this_cfg["filename"], this_cfg["data_id"]
                )
                data_entries.append(docs)
            elif key == "_id":
                log_json.update({key: str(this_tr[key])})
            elif key in ("startTime", "finishTime"):
                log_json.update({key: this_tr[key].timestamp()})
            elif key not in ("address", "user_id", "sys"):
                log_json.update({key: this_tr[key]})

        ### connectivity
        query = {"testRun": i_oid, "dbVersion": db_version}
        entries = localdb.componentTestRun.find(query)

        stage = this_tr.get("stage", "...")
        conn_json = {"stage": stage, "chipType": chip_type, "chips": []}
        chips = []
        for this_ctr in entries:
            if this_ctr["chip"] == "module":
                query = {"_id": ObjectId(this_ctr["component"])}
                this_cmp = localdb.component.find_one(query)
                conn_json.update(
                    {
                        "module": {
                            "serialNumber": this_cmp["name"],
                            "componentType": this_cmp["componentType"],
                        }
                    }
                )
                query = {"component": str(this_cmp["_id"])}
                this_QC = localdb.QC.module.status.find_one(query)
                if this_QC:
                    stage = this_QC["stage"]
                    if conn_json["stage"] != stage:
                        logger.warning("Current stage is \033[1m%s\033[0m\n", stage)
                        conn_json.update({"stage": stage})
                continue
            chip_conn = {}
            for key in this_ctr:
                if key == "config":
                    chip_conn.update({key: f"{dir_path}/{this_ctr[key]}"})
                elif "Cfg" in key and this_ctr[key] != "...":
                    ### chip config
                    query = {"_id": ObjectId(this_ctr[key])}
                    this_cfg = localdb.config.find_one(query)
                    if key == "beforeCfg":
                        docs = getData(
                            "json",
                            dir_path,
                            this_ctr.get("config", "{}.json".format(this_ctr["name"])),
                            this_cfg["data_id"],
                        )
                        data_entries.append(docs)
                        docs = getData(
                            "json",
                            dir_path,
                            "{}.before".format(
                                this_ctr.get(
                                    "config", "{}.json".format(this_ctr["name"])
                                )
                            ),
                            this_cfg["data_id"],
                        )
                        data_entries.append(docs)
                    elif key == "afterCfg":
                        docs = getData(
                            "json",
                            dir_path,
                            "{}.after".format(
                                this_ctr.get(
                                    "config", "{}.json".format(this_ctr["name"])
                                )
                            ),
                            this_cfg["data_id"],
                        )
                        data_entries.append(docs)
                    else:
                        docs = getData(
                            "json",
                            dir_path,
                            "{}_{}.json".format(this_ctr["name"], key),
                            this_cfg["data_id"],
                        )
                        data_entries.append(docs)
                elif key == "attachments":
                    ### attachment
                    for attachment in this_ctr[key]:
                        docs = getData(
                            attachment["contentType"],
                            dir_path,
                            "{}_{}".format(this_ctr["name"], attachment["filename"]),
                            attachment["code"],
                        )
                        data_entries.append(docs)
                elif key not in [
                    "_id",
                    "component",
                    "sys",
                    "chip",
                    "testRun",
                    "environment",
                    "dbVersion",
                ]:
                    chip_conn.update({key: this_ctr[key]})
            conn_json["chips"].append(chip_conn)
            ### output texts
            if i_chip and this_ctr["name"] == i_chip:
                chips.append("\033[1;31m{}\033[0m".format(this_ctr["name"]))
            else:
                chips.append(this_ctr["name"])
        docs = getData("json", dir_path, "connectivity.json", conn_json, True)
        data_entries.append(docs)

        log_json["connectivity"] = []
        log_json["connectivity"].append(conn_json)
        docs = getData("json", dir_path, "scanLog.json", log_json, True)
        data_entries.append(docs)

        ### user data
        query = {"_id": ObjectId(this_tr["user_id"])}
        this_user = localdb.user.find_one(query)

        ### site data
        query = {"_id": ObjectId(this_tr["address"])}
        this_site = localdb.institution.find_one(query)

        ### output texts
        return {
            "_id": str(this_tr["_id"]),
            "col": "testRun",
            "log": {
                "User": "{} at {}".format(
                    this_user["userName"], this_site["institution"]
                ),
                "Date": setTime(this_tr["startTime"]),
                "Chips": ", ".join(chips),
                "Run Number": this_tr["runNumber"],
                "Test Type": this_tr["testType"],
                "Stage": stage,
            },
            "data": data_entries,
        }

    ##############################################
    ### Pull data files from component information
    def __pull_component(i_chip):
        data_entries = []
        query = {"name": i_chip, "dbVersion": db_version}
        this_cmp = localdb.component.find_one(query)
        this_ch = localdb.chip.find_one(query)
        if not this_cmp and not this_ch:
            logger.error("Not found component data in Local DB: %s", i_chip)
            sys.exit(1)
        elif this_cmp:
            this_chip = this_cmp
        else:
            this_chip = this_ch

        ### connectivity
        stage = "Testing"
        chip_type = "NULL"
        conn_json = {"stage": stage, "chips": []}
        module = False
        chips = []
        children = []
        query = {"parent": str(this_chip["_id"]), "dbVersion": db_version}
        entries = localdb.childParentRelation.find(query)
        if entries.count() == 0:
            children.append(str(this_chip["_id"]))
        else:
            conn_json.update(
                {
                    "module": {
                        "serialNumber": this_chip["serialNumber"],
                        "componentType": this_chip["componentType"],
                    }
                }
            )
            query = {"component": str(this_chip["_id"])}
            this_QC = localdb.QC.module.status.find_one(query)
            if this_QC:
                stage = this_QC["stage"]
                conn_json.update({"stage": stage})
            for entry in entries:
                children.append(entry["child"])
            module = True
        configs = []
        for i, chip in enumerate(children):
            query = {"_id": ObjectId(chip)}
            this = localdb.component.find_one(query)
            if not this:
                this = localdb.chip.find_one(query)
                if not this:
                    continue
            chip_type = (
                this.get("chipType", "NULL")
                if this.get("chipType", "NULL") != "FE-I4B"
                else "FEI4B"
            )
            config = "{}/{}.json".format(dir_path, this["name"])
            chip_id = this.get("chipId", -1)
            (
                configs.append(
                    {"chipType": chip_type, "name": this["name"], "config": config}
                ),
            )
            conn_json["chips"].append(
                {
                    "name": this["name"],
                    "config": config,
                    "chipId": chip_id,
                    "tx": i,
                    "rx": i,
                }
            )
            conn_json.update({"chipType": chip_type})
            ### output texts
            if chip == str(this_chip["_id"]):
                chips.append("\033[1;31m{}\033[0m".format(this["name"]))
            else:
                chips.append(this["name"])

        docs = getData("json", dir_path, "connectivity.json", conn_json, True)
        data_entries.append(docs)

        ### output texts
        return {
            "_id": str(this_chip["_id"]),
            "col": "component",
            "log": {
                "Parent": "\033[1;31m{} ({})\033[0m".format(
                    this_chip["serialNumber"], this_chip["componentType"]
                )
                if module
                else None,
                "Chip Type": chip_type,
                "Chips": ", ".join(chips),
                "Stage": stage,
            },
            "data": data_entries,
            "configs": configs,
        }

    #################
    ### main function
    arg_vars = vars(args)

    tr_oid = None
    if arg_vars.get("test", None):
        tr_oid = arg_vars["test"]
    elif arg_vars.get("chip", None):
        if not args.config_only:
            query = {"name": arg_vars["chip"], "dbVersion": db_version}
            entries = localdb.componentTestRun.find(query)
            if entries.count() != 0:
                query = {"$or": [], "dbVersion": db_version}
                for entry in entries:
                    query["$or"].append({"_id": ObjectId(entry["testRun"])})
                entry = (
                    localdb.testRun.find(query)
                    .sort([("startTime", DESCENDING)])
                    .limit(1)
                )
                if entry.count() != 0:
                    tr_oid = str(entry[0]["_id"])
    else:
        query = {"dbVersion": db_version}
        entry = localdb.testRun.find(query).sort([("startTime", DESCENDING)]).limit(1)
        if entry.count() != 0:
            tr_oid = str(entry[0]["_id"])

    if tr_oid:
        query = {"testRun": tr_oid, "dbVersion": db_version}
        entries = localdb.componentTestRun.find(query)
        if entries.count() == 0:
            if arg_vars.get("chip", None):
                console_data = __pull_component(arg_vars["chip"])
            else:
                logger.error("Not found test data ID in Local DB: %s", tr_oid)
                sys.exit(1)
        else:
            console_data = __pull_test_run(tr_oid, arg_vars.get("chip", None))

    elif arg_vars.get("chip", None):
        console_data = __pull_component(arg_vars["chip"])
    else:
        logger.error("Not found any test data in Local DB")
        sys.exit(1)

    return console_data


#####################
### Display data list
### - component
### - user
### - site
def __list_component():
    docs_list = {"parent": [], "child": {}}
    entries = localdb.childParentRelation.find({"dbVersion": db_version})
    oids = []
    for entry in entries:
        oids.append(entry["parent"])
    oids = list(set(oids))
    for oid in oids:
        query = {"_id": ObjectId(oid)}
        this = localdb.component.find_one(query)
        if this["user_id"] != -1:
            query = {"_id": ObjectId(this["user_id"])}
            this_user = localdb.user.find_one(query)
            user = this_user.get("userName", "NULL")
        else:
            user = "NULL"
        query = {"_id": ObjectId(this["address"])}
        this_site = localdb.institution.find_one(query)
        docs = {
            "oid": oid,
            "name": this["name"],
            "type": this["componentType"],
            "asic": this["chipType"],
            "chips": [],
            "user": user,
            "site": this_site.get("institution", "NULL"),
        }
        query = {"parent": oid, "dbVersion": db_version}
        entries = localdb.childParentRelation.find(query)
        for entry in entries:
            docs["chips"].append(entry["child"])
        docs_list["parent"].append(docs)
    query = {"componentType": "front-end_chip", "dbVersion": db_version}
    entries = localdb.component.find(query)
    oids = []
    for entry in entries:
        oids.append(str(entry["_id"]))
    for oid in oids:
        query = {"_id": ObjectId(oid)}
        this = localdb.component.find_one(query)
        if this["user_id"] != -1:
            query = {"_id": ObjectId(this["user_id"])}
            this_user = localdb.user.find_one(query)
            user = this_user.get("userName", "NULL")
        else:
            user = "NULL"
        query = {"_id": ObjectId(this["address"])}
        this_site = localdb.institution.find_one(query)
        docs_list["child"].update(
            {
                oid: {
                    "name": this["name"],
                    "type": this["componentType"],
                    "asic": this["chipType"],
                    "chipId": this["chipId"],
                    "user": user,
                    "site": this_site.get("institution", "NULL"),
                }
            }
        )
    docs_list["parent"] = sorted(docs_list["parent"], key=lambda x: (x["type"]))

    return docs_list


def __list_user():
    docs_list = {}
    entries = localdb.user.find({"dbVersion": db_version})
    users = []
    for entry in entries:
        users.append(str(entry["userName"]))
    for user in users:
        query = {"userName": user, "dbVersion": db_version}
        entries = localdb.user.find(query)
        docs = []
        for entry in entries:
            docs.append(str(entry["institution"]))
        docs = list(set(docs))
        docs_list.update({user: docs})

    return docs_list


def __list_site():
    docs_list = {"localdb": [], "itkpd": []}
    entries = localdb.institution.find({"dbVersion": db_version})
    for entry in entries:
        docs_list["localdb"].append(
            {
                "institution": str(entry.get("institution", "null")),
                "code": str(entry.get("code", "null")),
            }
        )
    entries = localdb.pd.institution.find({"dbVersion": db_version})
    for entry in entries:
        docs_list["itkpd"].append(
            {
                "institution": str(entry.get("institution", "null")),
                "code": str(entry.get("code", "null")),
            }
        )
    docs_list["localdb"] = sorted(
        docs_list["localdb"], key=lambda x: (x["institution"])
    )
    docs_list["itkpd"] = sorted(docs_list["itkpd"], key=lambda x: (x["institution"]))
    return docs_list


#########################
### Pull viewer user data
def __pull_user(i_json):
    docs = {}
    query = {}
    if i_json.get("userName", "") != "":
        query.update({"name": i_json["userName"]})
    if i_json.get("viewerUser", "") != "":
        query.update({"username": i_json["viewerUser"]})
    if query != {}:
        this_user = toolsdb.viewer.user.find_one(query)
        if this_user:
            docs.update(
                {
                    "userName": this_user["name"],
                    "institution": this_user["institution"],
                    "description": "viewer",
                    "viewerUser": this_user["username"],
                }
            )
    return docs


##################
### Pull site data
def __pull_site(i_json):
    docs = {}
    query = {}
    if i_json.get("institution", "") != "":
        query.update({"institution": i_json["institution"]})
    if i_json.get("code", "") != "":
        query.update({"code": i_json["code"]})
    if query != {}:
        this_site = localdb.pd.institution.find_one(query)
        if this_site:
            docs.update(
                {"institution": this_site["institution"], "code": this_site["code"]}
            )
    return docs
