import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock


# Test 1: Successful Instance Deletion
@patch("thunder.utils.session.post")
@patch("thunder.utils.remove_instance_from_ssh_config")
def test_delete_successful(
    mock_remove_ssh_config, mock_post, temp_credentials_file, temp_config_file
):
    from thunder.thunder import cli

    # Mock the API response for a successful deletion
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    runner = CliRunner()
    instance_id = "1234-5678"
    result = runner.invoke(cli, ["delete", instance_id])

    # Assert that the command was successful and output is as expected
    assert result.exit_code == 0

    # Assert that remove_instance_from_ssh_config was called correctly
    mock_remove_ssh_config.assert_called_once_with(f"tnr-{instance_id}")


# Test 2: Instance Deletion Failure
@patch("thunder.utils.session.post")
def test_delete_failure(mock_post, temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    # Mock the API response for a failed deletion
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Instance deletion failed due to invalid ID."
    mock_post.return_value = mock_response

    runner = CliRunner()
    instance_id = "invalid-id"
    result = runner.invoke(cli, ["delete", instance_id])

    # Assert that the command failed and an appropriate error message is shown
    assert result.exit_code != 0
    assert f"invalid id." in result.output.lower()


# Test 3: Exception Handling During Instance Deletion
@patch("thunder.utils.session.post", side_effect=Exception("Network error"))
def test_delete_exception_handling(mock_post, temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()
    instance_id = "1234-5678"
    result = runner.invoke(cli, ["delete", instance_id])

    # Assert that the command failed and an appropriate error message is shown
    assert result.exit_code != 0
    assert f"network error" in result.output.lower()
