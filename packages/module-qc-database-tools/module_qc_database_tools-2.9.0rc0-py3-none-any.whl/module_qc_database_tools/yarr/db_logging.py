#################################
# Author: Arisa Kubota
# Email: arisa.kubota at cern.ch
# Date: July 2020
# Project: Local Database for YARR
#################################
from __future__ import annotations

import os
from copy import copy
from logging import (
    INFO,
    FileHandler,
    Formatter,
    StreamHandler,
    getLogger,
)
from pathlib import Path

_level = INFO
# _level = DEBUG
logger = getLogger("Log")
logger.setLevel(_level)

LevelNames = {
    "DEBUG": "[ debug  ]",  # white
    "INFO": "[  info  ]",  # cyan
    "WARNING": "[warning ]",  # yellow
    "ERROR": "[ error  ]",  # red
    "CRITICAL": "[critical]",  # white on red bg
}

LevelColors = {
    "DEBUG": 37,  # white
    "INFO": 32,  # green
    "WARNING": 33,  # yellow
    "ERROR": 31,  # red
    "CRITICAL": 41,  # white on red bg
}


class ColoredFormatter(Formatter):
    def __init__(self, pattern):
        Formatter.__init__(self, pattern, datefmt="%H:%M:%S")

    def format(self, record):
        colored_record = copy(record)
        levelname = colored_record.levelname
        color = LevelColors.get(levelname, 37)
        name = LevelNames.get(levelname, "[unknown ]")
        colored_levelname = f"\033[{color}m{name}[   Local DB    ]:\033[0m"
        colored_record.levelname = colored_levelname
        return Formatter.format(self, colored_record)


class LogFileFormatter(Formatter):
    def __init__(self, pattern):
        Formatter.__init__(self, pattern)

    def format(self, record):
        file_record = copy(record)
        levelname = file_record.levelname
        name = LevelNames.get(levelname, "[unknown ]")
        file_levelname = f"{name}[   Local DB    ]:"
        file_record.levelname = file_levelname
        return Formatter.format(self, file_record)


def setLog(level=_level):
    console = StreamHandler()
    console.setLevel(level)
    formatter = ColoredFormatter("[%(asctime)s:%(msecs)-3d]%(levelname)s %(message)s")
    console.setFormatter(formatter)
    logger.addHandler(console)

    logger.setLevel(level)
    logger.debug("Set log")


def setLogFile(filename="", level=_level):
    if filename == "":
        home = os.environ["HOME"]
        dirname = f"{home}/.yarr/localdb/log/"
        if Path(f"{dirname}/log").is_file():
            size = Path(f"{dirname}/log").stat().st_size
            if size / 1000.0 > 1000:  # greater than 1MB
                Path(f"{dirname}/log").rename(f"{dirname}/log-old-0")
                for i in reversed(range(10)):
                    if Path(f"{dirname}/log-old-{i}").is_file():
                        Path(f"{dirname}/log-old-{i}").rename(
                            f"{dirname}/log-old-{i + 1}"
                        )
                if Path(f"{dirname}/log-old-{10}").is_file():
                    Path(f"{dirname}/log-old-{10}").unlink()
        filename = f"{dirname}/log"
    dir_path = Path(filename).parent
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    handler = FileHandler(filename)
    handler.setLevel(level)
    formatter = ColoredFormatter("[%(asctime)s:%(msecs)-3d]%(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.debug("Set log file: %s", filename)
