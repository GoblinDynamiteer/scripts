import config


def test_config_get(tmp_path):
    _file = tmp_path / "_settings.txt"
    with open(_file, "w") as settings_file:
        settings_file.write("\n".join(["[default]", r"hue_ip=127.0.0.1", "", "[wb]", "password=abc123"]))
    cfg = config.ConfigurationManager(file_path=_file, verbose=False)
    cfg.set_config_file(_file)
    assert cfg.get(config.SettingKeys.IP_HUE) == "127.0.0.1"
    assert cfg.get(config.SettingKeys.WB_PASSWORD, section=config.SettingSection.WB) == "abc123"


def test_config_default(tmp_path):
    _file = tmp_path / "_settings.txt"
    with open(_file, "w") as settings_file:
        settings_file.write("\n".join(["[default]", r"hue_ip=127.0.0.1", "", "[wb]", "password=abc123"]))
    cfg = config.ConfigurationManager(file_path=_file, verbose=False)
    cfg.set_config_file(_file)
    assert cfg.get(config.SettingKeys.WB_USERNAME) is None
    assert cfg.get(config.SettingKeys.WB_USERNAME, default="user") == "user"


def test_config_convert(tmp_path):
    _file = tmp_path / "_settings.txt"
    with open(_file, "w") as settings_file:
        settings_file.write("\n".join(["[default]", r"hue_ip=127.0.0.1", "", "[wb]", "password=123"]))
    cfg = config.ConfigurationManager(file_path=_file, verbose=False)
    cfg.set_config_file(_file)
    assert cfg.get(config.SettingKeys.WB_PASSWORD, section=config.SettingSection.WB, convert=int) == 123
