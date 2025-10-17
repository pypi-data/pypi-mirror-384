from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import sys
import time as time_module
from getpass import getpass
from pathlib import Path

import dateutil
import pandas as pd
import pytz
from influxdb import InfluxDBClient, exceptions

from module_qc_database_tools import yarr

logger = logging.getLogger("Log")
yarr.db_logging.setLog()


class dcsDataClient:
    def __init__(
        self,
        remote_host="127.0.0.1",
        remote_port="8086",
        dbname="",
        use_ssl=False,
        influxpath="",
        username="",
    ):
        self.password = ""

        if "INFLUXDBPWD" in os.environ:
            # Don't ask the user twice (if the pwd was already entered in a previous stage)
            self.password = str(os.environ["INFLUXDBPWD"])

        try:
            # Try to connect without authentication
            self.client = InfluxDBClient(
                host=remote_host,
                port=remote_port,
                database=dbname,
                ssl=use_ssl,
                verify_ssl=use_ssl,
                path=influxpath,
                username=username,
                password=self.password,
            )

            database_list = self.client.get_list_database()

        except exceptions.InfluxDBClientError as e:
            # If auth is enabled, ask the user for his/her password
            if "authorization failed" in str(e):
                logger.warning(
                    'Input the password for user "%s" in InfluxDB. If you don\'t want to input the password in the future until you close your current bash session (e.g. you are running a script that calls this many times), use "export INFLUXDBPWD=yourPassword\'.',
                    username,
                )
                try:
                    self.password = getpass()
                except Exception:
                    logger.exception()
                    sys.exit(1)

        # And connect again.
        self.client = InfluxDBClient(
            host=remote_host,
            port=remote_port,
            database=dbname,
            ssl=use_ssl,
            verify_ssl=use_ssl,
            path=influxpath,
            username=username,
            password=self.password,
        )

        try:
            # It should be working now if the user entered the right pwd
            database_list = self.client.get_list_database()

        except exceptions.InfluxDBClientError as e:
            # If not, let the user know what's happening and exit.
            logger.error("Received error from InfluxDB: %s", e)
            logger.warning(
                "Please specify the db connectivity parameters "
                '"database", and optionally also "username", '
                '"host" and "port" in the ."influxdb_cfg" section in'
                "the file passed with --dcs_config or -d (-F if calling from dbAccessor)"
            )

            logger.warning(
                "See an example in %s/localdb/configs/influxdb_connectivity.json",
                Path.cwd(),
            )

            sys.exit(1)

        self.runStart = 0
        self.runEnd = 1566546707353068032
        if {"name": dbname} not in database_list:
            self.db_exist = False
        else:
            self.db_exist = True
            self.meas_list = self.client.get_list_measurements()

    def setTimeRange(self, start, end):
        self.runStart = start
        self.runEnd = end

    def getEvent(self, measName, tags=None):
        tags = tags or {}
        if self.db_exist:
            if {"name": measName} in self.meas_list:
                query_string = f'SELECT * FROM "{measName}" WHERE time >= {self.runStart} AND time <= {self.runEnd}'
                if tags:
                    for tag, value in tags.items():
                        query_string += f" and {tag}='{value}'"
                return self.client.query(query_string)
            # error_message('measurement',measName)
            return None
        return None


def getArgs():
    parser = argparse.ArgumentParser(description="data downloader from InfluxDB")

    parser.add_argument("command", help="select function : test/retrieve/remove")
    parser.add_argument("-c", "--chip", help="provided chipname")
    parser.add_argument(
        "-d", "--dcs_config", help="provided configuration file (.json) for DCS data"
    )
    parser.add_argument("-s", "--scan", help="provided scanLog file of target Scan")
    parser.add_argument("--port", help="provided port Number", default="8086")
    parser.add_argument("--host", help="provided host", default="127.0.0.1")
    parser.add_argument("--dbname", help="provided database name", default="")
    parser.add_argument("--database", help="provided database config")
    parser.add_argument(
        "--output",
        help="provided output directory name (default:same directory of scanLog.json)",
        default="/tmp/",
    )

    return parser.parse_args()


def error_message(key_type, name):
    logger.error("%s : %s is not found!", key_type, name)


