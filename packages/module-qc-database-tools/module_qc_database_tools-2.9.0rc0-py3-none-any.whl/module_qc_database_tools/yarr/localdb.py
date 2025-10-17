#################################
# Author: Arisa Kubota
# Email: arisa.kubota at cern.ch
# Date: July 2020
# Project: Local Database for YARR
#################################

### Common
from __future__ import annotations

import hashlib
import logging
import os
from urllib.parse import urlparse

import requests
from pymongo import MongoClient, errors

from module_qc_database_tools import exceptions


class LocalDb:
    def __init__(self):
        self.logger = logging.getLogger("Log").getChild("LocalDb")
        self.service = "mongodb"
        self.username = None
        self.password = None
        self.auth = "default"
        self.tls = False
        self.ssl = False
        self.__set_config()

    def setCfg(self, i_cfg):
        self.service = i_cfg.get("service", "mongodb")

        if "hostIp" in i_cfg:
            self.ip = i_cfg["hostIp"]
        if "hostPort" in i_cfg:
            self.port = i_cfg["hostPort"]
        if "dbName" in i_cfg:
            self.name = i_cfg["dbName"]
        if "tls" in i_cfg:
            self.tls = i_cfg["tls"].get("enabled", False)
        if "ssl" in i_cfg:
            self.ssl = i_cfg["ssl"].get("enabled", False)
        if "auth" in i_cfg:
            self.auth = i_cfg["auth"]
        if "username" in i_cfg:
            self.username = i_cfg["username"]
        if "password" in i_cfg:
            self.password = i_cfg["password"]
        if self.tls:
            self.cert = i_cfg["tls"].get("CertificateKeyFile", None)
            self.ca = i_cfg["tls"].get("CAFile", None)
        if self.ssl:
            self.cert = i_cfg["ssl"].get("PEMKeyFile", None)
            self.ca = i_cfg["ssl"].get("CAFile", None)

        return self.service

    def setUsername(self, i_username):
        self.username = i_username

    def setPassword(self, i_password):
        self.password = i_password

    def checkConnection(self):
        if self.service == "mongodb":
            url = f"mongodb://{self.ip}:{self.port}"
            if self.tls or self.ssl:
                url += "/?ssl=true"
                if self.ca and self.cert:
                    url += f"&ssl_ca_certs={self.ca}&ssl_certfile={self.cert}&ssl_match_hostname=false"
            if self.auth == "x509":
                url += "&authMechanism=MONGODB-X509"
                self.authSource = "$external"
            self.url = url
            self.__check_connection_mongo()
        elif self.service == "viewer":
            url = f"http://{self.ip}:{self.port}/localdb/"
            self.url = url
            self.__check_connection_viewer()
        return self.url

    def getClient(self):
        return self.client

    def getLocalDb(self):
        return self.client[self.name]

    def getLocalDbTools(self):
        return self.client[f"{self.name}tools"]

    def __set_config(self):
        if self.service == "mongodb":
            self.ip = "127.0.0.1"
            self.port = 27017
            self.name = "localdb"
            self.authSource = "localdb"
        elif self.service == "viewer":
            self.ip = "127.0.0.1"
            self.port = 5000
        else:
            raise exceptions.DBServiceError()

    def __check_connection_mongo(self):
        """Check connection to MongoDB and handle authentication if needed."""
        self.logger.info(
            "Checking connection to DB Server: %s/%s ...", self.url, self.name
        )
        max_server_delay = 1000

        client = MongoClient(
            self.url,
            serverSelectionTimeoutMS=max_server_delay,
            authSource=self.authSource,
        )
        localdb = client[self.name]

        try:
            localdb.command("ping")
            self.__connection_succeeded()
        except errors.ServerSelectionTimeoutError as err:
            return self.__connection_failed("to", err)

        try:
            localdb.list_collection_names()
        except errors.OperationFailure as err:
            self.logger.info("Local DB is locked.")
            return self.__attempt_authentication(err, max_server_delay)

        self.client = client
        return True

    def __attempt_authentication(self, err, max_server_delay):
        """Attempt to authenticate if initial connection fails."""
        username = self.username or os.environ.get("USERNAME")
        password = self.password or os.environ.get("PASSWORD", "")

        if not username and os.environ.get("username"):  # noqa: SIM112
            self.logger.warning(
                "Using the `username` environment variable is deprecated. Please use `USERNAME`"
            )
            username = os.environ.get("username")  # noqa: SIM112

        if not password and os.environ.get("password"):  # noqa: SIM112
            self.logger.warning(
                "Using the `password` environment variable is deprecated. Please use `PASSWORD`"
            )
            password = os.environ.get("password")  # noqa: SIM112

        if username and not self.username:
            username = hashlib.md5(username.encode("utf-8")).hexdigest()

        if not username or not password:
            return self.__connection_failed("auth", "No username and password given")

        parts = urlparse(self.url)
        auth_url = parts._replace(
            netloc=f"{username}:{password}@{parts.netloc}"
        ).geturl()

        client = MongoClient(
            auth_url,
            serverSelectionTimeoutMS=max_server_delay,
            authSource=self.authSource,
        )
        localdb = client[self.name]

        try:
            localdb.list_collection_names()
            self.__connection_succeeded("Authentication success.")
            self.client = client
            return True
        except errors.ServerSelectionTimeoutError:
            return self.__connection_failed("to", err)
        except errors.OperationFailure:
            return self.__connection_failed("auth", err)

    def __check_connection_viewer(self):
        self.logger.info("Checking connection to Viewer: %s ...", self.url)
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                self.__connection_succeeded()
            else:
                self.__connection_failed("code", response.status_code)
        except Exception as err:
            self.__connection_failed("", err)
        return True

    def __connection_succeeded(self, message="Good connection!"):
        self.logger.info("---> %s", message)

    def __connection_failed(self, err="to", message=""):
        if self.service == "mongodb":
            if err == "to":
                self.logger.error("---> Bad connection.")
                self.logger.error("     %s", message)
                raise exceptions.DBConnectionError()
            if err == "auth":
                self.logger.error("---> %s", message)
                self.logger.error(
                    "     Please login Local DB with correct username and password by"
                )
                self.logger.error(
                    "        $ source path/to/YARR/localdb/login_mongodb.sh"
                )
                raise exceptions.DBAuthenticationFailure()
        elif self.service == "viewer":
            if err == "code":
                self.logger.error("---> Bad connection.")
                self.logger.error("     http response status code: %s", message)
                raise exceptions.ViewerConnectionError()

            self.logger.error("---> Bad connection.")
            self.logger.error("     %s", message)
            raise exceptions.ViewerConnectionError()
