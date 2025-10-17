import pytest
from click.testing import CliRunner
from unittest.mock import patch
import os
import json


def test_login_success(temp_credentials_file, temp_config_file):
    from thunder.thunder import login
    
    # Use CliRunner to invoke the login command with a mocked token input
    runner = CliRunner()
    token_value = "valid_token"
    result = runner.invoke(login, input=f"{token_value}\n")
    assert result.exit_code == 0
    # Assert that the credentials file contains the correct token
    assert temp_credentials_file.exists()
    with open(temp_credentials_file, "r") as f:
        assert f.read().strip() == token_value

    # Assert that the config file was used
    assert temp_config_file.exists()
    with open(temp_config_file, "r") as f:
        config = json.load(f)
        assert config["deviceId"] == "26"


def test_login_failure(temp_credentials_file, temp_config_file):
    from thunder.thunder import login

    # Ensure the credentials file does not exist initially
    if temp_credentials_file.exists():
        temp_credentials_file.unlink()

    # Use CliRunner to invoke the login command with an invalid token input
    runner = CliRunner()
    result = runner.invoke(
        login,
        input="invalid_token\ninvalid_token\ninvalid_token\ninvalid_token\ninvalid_token\n",
    )

    # Assert failed login
    assert result.exit_code != 0

    # Assert that the credentials file does not exist since login failed
    assert not temp_credentials_file.exists()


def test_logout(temp_credentials_file, temp_config_file):
    from thunder.thunder import logout

    # Write a dummy token to the file to simulate a pre-existing file
    temp_credentials_file.write_text("dummy_token")

    # Assert that the file exists before the logout command
    assert temp_credentials_file.exists()

    # Use CliRunner to invoke the logout command
    runner = CliRunner()
    result = runner.invoke(logout)

    # Assert successful logout
    assert result.exit_code == 0
    assert "out" in result.output.lower()

    # Assert that the credentials file no longer exists after logout
    assert not temp_credentials_file.exists()
