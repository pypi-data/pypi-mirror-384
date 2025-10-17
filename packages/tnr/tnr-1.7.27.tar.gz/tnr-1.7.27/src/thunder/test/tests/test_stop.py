import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock


# Test 1: Successful Instance Stop
@patch("thunder.utils.session.post")
def test_stop_successful(mock_post, temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    # Mock the API response for a successful instance stop
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    runner = CliRunner()
    instance_id = "test_instance_id"
    result = runner.invoke(cli, ["stop", instance_id])

    # Assert that the command was successful and output is as expected
    assert result.exit_code == 0
    assert f"success" in result.output.lower()


# Test 2: Instance Stop Failure
@patch("thunder.utils.session.post")
def test_stop_failure(mock_post, temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    # Mock the API response for a failed instance stop
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Stop failed"
    mock_post.return_value = mock_response

    runner = CliRunner()
    instance_id = "test_instance_id"
    result = runner.invoke(cli, ["stop", instance_id])

    # Assert that the command failed and an appropriate error message is shown
    assert result.exit_code != 0
    assert f"fail" in result.output.lower()


# Test 3: Exception Handling During Instance Stop
@patch("thunder.utils.session.post", side_effect=Exception("Network error"))
def test_stop_exception_handling(mock_post, temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()
    instance_id = "test_instance_id"
    result = runner.invoke(cli, ["stop", instance_id])

    # Assert that the command failed and an appropriate error message is shown
    assert result.exit_code != 0
    assert f"network" in result.output.lower()
