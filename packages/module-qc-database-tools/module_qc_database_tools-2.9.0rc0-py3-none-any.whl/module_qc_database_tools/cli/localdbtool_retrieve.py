#################################
# Author: Arisa Kubota
# Email: arisa.kubota at cern.ch
# Date: July 2019
# Project: Local Database for YARR
#################################

# Common
from __future__ import annotations

import argparse
import io
import json
import logging
import os
import sys
from pathlib import Path

from module_qc_database_tools import exceptions, yarr

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

logger = logging.getLogger("Log")

home = os.environ["HOME"]
hostname = os.environ.get("HOSTNAME", "default_host")


class CommandError(Exception):
    pass


def getArgs():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "command",
        help="option*\tfuntion\n"
        + "init\tFunction initialization & Connection check\n"
        + "log\tDisplay data log\n"
        + "pull\tData retrieve\n"
        + "list\tDisplay data list\n"
        + "user\tGet user&site data\n",
        type=str,
        nargs="*",
    )
    parser.add_argument(
        "--config", help="Set User Config Path of Local DB Server.", type=str
    )
    parser.add_argument(
        "--username", help="Set the User Name of Local DB Server.", type=str
    )
    parser.add_argument(
        "--password", help="Set the Password of Local DB Server.", type=str
    )
    parser.add_argument("--database", help="Set Database Config Path", type=str)
    parser.add_argument("--user", help="Set the name of the user.", type=str)
    parser.add_argument("--site", help="Set the name of the site.", type=str)
    parser.add_argument("--chip", help="Set the name of the chip.", type=str)
    parser.add_argument("--test", help="Set data ID of the test.", type=str)
    parser.add_argument(
        "--directory", help="Provide directory name.", type=str, default="./db-data"
    )
    parser.add_argument(
        "--config_only", help="Set mode to pull config files only.", action="store_true"
    )
    parser.add_argument("--QC", help="Set QC Mode", action="store_true")

    args = parser.parse_args()

    if args.config is not None:
        conf = yarr.common.readCfg(args.config)  # Read from config file
        if "user" in conf and not args.user:
            args.user = conf["user"]
        if "site" in conf and not args.site:
            args.site = conf["site"]
        if "chip" in conf and not args.chip:
            args.chip = conf["chip"]
        if "directory" in conf and not args.directory:
            args.directory = conf["directory"]

    return args


################
# read JSON file
def readJson(i_path):
    logger.debug("Read json file and convert it to dict: %s", i_path)
    try:
        return yarr.common.readJson(i_path)
    except Exception as e:
        messages = str(e).split("\n")
        for message in messages:
            logger.error(message)
        __error_exit()


##########################
### Display log on console
def printLog(message):
    try:
        input(message)
    except KeyboardInterrupt:
        sys.exit()


######################
### main functions ###
######################


############
# Initialize
# Check the retrieve directory and connection to Local DB
def __init(db_cfg):
    logger.debug("Initialize.")

    args = getArgs()

    db = yarr.localdb.LocalDb()
    try:
        service = db.setCfg(db_cfg)
    except exceptions.DBCfgError:
        __error_exit("database")

    if args.username:
        db.setUsername(args.username)
    if args.password:
        db.setPassword(args.password)

    url = None
    try:
        url = db.checkConnection()
        connection = True
    except Exception:
        connection = False

    return {"service": service, "connection": connection, "url": url, "db": db}


