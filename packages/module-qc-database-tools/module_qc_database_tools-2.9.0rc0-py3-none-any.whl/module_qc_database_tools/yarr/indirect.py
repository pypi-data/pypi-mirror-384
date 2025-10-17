#################################
# Author: Arisa Kubota
# Email: arisa.kubota at cern.ch
# Date: July 2019
# Project: Local Database for YARR
#################################

# Common
from __future__ import annotations

import sys

# log
from logging import getLogger

import requests

URL = None

logger = getLogger("Log").getChild("sub")


####################
### Response to Json
### exist: return {json}
### not exist: return {}
### not json file: error
def getJson(viewer_url, params=None):
    if params is None:
        params = {}
    response = requests.get(viewer_url, params=params)
    try:
        r_json = response.json()
    except Exception:
        logger.exception("Something wrong in url and could not get json data")
        sys.exit(1)
    if r_json.get("error"):
        logger.error(r_json["message"])
        sys.exit(1)
    return r_json


#########################
### Display test data log
### Searchable by
### - chip name (perfect match)
### - user name (partial match)
### - site name (partial match)
def __log(args):
    params = {}

    params.update({"chip": args.chip})
    params.update({"user": args.user})
    params.update({"site": args.site})

    viewer_url = f"{URL}/retrieve/log"
    return getJson(viewer_url, params)


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
    params = {}
    params.update({"chip": args.chip})
    params.update({"test": args.test})
    params.update({"dir": dir_path})

    # get chip data
    viewer_url = f"{URL}/retrieve/data"
    r_json = getJson(viewer_url, params)

    if r_json.get("warning", None):
        logger.warning(r_json["warning"])

    console_data = r_json["console_data"]
    data_entries = []
    for entry in console_data["data"]:
        if not entry["bool"]:
            viewer_url = "{}/retrieve/config?oid={}&type={}".format(
                URL, entry["data"], entry["type"]
            )
            r_json = getJson(viewer_url)
            entry.update({"data": r_json["data"]})
        data_entries.append(entry)
    console_data["data"] = data_entries

    return console_data


#####################
### Display data list
### - component
### - user
### - site
def __list_component():
    viewer_url = f"{URL}/retrieve/list?opt=component"
    return getJson(viewer_url)


def __list_user():
    viewer_url = f"{URL}/retrieve/list?opt=user"
    return getJson(viewer_url)


def __list_site():
    viewer_url = f"{URL}/retrieve/list?opt=site"
    return getJson(viewer_url)
