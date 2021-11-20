from pathlib import Path

import pytest

import config


class TestConfigurationManager:
    _cfg = config.ConfigurationManager(verbose=False)

    def _update(self, config_file: Path):
        self._cfg.set_config_file(config_file)
        self._cfg._load()

    def test_config_get(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", r"hue_ip=127.0.0.1", "", "[wb]", "password=abc123"]))
        self._update(_file)
        assert self._cfg.get(config.SettingKeys.IP_HUE) == "127.0.0.1"
        assert self._cfg.get(config.SettingKeys.WB_PASSWORD, section=config.SettingSection.WB) == "abc123"

    def test_config_default(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", r"hue_ip=127.0.0.1", "", "[wb]", "password=abc123"]))
        self._update(_file)
        assert self._cfg.get(config.SettingKeys.WB_USERNAME) is None
        assert self._cfg.get(config.SettingKeys.WB_USERNAME, default="user") == "user"

    def test_config_convert(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", r"hue_ip=127.0.0.1", "", "[wb]", "password=123"]))
        self._update(_file)
        assert self._cfg.get(config.SettingKeys.WB_PASSWORD, section=config.SettingSection.WB, convert=int) == 123

    def test_config_raises_error_with_wrong_key_type(self):
        with pytest.raises(TypeError):
            _ = self._cfg.path(123)

    def test_config_path_str(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db.name}"]))
        self._update(_file)
        assert self._cfg.path("movdb") == _db.name

    def test_config_path_str_convert_to_path(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        _db.touch()
        assert _db.exists()
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db}"]))
        self._update(_file)
        assert self._cfg.path("movdb", convert_to_path=True) == _db

    def test_config_path_str_exists(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        _db.touch()
        assert _db.exists()
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db}"]))
        self._update(_file)
        self._cfg.path("movdb", assert_path_exists=True)

    def test_config_path_str_not_exists_raises_error(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        assert not _db.exists()
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db}"]))
        self._update(_file)
        with pytest.raises(AssertionError):
            self._cfg.path("movdb", assert_path_exists=True)

    def test_config_path_str_prefixed_with_path(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db.name}"]))
        self._update(_file)
        assert self._cfg.path("path_movdb") == _db.name

    def test_config_path_str_prefixed_with_path_convert_to_path(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        _db.touch()
        assert _db.exists()
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db}"]))
        self._update(_file)
        assert self._cfg.path("path_movdb", convert_to_path=True) == _db

    def test_config_path_str_prefixed_with_path_exists(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        _db.touch()
        assert _db.exists()
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db}"]))
        self._update(_file)
        self._cfg.path("path_movdb", assert_path_exists=True)

    def test_config_path_str_prefixed_with_path_not_exists_raises_error(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        assert not _db.exists()
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db}"]))
        self._update(_file)
        with pytest.raises(AssertionError):
            self._cfg.path("path_movdb", assert_path_exists=True)

    def test_config_path_key_enum(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db.name}"]))
        self._update(_file)
        assert self._cfg.path(config.SettingKeys.PATH_MOVIE_DATABASE) == _db.name

    def test_config_path_key_enum_convert_to_path(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        _db.touch()
        assert _db.exists()
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db}"]))
        self._update(_file)
        assert self._cfg.path(config.SettingKeys.PATH_MOVIE_DATABASE, convert_to_path=True) == _db

    def test_config_path_key_enum_exists(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        _db.touch()
        assert _db.exists()
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db}"]))
        self._update(_file)
        self._cfg.path(config.SettingKeys.PATH_MOVIE_DATABASE, assert_path_exists=True)

    def test_config_path_key_enum_not_exists_raises_error(self, tmp_path):
        _file = tmp_path / "_settings.txt"
        _db = tmp_path / "_db_file.json"
        assert not _db.exists()
        with open(_file, "w") as settings_file:
            settings_file.write("\n".join(["[default]", f"path_movdb={_db}"]))
        self._update(_file)
        with pytest.raises(AssertionError):
            self._cfg.path(config.SettingKeys.PATH_MOVIE_DATABASE, assert_path_exists=True)
