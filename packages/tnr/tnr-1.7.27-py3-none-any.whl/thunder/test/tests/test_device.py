# test_device.py
import pytest
from click.testing import CliRunner
from unittest.mock import patch
import json


def test_device_valid_input(temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()

    # Invoke the command 'tnr device a100'
    result = runner.invoke(cli, ["device", "a100"])

    # Assert that the command executed successfully
    assert result.exit_code == 0
    assert "✅ Device set to 1 x A100" in result.output

    # Verify that the config file was updated correctly
    with open(temp_config_file, "r") as f:
        config = json.load(f)
        assert config["gpuType"] == "a100"
        assert config["gpuCount"] == 1


def test_device_invalid_input(temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()

    # Invoke the command 'tnr device fake_device'
    result = runner.invoke(cli, ["device", "fake_device"])

    # Assert that the command failed
    assert result.exit_code != 0
    assert "Unsupported" in result.output


def test_device_no_arguments(temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()

    # Invoke the command 'tnr device' without arguments
    result = runner.invoke(cli, ["device"])

    # Assert that the command executed successfully
    assert result.exit_code == 0

    # Check the output for the current GPU
    assert "Current" in result.output
    assert "T4" in result.output.upper()


def test_device_set_ngpus(temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()

    # Invoke the command 'tnr device a100 -n 2'
    result = runner.invoke(cli, ["device", "a100", "-n", "2"])

    # Assert that the command executed successfully
    assert result.exit_code == 0
    assert "evice set" in result.output

    # Verify that the config file was updated correctly
    with open(temp_config_file, "r") as f:
        config = json.load(f)
        assert config["gpuType"] == "a100"
        assert config["gpuCount"] == 2


def test_device_set_cpu(temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()

    # Invoke the command 'tnr device cpu'
    result = runner.invoke(cli, ["device", "cpu"])

    # Assert that the command executed successfully
    assert result.exit_code == 0
    assert "CPU" in result.output

    # Verify that the config file was updated correctly
    with open(temp_config_file, "r") as f:
        config = json.load(f)
        assert config["gpuType"] == "cpu"
