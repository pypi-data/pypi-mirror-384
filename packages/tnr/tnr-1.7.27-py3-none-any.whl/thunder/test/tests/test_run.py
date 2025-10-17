import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
import os
import json


def test_run_no_arguments(temp_credentials_file, temp_config_file):
    from thunder.thunder import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["run"])

    assert result.exit_code != 0
    assert "argument" in result.output.lower()


@patch("thunder.thunder.get_latest", return_value=None)
@patch("thunder.thunder.requests.get")
@patch("thunder.thunder.os.execvp", return_value=None)
def test_run_failed_binary_download(
    mock_execvp,
    mock_requests_get,
    mock_get_latest,
    temp_credentials_file,
    temp_config_file,
    temp_binary_file,
):
    from thunder.thunder import cli

    # Delete the binary file if it exists
    temp_binary_file.unlink(missing_ok=True)

    # Mock the API response to simulate a valid user ID
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "test_uid"
    mock_requests_get.return_value = mock_response

    # Run the CLI command
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "echo", "Hello World"])

    # Assert that the command failed due to missing binary
    assert result.exit_code != 0
    assert "binary" in result.output.lower()


@patch("os.execvp", side_effect=FileNotFoundError)
@patch("thunder.thunder.get_latest")
@patch("thunder.thunder.requests.get")
def test_run_invalid_command(
    mock_requests_get,
    mock_get_latest,
    mock_execvp,
    temp_credentials_file,
    temp_config_file,
    temp_binary_file,
):
    from thunder.thunder import cli

    # Mock the API response to return a valid user ID and set binary path
    mock_get_latest.return_value = str(temp_binary_file)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "test_uid"
    mock_requests_get.return_value = mock_response

    runner = CliRunner()
    result = runner.invoke(cli, ["run", "nonexistentcommand"])

    assert result.exit_code != 0
    assert "command" in result.output.lower()


@patch("os.execvp")
@patch("thunder.thunder.get_latest")
@patch("thunder.thunder.requests.get")
def test_run_successful_command(
    mock_requests_get,
    mock_get_latest,
    mock_execvp,
    temp_credentials_file,
    temp_config_file,
    temp_binary_file,
):
    from thunder.thunder import cli

    mock_get_latest.return_value = str(temp_binary_file)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "test_uid"
    mock_requests_get.return_value = mock_response

    runner = CliRunner()
    with patch.dict(os.environ, {}, clear=True):
        result = runner.invoke(cli, ["run", "echo", "Hello World"])

        mock_execvp.assert_called_once_with("echo", ("echo", "Hello World"))
        assert os.environ["SESSION_USERNAME"] == "test_uid"
        assert os.environ["TOKEN"] == "valid_token"
        assert os.environ["__TNR_RUN"] == "true"
        assert os.environ["LD_PRELOAD"] == str(temp_binary_file)


@patch("os.execvp")
@patch("thunder.thunder.get_latest")
@patch("thunder.thunder.requests.get")
def test_run_warning_not_inside_instance(
    mock_requests_get,
    mock_get_latest,
    mock_execvp,
    temp_credentials_file,
    temp_config_file,
    temp_binary_file,
):
    import thunder.thunder
    from thunder.thunder import cli

    thunder.thunder.INSIDE_INSTANCE = False
    mock_get_latest.return_value = str(temp_binary_file)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "test_uid"
    mock_requests_get.return_value = mock_response

    runner = CliRunner()
    result = runner.invoke(cli, ["run", "echo", "Hello World"])

    assert "Attaching to a remote GPU from a non-managed instance" in result.output
    thunder.thunder.INSIDE_INSTANCE = True


@patch("os.execvp")
@patch("thunder.thunder.get_latest")
@patch("thunder.thunder.requests.get")
def test_run_no_warning_inside_instance(
    mock_requests_get,
    mock_get_latest,
    mock_execvp,
    temp_credentials_file,
    temp_config_file,
    temp_binary_file,
):
    import thunder.thunder
    from thunder.thunder import cli

    thunder.thunder.INSIDE_INSTANCE = True
    mock_get_latest.return_value = str(temp_binary_file)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "test_uid"
    mock_requests_get.return_value = mock_response

    runner = CliRunner()
    result = runner.invoke(cli, ["run", "echo", "Hello World"])

    assert "instance" not in result.output