def loadDBConnectivity(dcs_config_fname):
    with Path(dcs_config_fname).open() as dcs_config_f:
        dcs_config = json.load(dcs_config_f)

    if "influxdb_cfg" not in dcs_config:
        logger.error(
            'No "influxdb_cfg" key found in the influxDB connectivity file: %s',
            dcs_config_fname,
        )
        sys.exit(1)

    if "database" not in dcs_config["influxdb_cfg"]:
        logger.error(
            "Please specify the db connectivity parameters "
            '"database", and optionally also "username", '
            '"host" and "port" in the ."influxdb_cfg" section in "%s"',
            dcs_config_fname,
        )
        sys.exit(1)

    cfg = dcs_config["influxdb_cfg"]
    remote_host = cfg.get("host")
    remote_port = cfg.get("port")
    username = cfg.get("username")
    influxpath = cfg.get("influx-path")
    use_ssl = cfg.get("use-ssl", False)
    dbname = cfg.get("database")

    return cfg, remote_host, remote_port, username, influxpath, use_ssl, dbname


def getData(client, dcs_config_fname, chip, output_DIR):
    output_jsonName = f"{output_DIR}/dcsDataInfo.json"
    with Path(dcs_config_fname).open() as dcs_config_f:
        dcs_config = json.load(dcs_config_f)

    if dcs_config.get("environments") is None:
        logger.error("dcs Configuration file : %s", dcs_config)
        return 1

    dcsInfo = {}
    dcsInfo["environments"] = []
    for dcsList in dcs_config["environments"]:
        measurement = dcsList.get("measurement")
        now_ts = time_module.time()
        datFileName = f"{output_DIR}/{measurement}{now_ts}.dat"
        data_list = client.getEvent(measurement)  # ignore tags first
        if data_list is None:
            error_message("measurement", measurement)
        else:
            with Path(datFileName).open("w") as dat_f:
                key_text = "key unixtime "
                num_text = "num 0 "
                mode_text = "mode null "
                setting_text = "setting null "
                keyList = []
                tagsList = []
                for dcs in dcsList["dcsList"]:
                    key = dcs.get("key")
                    tags = dcs.get("tags", {})
                    num = 0
                    for i_key in keyList:
                        if key == i_key:
                            num += 1
                    keyList.append(key)
                    tagsList.append(tags)
                    key_text += str(key) + " "
                    num_text += str(num) + " "
                    mode_text += "null "
                    setting_text += str(dcs.get("setting", 0)) + " "
                    description = dcs.get("description")
                    dcsInfo["environments"] = appendDcsInfo(
                        dcsInfo["environments"],
                        description,
                        key,
                        num,
                        dcs.get("setting", 0),
                        datFileName,
                        chip,
                    )

                dat_f.write(key_text + "\n")
                dat_f.write(num_text + "\n")
                # dat_f.write(mode_text+'\n')
                dat_f.write(setting_text + "\n")

                # filter by tags
                data_list = client.getEvent(measurement, tags)

                for data in data_list[measurement]:
                    time = data.get("time")
                    unixtime = (
                        datetime.datetime.strptime(time[0:19], "%Y-%m-%dT%H:%M:%S")
                        .replace(tzinfo=pytz.utc)
                        .timestamp()
                    )

                    data_text = str(time) + " " + str(int(unixtime))
                    for dcs in dcsList["dcsList"]:
                        value = str(data.get(dcs.get("data_name")))
                        if value == "None":
                            value = "null"
                        data_text += " " + value
                    dat_f.write(data_text + "\n")
    with Path(output_jsonName).open("w") as of:
        json.dump(
            dcsInfo,
            of,
            ensure_ascii=False,
            indent=4,
            sort_keys=True,
            separators=(",", ": "),
        )
    return None


def getScanLog(scanLog_file):
    with Path(scanLog_file).open() as f:
        return json.load(f)


