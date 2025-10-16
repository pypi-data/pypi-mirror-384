import os
import json
import pathlib
from typing import Dict, Optional, Union


class LocalDevelopmentSettings:
    """Manages loading of local development settings from .env and JSON files.

    This class provides a standardized way to load configuration from
    .env files and Azure Functions-style `local.settings.json` files into
    environment variables, making local development environments consistent
    with deployed Azure environments.

    It supports overriding existing environment variables and provides clear
    output for loaded settings.
    """

    def __init__(
        self,
        service_name: str = "local_dev_settings",
        service_version: str = "1.0.0",
    ):
        """Initializes the LocalDevelopmentSettings manager.

        Args:
            service_name: The name of the service using the settings manager.
            service_version: The version of the service.
        """
        self.service_name = service_name
        self.service_version = service_version
        print(f"[{self.service_name}] LocalDevelopmentSettings initialized.")

    def load_from_dotenv(
        self,
        dotenv_path: Union[str, pathlib.Path],
        override: bool = False
    ) -> bool:
        """Loads key-value pairs from a .env file into environment variables.

        Args:
            dotenv_path: The path to the .env file.
            override: If True, existing environment variables will be overwritten.

        Returns:
            True if the file was loaded successfully, False otherwise.
        """
        dotenv_path = pathlib.Path(dotenv_path)
        if not dotenv_path.is_file():
            print(f"[{self.service_name}] WARNING: .env file not found at {dotenv_path}. Skipping.")
            return False

        try:
            with open(dotenv_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    parts = line.split("=", 1)
                    if len(parts) != 2:
                        continue

                    key, value = parts[0].strip(), parts[1].strip()
                    value = value.replace('"', "")

                    if key not in os.environ or override:
                        os.environ[key] = value
                        print(f"[{self.service_name}] DEBUG: Loaded from .env: {key}={value[:8]}...")
                    else:
                        print(f"[{self.service_name}] DEBUG: Skipping from .env (exists): {key}")

            print(f"[{self.service_name}] Successfully loaded settings from {dotenv_path}")
            return True
        except Exception as e:
            print(f"[{self.service_name}] ERROR: Error reading .env file at {dotenv_path}: {e}")
            return False

    def load_from_json(
        self,
        json_path: Union[str, pathlib.Path],
        override: bool = False
    ) -> bool:
        """Loads settings from a JSON file (e.g., local.settings.json).

        The JSON file is expected to have a "Values" key containing a
        dictionary of settings.

        Args:
            json_path: The path to the JSON settings file.
            override: If True, existing environment variables will be overwritten.

        Returns:
            True if the file was loaded successfully, False otherwise.
        """
        json_path = pathlib.Path(json_path)
        if not json_path.is_file():
            print(f"[{self.service_name}] WARNING: JSON settings file not found at {json_path}. Skipping.")
            return False

        try:
            with open(json_path, "r") as f:
                settings = json.load(f)

            if "Values" in settings and isinstance(settings["Values"], dict):
                for key, value in settings["Values"].items():
                    if key not in os.environ or override:
                        os.environ[key] = str(value)
                        print(f"[{self.service_name}] DEBUG: Loaded from JSON: {key}={str(value)[:8]}...")
                    else:
                        print(f"[{self.service_name}] DEBUG: Skipping from JSON (exists): {key}")
                print(f"[{self.service_name}] Successfully loaded settings from {json_path}")
                return True
            else:
                print(f"[{self.service_name}] WARNING: No 'Values' dictionary found in {json_path}. Skipping.")
                return False
        except json.JSONDecodeError:
            print(f"[{self.service_name}] ERROR: Error decoding JSON from {json_path}.")
            return False
        except Exception as e:
            print(f"[{self.service_name}] ERROR: Error reading JSON file at {json_path}: {e}")
            return False

    def apply_settings(
        self,
        settings: Dict[str, str],
        override: bool = True
    ):
        """Applies a dictionary of settings to the environment variables.

        Args:
            settings: A dictionary of key-value pairs to set as environment variables.
            override: If True, existing environment variables will be overwritten.
        """
        for key, value in settings.items():
            if key not in os.environ or override:
                os.environ[key] = str(value)
                print(f"[{self.service_name}] DEBUG: Applied setting: {key}={str(value)[:8]}...")
            else:
                print(f"[{self.service_name}] DEBUG: Skipping setting (exists): {key}")
        print(f"[{self.service_name}] Applied {len(settings)} settings to environment.")
    
    def print_settings(self):
        """Prints the current settings as a dictionary."""
        for key, value in os.environ.items():
            print(f"[{self.service_name}] DEBUG: Setting: {key}={value[:8]}...")
            

def create_local_env_manager(
    file_path: str = ".env",
    settings: Optional[Dict[str, str]] = None,
    override_json: bool = True,
    override_dotenv: bool = True,
    override_settings: bool = True
):
    """Convenience function to load settings from multiple sources.

    This function orchestrates loading settings from a `local.settings.json` file,
    a `.env` file, and a direct dictionary of settings, in that order.
    If the settings are not loaded from the file, the settings from the dictionary will not be applied.

    Args:
        file_path: Base path for `.env` or `local.settings.json`. The function
                   will look for both.
        settings: A dictionary of settings to apply.
        override_json: Whether settings from JSON should override existing env vars.
        override_dotenv: Whether settings from .env should override existing env vars.
        override_settings: Whether settings from the dictionary should override.
    """
    manager = LocalDevelopmentSettings()
    loadded_from_json = False
    loadded_from_dotenv = False
    # Try loading local.settings.json
    json_path = pathlib.Path(file_path).parent / "local.settings.json"
    if json_path.is_file():
        manager.load_from_json(json_path, override=override_json)
        loadded_from_json = True
    
    # Try loading .env
    dotenv_path = pathlib.Path(file_path)
    if dotenv_path.is_file() and dotenv_path.name == ".env":
        manager.load_from_dotenv(dotenv_path, override=override_dotenv)
        loadded_from_dotenv = True
        
    # Apply dictionary settings
    if settings and (loadded_from_json or loadded_from_dotenv):
        manager.apply_settings(settings, override=override_settings)
        
    return manager 