#####################
# error exit function
def __check_command():
    """
    This function checks command notation
    If there is any mistake, this function outputs error message and raises CommandError
    """
    args = getArgs()
    command = args.command
    nargs = len(args.command) - 1
    if not command:
        logger.error("Usage: localdbtool-retrieve <command> [--option]")
        logger.error("These are common retrieve commands used in various situations:")
        logger.error("")
        logger.error(
            "\tinit\t\tInitialize retrieve function and check connection to Local DB"
        )
        logger.error("\tlog\t\tDisplay test data log in Local DB")
        logger.error("\tpull\t\tRetrieve data from Local DB")
        logger.error("\tlist\t\tDisplay component/user/site data list")
        logger.error("\tuser\t\tRetrieve user&site data from Local DB")
        logger.error("")
        logger.error("See 'localdbtool-retrieve --help' to check available options")
        logger.error("")
        logger.error("The following argument is required: command")
        raise CommandError

    if command[0] == "test":
        pass
    elif command[0] == "init":
        if nargs != 0:
            logger.error("Usage: localdbtool-retrieve init [--database <dbCfg>]")
            logger.error("")
            logger.error("Option 'init' requires no parameters.")
            raise CommandError
    elif command[0] == "log":
        if nargs != 0:
            logger.error(
                "Usage: localdbtool-retrieve log [--database <dbCfg>] [--user <user_name>] [--site <site_name>] [--chip <chip_name>]"
            )
            logger.error("")
            logger.error("Option 'log' requires no parameters.")
            raise CommandError
    elif command[0] == "pull":
        if (args.chip and args.test) or nargs != 0:
            logger.error(
                "Usage: localdbtool-retrieve pull [--directory <dir>] [--database <dbCfg>]"
            )
            logger.error(
                "   or: localdbtool-retrieve pull --chip <chip_name> [--directory <dir>] [--database <dbCfg>]"
            )
            logger.error(
                "   or: localdbtool-retrieve pull --test <test_ID> [--directory <dir>] [--database <dbCfg>]"
            )
            logger.error("")
            logger.error('Option \'pull\' supports an option "--chip" or "--test".')
            raise CommandError
    elif command[0] == "list":
        if nargs != 0 and not (
            nargs == 1
            and (
                command[1] == "component"
                or command[1] == "user"
                or command[1] == "site"
            )
        ):
            logger.error("Usage: localdbtool-retrieve list")
            logger.error("   or: localdbtool-retrieve list component")
            logger.error("   or: localdbtool-retrieve list user")
            logger.error("   or: localdbtool-retrieve list site")
            logger.error("")
            logger.error(
                'Option \'list\' supports a parameter "component", "user", or "site".'
            )
            raise CommandError
    elif command[0] == "user":
        if nargs != 0:
            logger.error(
                "Usage: localdbtool-retrieve user [--database <dbCfg>] [--user <userCfg>] [--site <siteCfg>]"
            )
            logger.error("")
            logger.error("Option 'user' requires no parameters.")
            raise CommandError
    else:
        logger.error(
            "'%s' is not retrieve command. See 'localdbtool-retrieve --help' to check available commands and options.",
            command[0],
        )
        raise CommandError


def __error_exit(command=""):
    if command == "directory":
        logger.error('Not set directory name to "localdb"')
    elif command in ("database", "site", "user"):
        logger.error(
            "There is no default %s config in %s/.yarr/localdb. Set it by path/to/YARR/localdb/setup_db.sh",
            home,
            command,
        )
        logger.error("")
    elif command == "connection":
        logger.error(
            "Could not access Local DB, retry again in the good connection to Local DB Server"
        )

    logger.info("-----------------------")
    sys.exit(1)


