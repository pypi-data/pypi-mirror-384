import os
import json
from enum import Enum
from typing import Dict, Any, Union

import click
import requests
import platform
BASEURL = "https://api.thundercompute.com:8443"

# For debug mode
if os.environ.get('API_DEBUG_MODE') == "1":
    BASEURL = 'http://localhost:8443'

class RuntimeConfig:
    class InstallationType(Enum):
        LOCAL = 0
        GLOBAL = 1
        
    class System(Enum):
        WINDOWS = 0
        LINUX = 1
        MACOS = 2

    def __init__(self):
        self.installation_type : RuntimeConfig.InstallationType = None
        self.library_path: str = None
        self.system: RuntimeConfig.System = None

class Config:
    _instance = None
    _initialized: bool = False
    runtime: RuntimeConfig = RuntimeConfig()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def setup(self, token) -> None:
        self._initialized = True
        self.config: Dict[str, Union[int, str]] = {}
        
        system = platform.system()
        if system == "Linux":
            self.runtime.system = RuntimeConfig.System.LINUX
        elif system == "Windows":
            self.runtime.system = RuntimeConfig.System.WINDOWS
        elif system == "Darwin":
            self.runtime.system = RuntimeConfig.System.MACOS
        else:
            raise click.ClickException(f"Unsupported platform: {system}")
        
        # Try /etc/thunder/config.json first
        if self.runtime.system == RuntimeConfig.System.LINUX and os.geteuid() == 0:
            # For root try to user the config of the original user
            sudo_user = os.environ.get('SUDO_USER')
            if sudo_user is None:
                home_dir = "~"
            else:
                home_dir = f"~{sudo_user}"
        else:
            home_dir = "~"
        user_config: str = os.path.join(os.path.expanduser(home_dir), ".thunder", "config.json")

        success = False
        
        # Global config only supported on Linux
        if self.runtime.system == RuntimeConfig.System.LINUX:
            system_config: str = "/etc/thunder/config.json"
            if os.path.exists(system_config):
                try:
                    with open(system_config, "r") as f:
                        self.config = json.load(f)
                        self.file = system_config
                        self.runtime.installation_type = RuntimeConfig.InstallationType.GLOBAL
                        success = True
                except Exception as e:
                    pass
        
        if not success and os.path.exists(user_config):
            try:
                with open(user_config, "r") as f:
                    self.config = json.load(f)
                    self.file = user_config
                    self.runtime.installation_type = RuntimeConfig.InstallationType.LOCAL
                    success = True
            except Exception as e:
                pass
        
        if not success:
            self._create_default_config(user_config, token)
            self.file = user_config
            self.runtime.installation_type = RuntimeConfig.InstallationType.LOCAL
            
        if self.runtime.installation_type == RuntimeConfig.InstallationType.GLOBAL:
            self.runtime.library_path = "/etc/thunder/libthunder.so"
        else:
            self.runtime.library_path = os.path.expanduser("~/.thunder/libthunder.so")
                    
    @staticmethod
    def get_default(token) -> Dict[str, Union[int, str]]:
        try:
            endpoint = f"{BASEURL}/next_id"
            response = requests.get(
                endpoint, headers={"Authorization": f"Bearer {token}"}
            )
            device_id = response.json()["id"]
        except Exception as e:
            raise click.ClickException(f"Failed to create default config: {e}")
        
        config = {
            "instanceId": -1,
            "deviceId": str(device_id),
            "gpuType": "t4",
            "gpuCount": 1,
        }
        return config

    def _create_default_config(self, path:str, token: str) -> None:
        """Create default config file in ~/.thunder/config.json"""
        
        os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)        
        self.config = Config.get_default(token)
        with open(path, "w") as f:
            json.dump(self.config, f, indent=4)

    def _check_initialized(self):
        if not self._initialized:
            raise click.ClickException("Config used before initialization")

    def get(self, key, default=None):
        self._check_initialized()
        return self.config.get(key, default)
    
    def getX(self, key):
        self._check_initialized()
        if key not in self.config:
            raise click.ClickException(f"Config error: {key} not found in {self.file}")
        return self.config.get(key)
    
    def contains(self, key):
        self._check_initialized()
        return key in self.config
    
    def set(self, key, value):
        self._check_initialized()
        self.config[key] = value
        
    def save(self):
        self._check_initialized()
        try:
            with open(self.file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            raise click.ClickException(f"Failed to save config to {self.file}: {e}")
