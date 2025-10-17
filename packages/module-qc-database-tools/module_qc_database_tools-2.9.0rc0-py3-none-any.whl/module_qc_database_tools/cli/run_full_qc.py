from __future__ import annotations

import argparse
import json
import logging
import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# from typing import Optional
import itksn
import typer
from module_qc_data_tools.utils import (
    get_chip_type_from_serial_number,
    get_config_type_from_connectivity_path,
    get_layer_from_sn,
)

# app = typer.Typer(context_settings=CONTEXT_SETTINGS)

# Logging
logger = logging.getLogger(__name__)


class FullQCConf:
    """
    Class to contain all configs and functions to run full QC.
    """

    def __init__(self):
        ## placeholders for derived variables
        self.TYPE = "L2_warm"
        self.LPTYPE = "L2_LP"

        ## commandline
        self.BASEDIR = Path.home()
        self.MODULESN = ""
        self.LDBHOST = "localhost"
        self.LDBPORT = "5000"
        self.PROTOCOL = "http"
        self.CONNECTIVITY = (
            self.BASEDIR / self.MODULESN / f"{self.MODULESN}_{self.TYPE}.json"
        )
        self.CONTROLLER = "configs/controller/specCfg-rd53b-16x1.json"
        self.CONFIG = self.BASEDIR / "configs" / "new_hw_config.json"
        self.MEASCONFIG = ""
        self.OUTPUT = self.BASEDIR / self.MODULESN

        ## fixed
        ## will be overwritten from HW config
        self.YARR = self.BASEDIR / "Yarr"
        ## will be overwritten from module connectivity file path
        self.MODULEDIR = self.BASEDIR / self.MODULESN
        ## will be overwritten depending on module SN
        self.CHIPTYPE = "itkpixv2"
        self.CURRENTDIR = Path.cwd()

    def measure(self, meas):
        """
        Function to run simple calibration measurement (non-YARR-scans).
        """
        # Handle module connectivity file depending on the QC type i.e. "_warm" or "_LP"
        # module connectivity file e.g. "<MODULESN>_L2_warm.json"
        if meas in {"OVERVOLTAGE-PROTECTION", "UNDERSHUNT-PROTECTION"}:
            tmp_connectivity = (
                f"{Path(self.CONNECTIVITY).parent}/{self.MODULESN}_{self.LPTYPE}.json"
            )
            qc_type = self.LPTYPE
        else:
            tmp_connectivity = self.CONNECTIVITY
            qc_type = self.TYPE

        # Run measurement command
        cmd = [
            "mqt",
            "measurement",
            meas.lower(),
            "-c",
            str(self.CONFIG),
            "-m",
            str(tmp_connectivity),
            "-o",
            str(self.OUTPUT),
        ]
        if self.MEASCONFIG:
            cmd.extend(["-cm", self.MEASCONFIG])

        subprocess.run(cmd, check=True)

        # Find latest measurement results
        meas = meas.replace("-", "_")
        meas_dir = self.OUTPUT / "Measurements" / meas
        if not Path.exists(meas_dir):
            typer.echo(
                f"[red]Measurement directory for {meas} does not exist: {meas_dir}[/]."
            )
            raise typer.Exit(2)

        last_meas_path = sorted(meas_dir.iterdir(), key=os.path.getctime)[-1]
        logger.info("Measurement results in %s", last_meas_path)

        # Create timestamped analysis directory
        analysis_dir = self.OUTPUT / "Analysis" / meas
        analysis_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Using analysis directory: %s", analysis_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        ana_dir = analysis_dir / timestamp
        ana_dir.mkdir()
        logger.info("Analysis results directory: %s", ana_dir)

        # Upload measurements and generate analysis results
        ana_results = ana_dir / f"{self.MODULESN}.json"
        subprocess.run(
            [
                "mqdbt",
                "upload-measurement",
                "--path",
                str(last_meas_path),
                "--host",
                self.LDBHOST,
                "--port",
                self.LDBPORT,
                "--protocol",
                self.PROTOCOL,
                "--out",
                str(ana_results),
            ],
            check=True,
        )

        # Update chip CONFIG
        subprocess.run(
            [
                "analysis-update-chip-config",
                "-i",
                str(ana_dir),
                "-c",
                str(self.MODULEDIR),
                "-t",
                qc_type,
            ],
            check=True,
        )

        # Create symlink
        (ana_dir / "Measurements").symlink_to(last_meas_path)

        # Re-run eye diagram if necessary
        if meas == "ANALOG_READBACK":
            subprocess.run(
                [
                    "./bin/eyeDiagram",
                    "-r",
                    self.CONTROLLER,
                    "-c",
                    str(tmp_connectivity),
                ],
                cwd=self.YARR,
                check=True,
            )

        return 0

    def get_args(self):
        """
        Function using argparse to parse commandline arguments.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-b", "--basedir", type=Path, default=self.BASEDIR, help="Base directory."
        )
        parser.add_argument("-sn", "--modulesn", type=str, help="Module serial number.")
        parser.add_argument(
            "-m",
            "--module-connectivity",
            default=self.CONNECTIVITY,
            type=Path,
            help="Path to module connectivity file.",
        )
        parser.add_argument(
            "-r",
            "--controller",
            type=Path,
            default=self.CONTROLLER,
            help="Path to module connectivity file.",
        )
        parser.add_argument(
            "-c",
            "--config",
            type=Path,
            required=True,
            help="Path to hardware config file",
        )
        parser.add_argument(
            "-cm", "--measconfig", type=Path, help="Path to measurement config file"
        )
        parser.add_argument(
            "-o",
            "--output",
            type=Path,
            default=self.OUTPUT,
            help="Path to output directory",
        )
        parser.add_argument("--port", type=str, default=self.LDBPORT, help="LDB port")
        parser.add_argument("--host", type=str, default=self.LDBHOST, help="LDB host")
        parser.add_argument(
            "--protocol",
            type=str,
            default=self.PROTOCOL,
            help="Protocol - http or https.",
        )

        tests = parser.add_argument_group("tests")
        tests.add_argument(
            "-iv",
            action="store_true",
            help="Run sensor leakage current vs bias voltage.",
        )
        tests.add_argument(
            "-cal", action="store_true", help="Run CALibration measurements."
        )
        tests.add_argument("-mht", action="store_true", help="Run Minimum Health Test.")
        tests.add_argument("-tun", action="store_true", help="Run TUNing.")
        tests.add_argument(
            "-pfa", action="store_true", help="Run Pixel Failure Analysis."
        )
        args = parser.parse_args()

        logger.info(args)
        return parser, args

    def run_scan(self, scan_name, scan_output, tag):
        """
        Function to concatenate commands and run YARR scan
        """
        cmd = [
            "./bin/scanConsole",
            "-r",
            str(self.YARR / self.CONTROLLER),
            "-c",
            str(self.CONNECTIVITY),
            "-o",
            str(scan_output),
            "-W",
            tag,
            "-s",
        ]
        ## this is needed, otherwise YARR error due to not able to find scan config file e.g. "std_totscan.json -t 6000"
        cmd.extend(
            shlex.split(f"{self.YARR}/configs/scans/{self.CHIPTYPE}/{scan_name}")
        )
        subprocess.run(cmd, cwd=self.YARR, check=True)

    def iv(self):
        """
        Function to only run IV-MEASURE
        """
        self.measure("IV-MEASURE")
        return 0

    def cal(self):
        """
        Function to only run simple calibration non-YARR scans.
        """
        logger.info("Running simple (calibration) scans...")

        # # Run core column scan
        try:
            subprocess.run(
                [
                    "./bin/scanConsole",
                    "-r",
                    str(self.CONTROLLER),
                    "-c",
                    str(self.CONNECTIVITY),
                    "-s",
                    f"{self.YARR}/configs/scans/{self.CHIPTYPE}/corecolumnscan.json",
                ],
                cwd=self.YARR,
                check=True,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Unable to run core column scan: %s", e)

        # Perform QC measurements
        measurements = [
            "ADC-CALIBRATION",
            "ANALOG-READBACK",
            "SLDO",
            "VCAL-CALIBRATION",
            "INJECTION-CAPACITANCE",
            "LP-MODE",
            "DATA-TRANSMISSION",
        ]

        for meas in measurements:
            self.measure(meas)
        return 0

    def mht(self):
        """
        Runs all YARR scans in a Minimum Health Test and tags all scans with MHT
        """
        # Yarr-related Scans
        scan_output = self.OUTPUT / "data"
        scan_output.mkdir(parents=True, exist_ok=True)

        logger.info("Scan output directory: %s", scan_output)
        logger.info("Running minimum health test...")
        scans = [
            "std_digitalscan.json",
            "std_analogscan.json",
            "std_thresholdscan_hr.json",
            "std_totscan.json -t 6000",
        ]

        for scan in scans:
            self.run_scan(scan, scan_output, "MHT")

        return 0

    def tun(self):
        """
        Runs all YARR scans required for TUNing and tags all scans with TUN.
        Threshold tuning depends on the layer information.
        ToT tuning depends on the frontend chip type (only available for ITkPix v2).
        """
        # Yarr-related Scans
        scan_output = self.OUTPUT / "data"
        scan_output.mkdir(parents=True, exist_ok=True)

        logger.info("Scan output directory: %s", scan_output)
        logger.info("Tuning...")
        tunings = ["std_thresholdscan_hr.json", "std_totscan.json -t 6000"]

        layer = get_layer_from_sn(self.MODULESN, for_analysis=False)

        ## ToT tuning for v2 chips
        if "itkpixv2" in self.CHIPTYPE:
            if layer in ["L1", "L2"]:
                tunings.extend(["std_tune_globalthreshold.json -t 1700"])
            else:
                tunings.extend(["std_tune_globalthreshold.json -t 1200"])
            tunings.extend(["std_tune_globalpreamp.json -t 6000 7"])

        if layer in ["L1", "L2"]:
            tunings.extend(
                [
                    "std_tune_globalthreshold.json -t 1700",
                    "std_tune_pixelthreshold.json -t 1500",
                ]
            )
        else:
            tunings.extend(
                [
                    "std_tune_globalthreshold.json -t 1200",
                    "std_tune_pixelthreshold.json -t 1000",
                ]
            )

        tunings.extend(["std_thresholdscan_hd.json", "std_totscan.json -t 6000"])

        ## reset previous tuning before tuning
        subprocess.run(
            [
                sys.executable,  ## A string giving the absolute path of the executable binary for the Python interpreter
                "scripts/clear_chip_config.py",
                "-c",
                str(self.CONNECTIVITY),
            ],
            cwd=self.YARR,
            check=True,
        )

        for scan in tunings:
            self.run_scan(scan, scan_output, "TUN")

        return 0

    def pfa(self):
        """
        Runs all YARR scans for Pixel Failure Analysis and tags all scans with PFA.
        """
        # Yarr-related Scans
        scan_output = self.OUTPUT / "data"
        scan_output.mkdir(parents=True, exist_ok=True)

        logger.info("Scan output directory: %s", scan_output)
        logger.info("Running pixel failure scans...")
        failureScans = [
            "std_digitalscan.json -m 1",
            "std_analogscan.json",
            "std_thresholdscan_hd.json",
        ]
        if "itkpixv2" in self.CHIPTYPE:
            failureScans.extend(["std_totscan.json -t 6000"])
        failureScans.extend(
            [
                "std_noisescan.json",
                "std_discbumpscan.json",
                "std_mergedbumpscan.json -t 2000",
            ]
        )

        for scan in failureScans:
            self.run_scan(scan, scan_output, "PFA")

        return 0


def main(
    # MODULESN: Optional[str] = OPTIONS["serial_number"],
    # OUTPUT: Optional[Path] = typer.Option(
    # None,
    # "-o",
    # "--outdir",
    # help="Path to output directory.",
    # exists=False,
    # writable=True,
    # ),
    # LDBHOST: str = OPTIONS["host"],
    # LDBPORT: int = OPTIONS["port"],
    # PROTOCOL: str = OPTIONS["protocol"],
    # dry_run: bool = OPTIONS["dry_run"],
    # CONTROLLER: Optional[Path] = OPTIONS["controller_config"],
    # CONNECTIVITY: Path = OPTIONS["module_connectivity"],
    # CONFIG: Path = OPTIONS["config_hw"],
    # _verbosity: LogLevel = OPTIONS["verbosity"]
):
    """
    Main function to execute all QC scans.

    For instructions in case of core column issues, see https://codimd.web.cern.ch/s/iTKWoRkuP .

    Set up local DB with the latest Yarr release
    This should be done before running the script
    Create ssh tunneling using first. For example, do
    `ssh -f -N admin@server1.example.com -L 8080:server1.example.com:3000`
    After the tunneling has been successfully created, do
    `./localdb/setup_db.sh`
    For more information, see https://cern.ch/yarr/localdb/.
    """
    # Configurations; use uppercase for global variables

    qc = FullQCConf()

    parser, args = qc.get_args()

    if args.module_connectivity:
        qc.CONNECTIVITY = args.module_connectivity

    if args.config:
        qc.CONFIG = args.config
        with Path.open(qc.CONFIG, encoding="utf-8") as _hwconf:
            qc.YARR = json.load(_hwconf)["yarr"]["run_dir"]

    check_existence = [qc.CONNECTIVITY, qc.CONFIG]

    for item in check_existence:
        if not Path.exists(item):
            logger.error("Path does not exist: %s!", item)
            sys.exit(2)

    if args.modulesn:
        qc.MODULESN = args.modulesn

    if args.basedir:
        qc.BASEDIR = args.basedir

    if args.controller:
        qc.CONTROLLER = args.controller

    if args.output:
        qc.OUTPUT = args.output

    if args.port:
        qc.LDBPORT = args.port

    if args.host:
        qc.LDBHOST = args.host

    if args.protocol:
        qc.PROTOCOL = args.protocol

    if not qc.MODULESN:
        qc.MODULESN = (
            str(qc.CONNECTIVITY).rsplit("/", maxsplit=1)[-1].split("_", maxsplit=1)[0]
        )

    qc.CHIPTYPE = get_chip_type_from_serial_number(qc.MODULESN).lower()
    qc.TYPE = get_config_type_from_connectivity_path(qc.CONNECTIVITY)
    qc.LPTYPE = "_".join([qc.TYPE.split("_", maxsplit=1)[0], "LP"])
    qc.MODULEDIR = qc.CONNECTIVITY.parent

    _tests = [group for group in parser._action_groups if "tests" in group.title]  # pylint: disable=protected-access
    _tests = _tests[0]  ## type <class 'argparse._ArgumentGroup'>
    logger.debug(_tests)

    logger.info("Hardware config: %s", qc.CONFIG)
    logger.info("Module connectivity: %s", qc.CONNECTIVITY)
    logger.info("Output directory: %s", qc.OUTPUT)

    try:
        _cmd = ["analysis-check-kshunt-in-chip-config", "-c", qc.MODULEDIR]
        subprocess.run(_cmd, check=True)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("!!! Not able to update k-factors in the chip config %s !!!", e)

    if not any(getattr(args, item.dest) for item in _tests._group_actions):  # pylint: disable=protected-access
        logger.info("No single tests specified, running full QC.")
        ## if not digital, run measure(IV)
        info = itksn.parse(qc.MODULESN.encode("utf-8"))
        if "digital" not in info.component_code.title().lower():
            qc.iv()
        # Run eye diagram
        subprocess.run(
            [
                "./bin/eyeDiagram",
                "-r",
                str(qc.CONTROLLER),
                "-c",
                str(qc.CONNECTIVITY),
            ],
            cwd=qc.YARR,
            check=True,
        )
        qc.cal()
        qc.mht()
        qc.tun()
        qc.pfa()
        logger.info("Script completed successfully.")
    else:
        for item in _tests._group_actions:  # pylint: disable=protected-access
            ## e.g. _StoreTrueAction(option_strings=['-iv'], dest='iv', nargs=0, const=True, default=False, type=None, choices=None, required=False, help='Run sensor leakage current vs bias voltage.', metavar=None)
            logger.debug(item)
            logger.debug(type(item))

            if getattr(args, item.dest):
                # Run eye diagram
                subprocess.run(
                    [
                        "./bin/eyeDiagram",
                        "-r",
                        str(qc.CONTROLLER),
                        "-c",
                        str(qc.CONNECTIVITY),
                    ],
                    cwd=qc.YARR,
                    check=True,
                )
                exec(f"qc.{item.dest}()")  # pylint: disable=exec-used


if __name__ == "__main__":
    main()
