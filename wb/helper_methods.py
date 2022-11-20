from pathlib import PurePosixPath
from typing import List

from config import ConfigurationManager, SettingKeys, SettingSection


def get_remote_files_path() -> PurePosixPath:
    _username = ConfigurationManager().get(SettingKeys.WB_USERNAME, section=SettingSection.WB)
    return PurePosixPath(f"/home/{_username}/files/")


def get_remote_tmp_dir() -> PurePosixPath:
    _username = ConfigurationManager().get(SettingKeys.WB_USERNAME, section=SettingSection.WB)
    return PurePosixPath(f"/home/{_username}/.tmp/")


def gen_find_cmd(extensions: List[str]):
    _files_path = get_remote_files_path()
    _cmd_str = f"find {_files_path} \\("
    for _ix, _ext in enumerate(extensions, 0):
        if _ix:
            _cmd_str += " -o"
        _cmd_str += f" -iname \"*.{_ext}\""
    return _cmd_str + " \\) -printf \"%T@ | %s | %p\\n\" | sort -n"


def parse_download_arg(download_arg: str, number_of_items: int):
    _ret = []
    _splits = download_arg.split(",")
    for _str in _splits:
        if _str.isnumeric():
            _ret.append(int(_str))
        elif _str.startswith("-"):
            _ret.extend(list(range(number_of_items + 1))[int(_str):])
        elif "-" in _str:
            if _str.replace("-", "").isnumeric():
                _start, _end = [int(ix) for ix in _str.split("-")]
                _ret.extend(range(_start, _end + 1))
        else:
            _ret.append(_str)
    return _ret