def main():
    logger.debug("Main Function.")
    args = getArgs()
    command = args.command
    nargs = len(args.command) - 1

    try:
        __check_command()
    except CommandError:
        logger.error("")
        logger.error("Command Exception: Aborting...")
        sys.exit(1)

    if command[0] == "test":
        sys.exit(0)

    yarr.db_logging.setLog()

    logger.info("-----------------------")

    if args.database:
        db_cfg = readJson(args.database)
    else:
        db_cfg = readJson(f"{home}/.yarr/localdb/{hostname}_database.json")

    response = __init(db_cfg)
    if command[0] == "init":
        logger.info("Function: Initialize")
        logger.info("-----------------------")
        if response["connection"]:
            sys.exit(0)
        else:
            sys.exit(1)

    if response["connection"]:
        if response["service"] == "viewer":
            from module_qc_database_tools.yarr import (  # noqa: PLC0415
                indirect as function,
            )

            function.URL = response["url"]
        else:
            from module_qc_database_tools.yarr import (  # noqa: PLC0415
                direct as function,
            )

            db = response["db"]
            function.localdb = db.getLocalDb()
            function.toolsdb = db.getLocalDbTools()
    else:
        __error_exit("connection")

    if command[0] == "log":
        r_json = function.__log(args)
        for test_data in r_json["log"]:
            printLog("\033[1;33mtest data ID: {} \033[0m".format(test_data["runId"]))
            printLog(
                "User      : {} at {}".format(test_data["user"], test_data["site"])
            )
            printLog("Date      : {}".format(test_data["datetime"]))
            printLog("Component : {}".format(", ".join(test_data["chips"])))
            printLog("Run Number: {}".format(test_data["runNumber"]))
            printLog("Test Type : {}".format(test_data["testType"]))
            if test_data.get("environment", {}) == {}:
                printLog("DCS Data  : NULL")
            else:
                printLog("DCS Data  :")
                for chip in test_data.get("environment", {}):
                    if args.chip == chip:
                        printLog(
                            "   \033[1;31m{} ({})\033[0m".format(
                                ", ".join(test_data["environment"][chip]), chip
                            )
                        )
                    else:
                        printLog(
                            "   {} ({})".format(
                                ", ".join(test_data["environment"][chip]), chip
                            )
                        )
            printLog("")
        logger.info("-----------------------")
        sys.exit(0)
    if command[0] == "pull":
        # make directory
        dir_path = args.directory
        logger.info("Retrieve/Create data files in %s", dir_path)
        if dir_path == "localdb":
            __error_exit("directory")
        if Path(dir_path).is_dir():
            logger.warning(
                "Already exist directory: %s. Please specify the new directory.",
                dir_path,
            )
            sys.exit(1)
        Path(dir_path).mkdir(parents=True)
        console_data = function.__pull(dir_path, args)
        logger.info(
            "\033[1;33m%s data ID: %s \033[0m", console_data["col"], console_data["_id"]
        )
        for key in console_data["log"]:
            if console_data["log"][key]:
                logger.info("- %s: %s", key, console_data["log"][key])
        for data in console_data["data"]:
            logger.info("Retrieve ... %s", data["path"])
            if data["type"] == "json":
                with Path(data["path"]).open("w") as f:
                    json.dump(data["data"], f, indent=4)
            else:
                with Path(data["path"]).open("w") as f:
                    f.write(data["data"])
        logger.warning(
            '\033[31mPlease confirm if there is no mistake in "%s/connectivity" before running scanConsole.\033[0m',
            args.directory,
        )
        if console_data.get("configs", []):
            logger.warning("\033[31mAnd create chip config files by:\033[0m")
        for chip_config in console_data.get("configs", []):
            logger.warning(
                "\033[31m    ./bin/createConfig -t %s -n %s -o %s\033[0m",
                chip_config["chipType"],
                chip_config["name"],
                chip_config["config"],
            )
        logger.info("-----------------------")
        sys.exit(0)
    if command[0] == "list":
        if nargs == 0:
            opt = "component"
        elif nargs == 1 and (
            command[1] == "component" or command[1] == "user" or command[1] == "site"
        ):
            opt = command[1]
        if opt == "component":
            r_json = function.__list_component()
            printLog("")
            for docs in r_json["parent"]:
                printLog("\033[1;33m{}: {} \033[0m".format(docs["type"], docs["name"]))
                printLog("User      : {} at {}".format(docs["user"], docs["site"]))
                printLog("Chip Type : {}".format(docs["asic"]))
                printLog("Chips({})  :".format(len(docs["chips"])))
                for oid in docs["chips"]:
                    if oid in r_json["child"]:
                        chip_docs = r_json["child"][oid]
                        printLog(
                            "\033[1;33m    {}: {} \033[0m".format(
                                chip_docs["type"], chip_docs["name"]
                            )
                        )
                        printLog(
                            "    User  : {} at {}".format(
                                chip_docs["user"], chip_docs["site"]
                            )
                        )
                        printLog("    ChipId: {}".format(chip_docs["chipId"]))
                        del r_json["child"][oid]
                printLog("")
            for oid in r_json["child"]:
                if oid in r_json["child"]:
                    docs = r_json["child"][oid]
                    printLog(
                        "\033[1;33m{}: {} \033[0m".format(docs["type"], docs["name"])
                    )
                    printLog("User      : {} at {}".format(docs["user"], docs["site"]))
                    printLog("Chip Type : {}".format(docs["asic"]))
                    printLog("ChipId    : {}".format(docs["chipId"]))
                    printLog("")

        elif opt == "user":
            r_json = function.__list_user()

            printLog("")
            for user in r_json:
                printLog(f"\033[1;33mUser Name: {user}\033[0m")
                for docs in r_json[user]:
                    printLog("- %s", docs)
                printLog("")

        elif opt == "site":
            r_json = function.__list_site()
            printLog("")
            printLog("ITk PD Institution List:")
            for site in r_json["itkpd"]:
                printLog(
                    "- \033[1;33m{}\033[0m \033[1;32m(Code: {})\033[0m".format(
                        site["institution"], site["code"]
                    )
                )
            printLog("Local DB Institution List:")
            for site in r_json["localdb"]:
                printLog(
                    "- \033[1;33m{}\033[0m \033[1;32m(Code: {})\033[0m".format(
                        site["institution"], site["code"]
                    )
                )
            printLog("")

        logger.info("-----------------------")
        sys.exit(0)

    if command[0] == "user":
        # user
        user_path = ""
        user_path = args.user if args.user else f"{home}/.yarr/localdb/user.json"
        user_json = readJson(user_path)
        r_json = function.__pull_user(user_json)
        if r_json == {} and args.QC:
            logger.error("Not found QC user data registered in Local DB.")
            logger.error("Please set your Local DB Viewer account correctly in")
            logger.error('{ "viewerUser": "xxx" } in %s', user_path)
            logger.error(
                "If you do not have such an account, please contact Local DB administrator in your institute."
            )
            sys.exit(1)
        yarr.common.writeUserCfg(r_json, user_path)

        # site
        site_path = args.site or f"{home}/.yarr/localdb/{hostname}_site.json"
        site_json = yarr.common.readJson(site_path)
        r_json = function.__pull_site(site_json)
        if r_json == {} and args.QC:
            r_json = function.__pull_site(user_json)
        if r_json == {} and args.QC:
            logger.error("Not found QC site data registered in Local DB.")
            logger.error("Please set your institution correctly in ")
            logger.error(
                '{ "code": "xxx" } or { "institution": "xxx" } in %s', site_path
            )
            sys.exit(1)
        yarr.common.writeSiteCfg(r_json, site_path)
        logger.info("-----------------------")
        sys.exit(0)


if __name__ == "__main__":
    main()
