import os
import json
import pytest
from unittest.mock import MagicMock, patch
import pathlib

from azpaddypy.mgmt.local_env_manager import LocalDevelopmentSettings, create_local_env_manager

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

def test_load_from_dotenv_success(temp_dir):
    dotenv_content = '''KEY1="VALUE1"
#COMMENT
KEY2=VALUE2'''
    dotenv_path = temp_dir / ".env"
    dotenv_path.write_text(dotenv_content)

    os.environ.pop("KEY1", None)
    os.environ.pop("KEY2", None)

    manager = LocalDevelopmentSettings()
    result = manager.load_from_dotenv(dotenv_path)

    assert result is True
    assert os.environ["KEY1"] == "VALUE1"
    assert os.environ["KEY2"] == "VALUE2"

def test_load_from_dotenv_override(temp_dir):
    dotenv_content = 'KEY1="NEW_VALUE"'
    dotenv_path = temp_dir / ".env"
    dotenv_path.write_text(dotenv_content)

    os.environ["KEY1"] = "OLD_VALUE"

    manager = LocalDevelopmentSettings()
    manager.load_from_dotenv(dotenv_path, override=True)
    assert os.environ["KEY1"] == "NEW_VALUE"

    manager.load_from_dotenv(dotenv_path, override=False)
    assert os.environ["KEY1"] == "NEW_VALUE"

def test_load_from_json_success(temp_dir):
    json_content = json.dumps({"Values": {"KEY1": "VALUE1", "KEY2": 42}})
    json_path = temp_dir / "local.settings.json"
    json_path.write_text(json_content)

    os.environ.pop("KEY1", None)
    os.environ.pop("KEY2", None)

    manager = LocalDevelopmentSettings()
    result = manager.load_from_json(json_path)

    assert result is True
    assert os.environ["KEY1"] == "VALUE1"
    assert os.environ["KEY2"] == "42"

def test_apply_settings():
    settings = {"KEY1": "VALUE1", "KEY2": "VALUE2"}
    os.environ.pop("KEY1", None)
    os.environ["KEY2"] = "OLD_VALUE"

    manager = LocalDevelopmentSettings()

    manager.apply_settings(settings, override=False)
    assert os.environ["KEY1"] == "VALUE1"
    assert os.environ["KEY2"] == "OLD_VALUE"

    manager.apply_settings(settings, override=True)
    assert os.environ["KEY1"] == "VALUE1"
    assert os.environ["KEY2"] == "VALUE2"

def test_create_local_env_manager(temp_dir):
    json_content = json.dumps({"Values": {"JSON_KEY": "JSON_VALUE"}})
    json_path = temp_dir / "local.settings.json"
    json_path.write_text(json_content)

    dotenv_content = "DOTENV_KEY=DOTENV_VALUE"
    dotenv_path = temp_dir / ".env"
    dotenv_path.write_text(dotenv_content)

    dict_settings = {"DICT_KEY": "DICT_VALUE"}

    create_local_env_manager(
        file_path=str(dotenv_path),
        settings=dict_settings
    )

    assert os.environ["JSON_KEY"] == "JSON_VALUE"
    assert os.environ["DOTENV_KEY"] == "DOTENV_VALUE"
    assert os.environ["DICT_KEY"] == "DICT_VALUE"

    # Clean up environment variables
    os.environ.pop("JSON_KEY", None)
    os.environ.pop("DOTENV_KEY", None)
    os.environ.pop("DICT_KEY", None) 