def calculate_runTime(scanLog):
    # Reading from Yarr's cfg the timestamp corresponding to the beginning of the analysis
    start_time_str = scanLog["timestamp"]
    start_time = datetime.datetime.strptime(
        start_time_str, "%Y-%m-%d_%H:%M:%S"
    ).replace(tzinfo=dateutil.tz.tzlocal())
    start_timestamp = pd.to_datetime(str(start_time))  # local time in InfluxDB

    # Calculate the timestamp corresponding to the end of the analysis
    stopwatch = scanLog["stopwatch"]
    analysis = stopwatch["analysis"]
    config = stopwatch["config"]
    processing = stopwatch["processing"]
    scan = stopwatch["scan"]
    total_ms = analysis + config + processing + scan
    end_timestamp = start_timestamp + pd.offsets.Milli(total_ms)

    # Add an extra offset to make sure we catch the whole scan
    offset_time = 15000  # ms
    start_timestamp = start_timestamp - pd.offsets.Milli(offset_time)
    end_timestamp = end_timestamp + pd.offsets.Milli(offset_time)

    # Although start_timestamp and end_timestamp have ms precision, the values
    # of both are completed with 0s until ns (6 extra 0s). We have to remove 3
    # to have the value in us (so InfluxDB does not complain), although the
    # actual precision is ms)

    # return int(start_timestamp.value/1000), int(end_timestamp.value/1000)
    return int(start_timestamp.value), int(end_timestamp.value)


def appendDcsInfo(dcsInfoList, description, key, num, setting, path, chip):
    singleInfo = {}
    singleInfo["description"] = description
    singleInfo["key"] = key
    singleInfo["num"] = num
    singleInfo["setting"] = setting
    singleInfo["path"] = path
    singleInfo["chip"] = chip
    singleInfo["status"] = "enabled"

    dcsInfoList.append(singleInfo)
    return dcsInfoList


def removeDatFile(dcsInfo_path):
    dcsInfo = Path(dcsInfo_path)
    with dcsInfo.open() as dcsinfo_f:
        dcsinfo_json = json.load(dcsinfo_f)
        for env in dcsinfo_json["environments"]:
            path = Path(env["path"])
            if path.exists():
                path.unlink()
    dcsInfo.unlink()


def main():
    args = getArgs()

    command = args.command
    dcs_config_fname = args.dcs_config

    if command == "test":
        sys.exit(0)
    elif command == "init":
        if args.dcs_config is None:
            logger.error(
                "dcs configuration file is required! Please specify dcs configuration file path under --dcs_config or -d"
            )
            sys.exit(1)
        try:
            (
                _cfg,
                remote_host,
                remote_port,
                username,
                influxpath,
                use_ssl,
                dbname,
            ) = loadDBConnectivity(dcs_config_fname)
            client = dcsDataClient(
                remote_host=remote_host,
                remote_port=remote_port,
                dbname=dbname,
                use_ssl=use_ssl,
                influxpath=influxpath,
                username=username,
            )

        except Exception:
            logger.exception("---> Bad connection to Influx DB.")
            sys.exit(1)
    elif command == "remove":
        if args.scan is None:
            logger.error(
                "scanlog file is required! Please specify scan log file path under --scan or -s"
            )
            sys.exit(1)
        scanlog_path = args.scan
        scan_dir = Path(scanlog_path).parent
        if scan_dir.exists():
            dcsDataInfo_path = scan_dir / "dcsDataInfo.json"
            removeDatFile(dcsDataInfo_path)
        else:
            error_message("target directory", scan_dir)

    elif command == "retrieve":
        # required variable check
        if args.chip is None:
            logger.error(
                "chipname is required! Please specify chipname under --chip or -c"
            )
            sys.exit(1)
        if args.dcs_config is None:
            logger.error(
                "dcs configuration file is required! Please specify dcs configuration file path under --dcs_config or -d"
            )
            sys.exit(1)

        (
            _cfg,
            remote_host,
            remote_port,
            username,
            influxpath,
            use_ssl,
            dbname,
        ) = loadDBConnectivity(dcs_config_fname)

        remote_port = args.port or remote_port
        remote_host = args.host or remote_host
        dbname = args.dbname or dbname
        if args.scan is not None:
            scanlog_path = args.scan

        if not Path(args.output).exists():
            error_message("directory", args.output)
            sys.exit(1)

        start_runTime, end_runTime = calculate_runTime(getScanLog(scanlog_path))

        client = dcsDataClient()
        if client.db_exist:
            client.setTimeRange(start_runTime, end_runTime)
            getData(client, dcs_config_fname, args.chip, args.output)
            sys.exit(0)
        else:
            error_message("database", args.dbname)
            sys.exit(1)


if __name__ == "__main__":
    main()
