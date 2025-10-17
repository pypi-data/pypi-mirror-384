# test_status.py
import pytest
from click.testing import CliRunner
from unittest.mock import patch
import json


def test_status_with_instances_and_sessions(temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()

    with patch("thunder.utils.get_instances") as mock_get_instances, patch(
        "thunder.utils.get_active_sessions"
    ) as mock_get_active_sessions:

        # Mock get_instances to return some instances
        mock_get_instances.return_value = (
            True,
            None,
            {
                "instance_1": {
                    "status": "RUNNING",
                    "ip": "192.168.1.1",
                    "createdAt": "2023-10-01",
                },
                "instance_2": {
                    "status": "STOPPED",
                    "ip": None,
                    "createdAt": "2023-10-02",
                },
            },
        )

        # Mock get_active_sessions to return some sessions
        mock_get_active_sessions.return_value = [
            {"count": 2, "gpu": "A100", "duration": 3600}
        ]

        # Invoke the command 'tnr status'
        result = runner.invoke(cli, ["status"])

        # Assert that the command executed successfully
        assert result.exit_code == 0
        output = result.output

        # Check that the output contains expected information
        assert "Thunder Compute Instances" in output
        assert "instance_1" in output
        assert "instance_2" in output
        assert "RUNNING" in output
        assert "STOPPED" in output
        assert "192.168.1.1" in output
        assert "2023-10-01" in output
        assert "Active GPU Processes" in output
        assert "A100" in output
        assert "3600s" in output


def test_status_no_instances_or_sessions(temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()

    with patch("thunder.utils.get_instances") as mock_get_instances, patch(
        "thunder.utils.get_active_sessions"
    ) as mock_get_active_sessions:

        # Mock get_instances to return no instances
        mock_get_instances.return_value = (True, None, {})
        # Mock get_active_sessions to return no sessions
        mock_get_active_sessions.return_value = []

        # Invoke the command 'tnr status'
        result = runner.invoke(cli, ["status"])

        # Assert that the command executed successfully
        assert result.exit_code == 0
        output = result.output

        # Check that the output indicates no instances or sessions
        assert "Thunder Compute Instances" in output
        assert "--" in output  # Placeholder for no instances
        assert "Active GPU Processes" in output
        assert "--" in output  # Placeholder for no sessions


def test_status_get_instances_failure(temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()

    with patch("thunder.utils.get_instances") as mock_get_instances:
        # Mock get_instances to return failure
        mock_get_instances.return_value = (False, "Error message", None)

        # Invoke the command 'tnr status'
        result = runner.invoke(cli, ["status"])

        # Assert that the command failed and the error message is displayed
        assert result.exit_code != 0
