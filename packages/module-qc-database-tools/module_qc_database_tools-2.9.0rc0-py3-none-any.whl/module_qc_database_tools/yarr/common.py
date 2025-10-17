#################################
# Author: Arisa Kubota
# Email: arisa.kubota at cern.ch
# Date: July 2020
# Project: Local Database for YARR
#################################
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import yaml

from module_qc_database_tools import exceptions

logger = logging.getLogger("Log").getChild("common")


home = os.environ["HOME"]
hostname = os.environ.get("HOSTNAME", "default_host")


def readCfg(i_path):
    """This function converts yaml config file to dict."""
    logger.debug("Read config file: %s", i_path)
    if Path(i_path).is_file():
        with Path(i_path).open() as f:
            return yaml.load(f, Loader=yaml.SafeLoader)
    return None


def readKey(i_path):
    """This function read key file for authentication with Local DB."""
    logger.debug("Read key file: %s", i_path)
    with Path(i_path).open() as file_text:
        file_keys = file_text.read().split()
    keys = {"username": file_keys[0], "password": file_keys[1]}
    file_text.close()
    return keys


def writeJson(i_dict, i_path):
    """
    This function writes dict data into JSON file.
    If data is not dict, handle it as an exception.
    """
    logger.debug("Write data into JSON file: %s", i_path)
    try:
        with Path(i_path).open("w") as f:
            json.dump(i_dict, f, indent=4)
    except Exception as err:
        logger.exception("Could not write JSON file: %s", i_path)
        raise exceptions.JsonParsingError() from err


def readJson(i_path):
    """
    This function reads JSON file and convert it to dict format.
    If a JSON parsing error occurs, handle it as an exception.
    """
    logger.debug("Read JSON file and convert it to dict: %s", i_path)
    j = {}
    if i_path and Path(i_path).is_file():
        try:
            with Path(i_path).open() as f:
                j = json.load(f)
        except ValueError as err:
            logger.exception("Could not parse %s", i_path)
            raise exceptions.JsonParsingError() from err
    return j


def readDbCfg(args, log=None, path=""):
    """
    This function reads database config from
    1. argument: --database
    2. path written in scanLog.json: for upload tool
    3. default: $HOME/.yarr/localdb/$HOSTNAME_database.json
    raise ConfigError if no db config
    """
    if log is None:
        log = {}
    cfg = {}
    num = 0
    if args.database:
        path = str(Path(args.database).resolve())
        cfg = readJson(path)
        num = 1
    elif log != {}:
        cfg = log
        num = 2
    else:
        path = f"{home}/.yarr/localdb/{hostname}_database.json"
        cfg = readJson(path)
        path = path + " (default)"
        num = 3
    logger.info("-> Setting database config: %s", path)
    if cfg == {}:
        logger.error("\033[5mNot found database config.\033[0m")
        if num in (1, 2):
            logger.error(
                "Specify the correct path to database config file under -d option."
            )
        else:
            logger.error("Create the default config by")
            logger.error("   $ path/to/YARR/localdb/setup_db.sh")
        raise exceptions.ConfigError()
    return cfg


def readUserCfg(args, log=None, path=""):
    """
    This function reads user config from
    1. argument: --user
    2. path written in scanLog.json: for upload tool
    3. default: $HOME/.yarr/localdb/user.json
    Return empty if no config
    """
    if log is None:
        log = {}
    cfg = log
    if args.user:
        path = str(Path(args.user).resolve())
        cfg.update(readJson(path))
    if cfg == {}:
        path = f"{home}/.yarr/localdb/user.json"
        cfg = readJson(path)
    logger.info("-> Setting user config: %s", path)
    return cfg


def readSiteCfg(args, log=None, path=""):
    """
    This function reads site config from
    1. argument: --site
    2. path written in scanLog.json: for upload tool
    3. default: $HOME/.yarr/localdb/$HOSTNAME_site.json
    Return empty if no config
    """
    if log is None:
        log = {}
    cfg = log
    if args.site:
        path = str(Path(args.site).resolve())
        cfg.update(readJson(path))
    if cfg == {}:
        path = f"{home}/.yarr/localdb/{hostname}_site.json"
        cfg = readJson(path)
    logger.info("-> Setting site config: %s", path)
    return cfg


def writeUserCfg(doc=None, path=""):
    """
    This function writes user config file
    """
    if doc is None:
        doc = {}
    if path == "":
        path = f"{home}/.yarr/localdb/user.json"
    if doc != {}:
        writeJson(doc, path)
    doc = readJson(path)
    logger.info("-> Set user config: %s", path)
    logger.info("~~~ {")
    for key in doc:
        logger.info('~~~   "%s": "%s"', key, doc[key])
    logger.info("~~~ }")


def writeSiteCfg(doc=None, path=""):
    """
    This function writes site config file
    """
    if doc is None:
        doc = {}
    if path == "":
        path = f"{home}/.yarr/localdb/{hostname}_site.json"
    if doc != {}:
        writeJson(doc, path)
    doc = readJson(path)
    logger.info("-> Set site config: %s", path)
    logger.info("~~~ {")
    for key in doc:
        logger.info('~~~   "%s": "%s"', key, doc[key])
    logger.info("~~~ }")


def addInstanceMethod(Class, method):
    setattr(Class, method.__name__, method)
