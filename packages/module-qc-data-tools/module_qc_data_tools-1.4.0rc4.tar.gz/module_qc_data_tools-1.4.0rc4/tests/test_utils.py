from __future__ import annotations

import json
import logging

import pytest

import module_qc_data_tools


def test_serial_number_to_uid():
    assert (
        module_qc_data_tools.utils.chip_serial_number_to_uid("20UPGFC0087209")
        == "0x154a9"
    )


def test_uid_to_serial_number():
    assert (
        module_qc_data_tools.utils.chip_uid_to_serial_number("0x154a9")
        == "20UPGFC0087209"
    )


def test_uid_is_none():
    with pytest.raises(TypeError):
        module_qc_data_tools.utils.chip_uid_to_serial_number(None)


@pytest.mark.parametrize(
    ("serial_number", "chip_type"),
    [
        ("20UPIM11602031", "RD53B"),
        ("20UPIM12602031", "RD53B"),
        ("20UPIM13602031", "ITKPIXV2"),
        ("20UPIM14602031", "ITKPIXV2"),
        ("20UPIM15602031", "ITKPIXV2"),
    ],
)
def test_chip_type_from_module_serial_number(serial_number, chip_type):
    assert (
        module_qc_data_tools.utils.get_chip_type_from_serial_number(serial_number)
        == chip_type
    )


