import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock


# Test 1: Successful Instance Creation
@patch("thunder.utils.session.post")
def test_create_successful(mock_post, temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    # Mock the API response for a successful instance creation
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"uuid": "1234-5678", "key": "dummy_key_value"}
    mock_post.return_value = mock_response

    runner = CliRunner()
    result = runner.invoke(cli, ["create"])

    # Assert that the command was successful and output is as expected
    assert result.exit_code == 0


# Test 2: Instance Creation Failure
@patch("thunder.utils.session.post")
def test_create_failure(mock_post, temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    # Mock the API response for a failed instance creation
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Instance creation failed"
    mock_post.return_value = mock_response

    runner = CliRunner()
    result = runner.invoke(cli, ["create"])

    # Assert that the command failed and an appropriate error message is shown
    assert result.exit_code != 0
    assert "failed" in result.output.lower()


# Test 3: Exception Handling During Instance Creation
@patch("thunder.utils.session.post", side_effect=Exception("Network error"))
def test_create_exception_handling(mock_post, temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["create"])

    # Assert that the command failed and an appropriate error message is shown
    assert result.exit_code != 0
    assert "network error" in result.output.lower()
