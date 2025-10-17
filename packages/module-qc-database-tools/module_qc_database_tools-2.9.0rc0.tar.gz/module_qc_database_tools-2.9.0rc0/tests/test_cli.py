from __future__ import annotations

import warnings

import pytest
from typer.testing import CliRunner

from module_qc_database_tools.cli import app


@pytest.fixture
def runner():
    return CliRunner()


def test_generate_yarr_config_help(runner):
    result = runner.invoke(
        app,
        args=[
            "generate-yarr-config",
            "-h",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr


def test_register_component_help(runner):
    result = runner.invoke(
        app,
        args=[
            "register-component",
            "-h",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr


@pytest.mark.parametrize(
    "extra_args",
    [[""], ["--noeos"]],
    ids=["default", "noeos"],
)
def test_generate_yarr_config(request, runner, tmp_path, extra_args):
    warnings.simplefilter("ignore", ResourceWarning)

    if "default" in request.node.callspec.id:
        pytest.skip("Skipping due to broken attachments on component.")

    output_dir = tmp_path / "configs"

    result = runner.invoke(
        app,
        args=[
            "generate-yarr-config",
            "-o",
            output_dir,
            "--sn",
            "20UPGM23610013",
            "--version",
            "TESTONWAFER",
            *extra_args,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.stderr

    paths = [p.relative_to(output_dir) for p in list(output_dir.rglob("*"))]
    assert sorted(map(str, paths)) == [
        "20UPGM23610013",
        "20UPGM23610013/20UPGM23610013_L2_LP.json",
        "20UPGM23610013/20UPGM23610013_L2_cold.json",
        "20UPGM23610013/20UPGM23610013_L2_warm.json",
        "20UPGM23610013/20UPGM23610013_info.json",
        "20UPGM23610013/L2_LP",
        "20UPGM23610013/L2_LP/0x20d85_L2_LP.json",
        "20UPGM23610013/L2_LP/0x20d92_L2_LP.json",
        "20UPGM23610013/L2_LP/0x20d99_L2_LP.json",
        "20UPGM23610013/L2_LP/0x20db9_L2_LP.json",
        "20UPGM23610013/L2_cold",
        "20UPGM23610013/L2_cold/0x20d85_L2_cold.json",
        "20UPGM23610013/L2_cold/0x20d92_L2_cold.json",
        "20UPGM23610013/L2_cold/0x20d99_L2_cold.json",
        "20UPGM23610013/L2_cold/0x20db9_L2_cold.json",
        "20UPGM23610013/L2_warm",
        "20UPGM23610013/L2_warm/0x20d85_L2_warm.json",
        "20UPGM23610013/L2_warm/0x20d92_L2_warm.json",
        "20UPGM23610013/L2_warm/0x20d99_L2_warm.json",
        "20UPGM23610013/L2_warm/0x20db9_L2_warm.json",
    ]