class TestHwConfigUtilities:
    """Test suite for hardware config utilities."""

    @pytest.fixture
    def valid_hw_config(self):
        """Fixture providing a valid hardware config."""
        return {
            "yarr": {
                "run_dir": "/path/to/yarr",
                "controller": "configs/controller.json",
                "scanConsole_exe": "bin/scanConsole",
                "write_register_exe": "bin/write_register",
                "read_register_exe": "bin/read_register",
                "read_adc_exe": "bin/read_adc",
                "switchLPM_exe": "bin/switchLPM",
                "lpm_digitalscan": "configs/lpm_digitalscan.json",
                "eyeDiagram_exe": "bin/eyeDiagram",
                "read_ringosc_exe": "bin/read_ringosc",
            },
            "power_supply": {
                "run_dir": "/path/to/ps",
                "on_cmd": "power_on",
                "off_cmd": "power_off",
                "set_cmd": "set_voltage {v} {i}",
                "getI_cmd": "get_current",
                "getV_cmd": "get_voltage",
                "measI_cmd": "measure_current",
                "measV_cmd": "measure_voltage",
            },
            "multimeter": {
                "run_dir": "/path/to/multimeter",
                "dcv_cmd": ["measure_ch0", "measure_ch1"],
                "share_vmux": True,
                "v_mux_channels": [0, 0, 0, 0],
            },
        }

    @pytest.fixture
    def minimal_valid_hw_config(self):
        """Fixture providing a minimal valid hardware config."""
        return {
            "yarr": {
                "run_dir": "/yarr",
                "controller": "controller.json",
                "scanConsole_exe": "scanConsole",
                "write_register_exe": "write_register",
                "read_register_exe": "read_register",
                "read_adc_exe": "read_adc",
                "switchLPM_exe": "switchLPM",
                "lpm_digitalscan": "lpm_digitalscan.json",
                "eyeDiagram_exe": "eyeDiagram",
                "read_ringosc_exe": "read_ringosc",
            },
            "power_supply": {
                "run_dir": "/ps",
                "on_cmd": "on",
                "off_cmd": "off",
                "set_cmd": "set {v} {i}",
                "getI_cmd": "getI",
                "getV_cmd": "getV",
                "measI_cmd": "measI",
                "measV_cmd": "measV",
            },
            "multimeter": {
                "run_dir": "/mm",
                "dcv_cmd": ["dcv"],
                "share_vmux": False,
                "v_mux_channels": [0, 1, 2, 3],
            },
        }

    def test_check_hw_config_valid(self, valid_hw_config):
        """Test check_hw_config with valid configuration."""
        assert module_qc_data_tools.utils.check_hw_config(valid_hw_config) is True

    def test_check_hw_config_minimal_valid(self, minimal_valid_hw_config):
        """Test check_hw_config with minimal valid configuration."""
        assert (
            module_qc_data_tools.utils.check_hw_config(minimal_valid_hw_config) is True
        )

    def test_check_hw_config_missing_required_field(self):
        """Test check_hw_config with missing required field."""
        invalid_config = {
            "yarr": {
                "run_dir": "/yarr"
                # Missing required fields
            }
        }
        with pytest.raises(
            RuntimeError, match="Input hardware config fails schema check"
        ):
            module_qc_data_tools.utils.check_hw_config(invalid_config)

    def test_check_hw_config_invalid_type(self):
        """Test check_hw_config with invalid field type."""
        invalid_config = {
            "yarr": {
                "run_dir": 123,  # Should be string
                "controller": "controller.json",
                "scanConsole_exe": "scanConsole",
                "write_register_exe": "write_register",
                "read_register_exe": "read_register",
                "read_adc_exe": "read_adc",
                "switchLPM_exe": "switchLPM",
                "lpm_digitalscan": "lpm_digitalscan.json",
                "eyeDiagram_exe": "eyeDiagram",
                "read_ringosc_exe": "read_ringosc",
            }
        }
        with pytest.raises(
            RuntimeError, match="Input hardware config fails schema check"
        ):
            module_qc_data_tools.utils.check_hw_config(invalid_config)

    def test_check_hw_config_empty_dict(self):
        """Test check_hw_config with empty dictionary - should pass as schema allows empty object."""
        # The schema appears to allow empty objects, so this should return True
        assert module_qc_data_tools.utils.check_hw_config({}) is True

    def test_check_hw_config_with_optional_fields(self, valid_hw_config):
        """Test check_hw_config with optional fields."""
        # Add optional fields
        valid_hw_config["yarr"]["success_code"] = 0
        valid_hw_config["yarr"]["max_attempts"] = 3
        valid_hw_config["yarr"]["sleep_attempts"] = 2.0
        valid_config_with_optional = valid_hw_config

        assert (
            module_qc_data_tools.utils.check_hw_config(valid_config_with_optional)
            is True
        )

    def test_check_hw_config_with_high_voltage(self, minimal_valid_hw_config):
        """Test check_hw_config with high voltage configuration."""
        minimal_valid_hw_config["high_voltage"] = {
            "run_dir": "/hv",
            "on_cmd": "hv_on",
            "off_cmd": "hv_off",
            "set_cmd": "hv_set {v} {i}",
            "getI_cmd": "hv_getI",
            "getV_cmd": "hv_getV",
            "measI_cmd": "hv_measI",
            "measV_cmd": "hv_measV",
        }

        assert (
            module_qc_data_tools.utils.check_hw_config(minimal_valid_hw_config) is True
        )

    def test_check_hw_config_with_ntc(self, minimal_valid_hw_config):
        """Test check_hw_config with NTC configuration."""
        minimal_valid_hw_config["ntc"] = {"run_dir": "/ntc", "cmd": "read_temperature"}

        assert (
            module_qc_data_tools.utils.check_hw_config(minimal_valid_hw_config) is True
        )

    def test_check_hw_config_with_localdb(self, minimal_valid_hw_config):
        """Test check_hw_config with localdb configuration."""
        minimal_valid_hw_config["localdb"] = {
            "uri_ldb": "http://localhost:8080",
            "uri_mdb": "mongodb://localhost:27017",
            "tags": ["test", "qa"],
            "institution": "CERN",
            "userName": "testuser",
        }

        assert (
            module_qc_data_tools.utils.check_hw_config(minimal_valid_hw_config) is True
        )

    def test_load_hw_config_valid_file(self, valid_hw_config, tmp_path):
        """Test load_hw_config with valid config file."""
        config_file = tmp_path / "hw_config.json"
        config_file.write_text(json.dumps(valid_hw_config))

        loaded_config = module_qc_data_tools.utils.load_hw_config(config_file)
        assert loaded_config == valid_hw_config

    def test_load_hw_config_invalid_file(self, tmp_path):
        """Test load_hw_config with config that should trigger validation error."""
        # Create a config that should actually fail validation - use wrong types
        invalid_config = {
            "yarr": {
                "run_dir": 123,  # Should be string, not number
                "controller": "controller.json",
            }
        }

        config_file = tmp_path / "invalid_config.json"
        config_file.write_text(json.dumps(invalid_config))

        with pytest.raises(
            RuntimeError, match="Input hardware config fails schema check"
        ):
            module_qc_data_tools.utils.load_hw_config(config_file)

    def test_load_hw_config_nonexistent_file(self, tmp_path):
        """Test load_hw_config with nonexistent file."""
        nonexistent_file = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            module_qc_data_tools.utils.load_hw_config(nonexistent_file)

    def test_load_hw_config_malformed_json(self, tmp_path):
        """Test load_hw_config with malformed JSON file."""
        config_file = tmp_path / "malformed.json"
        config_file.write_text('{"invalid": json}')  # Malformed JSON

        with pytest.raises(json.JSONDecodeError):
            module_qc_data_tools.utils.load_hw_config(config_file)

    def test_load_hw_config_deprecated_format_warning(self, caplog, tmp_path):
        """Test load_hw_config logs warning for deprecated config format."""
        deprecated_config = {
            "tasks": {"test": "config"},
            "yarr": {
                "run_dir": "/yarr",
                "controller": "controller.json",
                "scanConsole_exe": "scanConsole",
                "write_register_exe": "write_register",
                "read_register_exe": "read_register",
                "read_adc_exe": "read_adc",
                "switchLPM_exe": "switchLPM",
                "lpm_digitalscan": "lpm_digitalscan.json",
                "eyeDiagram_exe": "eyeDiagram",
                "read_ringosc_exe": "read_ringosc",
            },
            "power_supply": {
                "run_dir": "/ps",
                "on_cmd": "on",
                "off_cmd": "off",
                "set_cmd": "set {v} {i}",
                "getI_cmd": "getI",
                "getV_cmd": "getV",
                "measI_cmd": "measI",
                "measV_cmd": "measV",
            },
            "multimeter": {
                "run_dir": "/mm",
                "dcv_cmd": ["dcv"],
                "share_vmux": True,
                "v_mux_channels": [0, 0, 0, 0],
            },
        }

        config_file = tmp_path / "deprecated_config.json"
        config_file.write_text(json.dumps(deprecated_config))

        with caplog.at_level(logging.ERROR):
            # This should succeed but log a warning about deprecated format
            loaded_config = module_qc_data_tools.utils.load_hw_config(config_file)
            assert loaded_config == deprecated_config

        # Check that error messages were logged
        log_messages = [record.message for record in caplog.records]
        assert any(
            "has both measurement and hardware configs" in msg for msg in log_messages
        )
        assert any("mqt split-old-config" in msg for msg in log_messages)