@patch("os.execvp", side_effect=RuntimeError("Unexpected error"))
@patch("thunder.thunder.get_latest")
@patch("thunder.thunder.requests.get")
def test_run_exception_handling(
    mock_requests_get,
    mock_get_latest,
    mock_execvp,
    temp_credentials_file,
    temp_config_file,
    temp_binary_file,
):
    from thunder.thunder import cli

    mock_get_latest.return_value = str(temp_binary_file)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "test_uid"
    mock_requests_get.return_value = mock_response

    runner = CliRunner()
    result = runner.invoke(cli, ["run", "echo", "Hello World"])

    assert result.exit_code != 0
    assert "exception" in result.output.lower()


@patch("os.execvp")
@patch("thunder.thunder.get_latest")
@patch("thunder.thunder.requests.get")
def test_run_command_with_additional_arguments(
    mock_requests_get,
    mock_get_latest,
    mock_execvp,
    temp_credentials_file,
    temp_config_file,
    temp_binary_file,
):
    from thunder.thunder import cli

    mock_get_latest.return_value = str(temp_binary_file)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "test_uid"
    mock_requests_get.return_value = mock_response

    command_args = ("python", "script.py", "--arg", "value")

    runner = CliRunner()
    result = runner.invoke(cli, ("run",) + command_args)

    mock_execvp.assert_called_once_with("python", command_args)


@patch("os.execvp")
@patch("thunder.thunder.get_latest")
@patch("thunder.thunder.requests.get")
def test_run_ld_preload_already_set(
    mock_requests_get,
    mock_get_latest,
    mock_execvp,
    temp_credentials_file,
    temp_config_file,
    temp_binary_file,
):
    from thunder.thunder import cli

    os.environ["LD_PRELOAD"] = "/path/to/previous/lib.so"
    mock_get_latest.return_value = str(temp_binary_file)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "test_uid"
    mock_requests_get.return_value = mock_response

    runner = CliRunner()
    with patch.dict(os.environ, os.environ.copy(), clear=True):
        result = runner.invoke(cli, ("run", "echo", "Hello World"))

        assert os.environ["LD_PRELOAD"] == str(temp_binary_file)


@patch("os.execvp")
@patch("thunder.thunder.get_latest")
@patch("thunder.thunder.requests.get")
def test_run_device_cpu(
    mock_requests_get,
    mock_get_latest,
    mock_execvp,
    temp_credentials_file,
    temp_config_file,
):
    from thunder.thunder import cli

    # Modify the config to set gpuType to 'cpu'
    with open(temp_config_file, "r") as f:
        config = json.load(f)
    config["gpuType"] = "cpu"
    with open(temp_config_file, "w") as f:
        json.dump(config, f)

    # Mock the API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "test_uid"
    mock_requests_get.return_value = mock_response

    runner = CliRunner()
    with patch.dict(os.environ, {}, clear=True):
        result = runner.invoke(cli, ("run", "echo", "Hello World"))

        assert "LD_PRELOAD" not in os.environ
        mock_execvp.assert_called_once_with("echo", ("echo", "Hello World"))


@patch("os.execvp")
@patch("thunder.thunder.get_latest")
@patch("thunder.thunder.requests.get")
def test_run_device_not_cpu(
    mock_requests_get,
    mock_get_latest,
    mock_execvp,
    temp_credentials_file,
    temp_config_file,
    temp_binary_file,
):
    from thunder.thunder import cli

    # Ensure the gpuType is not 'cpu'
    with open(temp_config_file, "r") as f:
        config = json.load(f)
    config["gpuType"] = "t4"
    with open(temp_config_file, "w") as f:
        json.dump(config, f)

    mock_get_latest.return_value = str(temp_binary_file)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "test_uid"
    mock_requests_get.return_value = mock_response

    runner = CliRunner()
    with patch.dict(os.environ, {}, clear=True):
        result = runner.invoke(cli, ("run", "echo", "Hello World"))

        assert os.environ["LD_PRELOAD"] == str(temp_binary_file)
        mock_execvp.assert_called_once_with("echo", ("echo", "Hello World"))
