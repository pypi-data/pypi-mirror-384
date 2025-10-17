from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from module_qc_database_tools.cli.utils import load_localdb_config_from_hw


def test_load_localdb_config_from_hw_none():
    """Test that passing None returns empty dict."""
    result = load_localdb_config_from_hw(None)
    assert result == {}


def test_load_localdb_config_from_hw_valid_config(tmp_path):
    """Test loading valid hardware config with localdb section."""
    config_data = {
        "localdb": {
            "uri_ldb": "https://itkpix-srv.ucsc.edu:443/localdb",
            "uri_mdb": "mongodb://itkpix-srv.ucsc.edu:27017/localdb?ssl=True",
            "tags": ["alpha"],
            "institution": "UCSC",
            "userName": "pixdaq",
        }
    }
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config_data))

    result = load_localdb_config_from_hw(config_file)

    expected = {
        "host": "itkpix-srv.ucsc.edu",
        "port": 443,
        "protocol": "https",
        "mongo_uri": "mongodb://itkpix-srv.ucsc.edu:27017/localdb?ssl=True",
        "localdb_name": "localdb",
        "tags": ["alpha"],
        "institution": "UCSC",
        "userName": "pixdaq",
    }
    assert result == expected


def test_load_localdb_config_from_hw_uri_parsing():
    """Test that URI components are correctly extracted."""
    test_cases = [
        {
            "uri_ldb": "http://localhost:5000/localdb",
            "expected": {"host": "localhost", "port": 5000, "protocol": "http"},
        },
        {
            "uri_ldb": "https://example.com:8080/localdb",
            "expected": {"host": "example.com", "port": 8080, "protocol": "https"},
        },
        {
            "uri_ldb": "https://test.server/localdb",
            "expected": {"host": "test.server", "port": None, "protocol": "https"},
        },
    ]

    for case in test_cases:
        config_data = {
            "localdb": {
                "uri_ldb": case["uri_ldb"],
                "uri_mdb": "mongodb://localhost:27017/testdb",
                "institution": "TEST",
                "userName": "test",
            }
        }

        # Create a mock config file using pytest's tmp_path fixture would be needed here
        # For this test, we'll use a more direct approach by mocking load_hw_config
        with patch(
            "module_qc_database_tools.cli.utils.load_hw_config",
            return_value=config_data,
        ):
            result = load_localdb_config_from_hw(Path("dummy"))

        for key, value in case["expected"].items():
            assert result[key] == value


def test_load_localdb_config_from_hw_tags_handling(tmp_path):
    """Test default empty tags and provided tags."""
    # Test with tags provided
    config_with_tags = {
        "localdb": {
            "uri_ldb": "https://example.com/localdb",
            "uri_mdb": "mongodb://example.com:27017/localdb",
            "tags": ["tag1", "tag2"],
            "institution": "TEST",
            "userName": "test",
        }
    }
    config_file = tmp_path / "with_tags.json"
    config_file.write_text(json.dumps(config_with_tags))

    result = load_localdb_config_from_hw(config_file)
    assert result["tags"] == ["tag1", "tag2"]

    # Test without tags (should default to empty list)
    config_without_tags = {
        "localdb": {
            "uri_ldb": "https://example.com/localdb",
            "uri_mdb": "mongodb://example.com:27017/localdb",
            "institution": "TEST",
            "userName": "test",
        }
    }
    config_file = tmp_path / "without_tags.json"
    config_file.write_text(json.dumps(config_without_tags))

    result = load_localdb_config_from_hw(config_file)
    assert result["tags"] == []


def test_load_localdb_config_from_hw_mongo_uri_parsing(tmp_path):
    """Test that MongoDB URI database name is correctly extracted."""
    test_cases = [
        {"uri_mdb": "mongodb://localhost:27017/testdb", "expected_name": "testdb"},
        {
            "uri_mdb": "mongodb://localhost:27017/testdb?ssl=True",
            "expected_name": "testdb",
        },
        {
            "uri_mdb": "mongodb://localhost:27017/",
            "expected_name": None,  # Should not set localdb_name if path is empty
        },
    ]

    for case in test_cases:
        config_data = {
            "localdb": {
                "uri_ldb": "https://example.com/localdb",
                "uri_mdb": case["uri_mdb"],
                "institution": "TEST",
                "userName": "test",
            }
        }
        config_file = tmp_path / f"test_{case['expected_name']}.json"
        config_file.write_text(json.dumps(config_data))

        result = load_localdb_config_from_hw(config_file)

        if case["expected_name"]:
            assert result["localdb_name"] == case["expected_name"]
        else:
            assert "localdb_name" not in result or not result["localdb_name"]
