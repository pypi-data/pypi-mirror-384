import pytest
from unittest.mock import patch
import json


@pytest.fixture(scope="function", autouse=True)
def temp_credentials_file(tmp_path_factory):
    # Create a temporary directory using tmp_path_factory
    base_temp_path = tmp_path_factory.mktemp("data")
    credentials_dir = base_temp_path / ".thunder"
    credentials_dir.mkdir(mode=0o700)
    credentials_file = credentials_dir / "token"
    credentials_file.write_text("valid_token")

    # Patch get_credentials_file_path to return our temp file path
    with patch(
        "thunder.auth.get_credentials_file_path",
        return_value=str(credentials_file),
    ):
        yield credentials_file


@pytest.fixture(scope="function", autouse=True)
def temp_config_file(tmp_path_factory, temp_binary_file):
    # Create a temporary directory using tmp_path_factory
    base_temp_path = tmp_path_factory.mktemp("data")
    config_dir = base_temp_path / ".thunder"
    config_dir.mkdir(mode=0o700)
    config_file = config_dir / "config.json"

    # Write default config data into the file, using temp_binary_file's path for "binary"
    config_data = {
        "deploymentMode": "test",
        "instanceId": "0",
        "deviceId": "26",
        "gpuType": "t4",
        "gpuCount": 2,
        "binary": str(temp_binary_file),
        "managerAddress": "tcp://0.0.0.0:9000",
        "loggingAddress": "tcp://0.0.0.0:9001",
        "managerPublicKey": "k+P7>I2!MJx.(@?fOGDoHVXwzKep.t^3&nA0=r&i",
    }

    with open(config_file, "w") as f:
        json.dump(config_data, f)

    # Patch the config file path used by your application
    with patch("thunder.utils.CONFIG_PATH", new=str(config_file)):
        yield config_file


@pytest.fixture(scope="function", autouse=True)
def temp_binary_file(tmp_path_factory):
    # Create the binary file in a temporary directory
    base_temp_path = tmp_path_factory.mktemp("data")
    binary_file = base_temp_path / ".thunder" / "libthunder.so"
    binary_file.parent.mkdir(parents=True, exist_ok=True)
    binary_file.touch(mode=0o700)  # Creates an empty file with execute permissions

    yield binary_file
