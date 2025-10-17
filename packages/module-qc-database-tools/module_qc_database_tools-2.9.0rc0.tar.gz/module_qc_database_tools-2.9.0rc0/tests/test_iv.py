from __future__ import annotations

import itkdb
import pytest

from module_qc_database_tools.iv import fetch_reference_ivs


@pytest.fixture
def client():
    c = itkdb.Client()
    yield c
    c.close()


@pytest.mark.parametrize(
    "serial_number",
    ["20UPGM22110155"],
)
def test_fetch_reference_iv(client, serial_number):
    result = fetch_reference_ivs(
        client,
        serial_number,
    )
    assert len(result["reference_IVs"]) == 1
    assert all(
        k in result["reference_IVs"][0]["IV_ARRAY"]
        for k in ["current", "humidity", "temperature", "voltage"]
    )
    assert result["reference_IVs"][0]["component_sn"] == "20UPGS35300173"
    assert result["reference_IVs"][0]["stage"] == "BAREMODULERECEPTION"
    assert result["reference_IVs"][0]["Vbd"] == -999.0
    assert result["reference_IVs"][0]["Vfd"] == 52
    assert result["reference_IVs"][0]["Ilc"] == 0.423435
