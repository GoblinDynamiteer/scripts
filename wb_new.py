#!/usr/bin/env python3

from pathlib import Path
from typing import List
from enum import Enum

from util import BaseLog
from config import ConfigurationManager, SettingSection, SettingKeys

from paramiko.client import SSHClient, AutoAddPolicy


def get_remote_files_path() -> Path:
    _username = ConfigurationManager().get(SettingKeys.WB_USERNAME, section=SettingSection.WB)
    return Path(f"/home/{_username}/files/")


def gen_find_cmd(extensions: List[str]):
    _files_path = get_remote_files_path()
    _cmd_str = f"find {_files_path} \\("
    for _ix, _ext in enumerate(extensions, 0):
        if _ix:
            _cmd_str += " -o"
        _cmd_str += f" -iname \"*.{_ext}\""
    return _cmd_str + " \\) -printf \"%T@ | %s | %p\\n\" | sort -n"


class FileListItem(BaseLog):
    _ignore = ["sample", "subs"]

    def __init__(self, string: str):
        BaseLog.__init__(self, verbose=True)
        self.set_log_prefix("ITEM")
        self._raw = string.replace("\n", "").strip()
        self._index = None
        self._parse()

    def _parse(self):
        self.log(f"parsing {self._raw}")
        self._valid = False
        try:
            _stamp, _bytes, _path = self._raw.split(" | ")
        except ValueError as _:
            self.error(f"could not split line: {self._raw}",
                       error_prefix="parse_error")
            return
        self._path = Path(_path)
        _files_path = get_remote_files_path()
        if not self._path.is_relative_to(_files_path):
            self.error(f"path {self._path} is not relative to: {_files_path}",
                       error_prefix="parse_error")
            return
        if not _bytes.isdigit():
            self.error(f"bytes value: {_bytes} is not an integer!",
                       error_prefix="parse_error")
            return
        self._bytes = int(_bytes)
        try:
            self._timestamp = int(_stamp.split(".")[0])
        except ValueError as _:
            self.error(f"could not parse timestamp from: {_stamp}",
                       error_prefix="parse_error")
            return
        self._valid = True

    @property
    def index(self) -> [int, None]:
        return self._index

    @index.setter
    def index(self, index_val: int):
        self._index = index_val

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def path(self):
        return self._path

    @property
    def is_video(self) -> bool:
        return self._path.suffix == ".mkv"

    @property
    def is_rar(self) -> bool:
        return self._path.suffix == ".rar"

    @property
    def size(self) -> int:
        return self._bytes

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @property
    def valid(self):
        if not self._valid:
            return False
        if any([_i in self.name for _i in self._ignore]):
            return False
        return True


class FileList:
    def __init__(self, start_index=1):
        self._items: List[FileListItem] = []
        self._index = start_index

    def last_index(self) -> int:
        return self._index

    def parse_find_cmd_output(self, lines: List[str]):
        for line in lines:
            _item = FileListItem(line)
            if _item.valid:
                _item.index = self._index
                self._index += 1
                self._items.append(_item)

    def print(self):
        for item in self._items:
            self.print_item(item)

    def print_item(self, item: FileListItem):
        print(item.index, item.path)


class SSHConnection(BaseLog):
    def __init__(self):
        super().__init__(verbose=True)
        self._client = SSHClient()
        self._client.set_missing_host_key_policy(AutoAddPolicy())
        self._connected = False

    def connect(self, hostname, username=None, password=None):
        self.set_log_prefix(f"SSH_CONN_{hostname.split('.')[0].upper()}")
        self.log(f"connecting to {hostname}...")
        try:
            self._client.connect(hostname, username=username, password=password)
            self._connected = True
            self.log("OK")
        except Exception as error:
            self.error(f"FAIL: {error}")
            self._connected = False

    def run_command(self, command):
        if not self._connected:
            return None
        _, stdout, _ = self._client.exec_command(command)
        try:
            return stdout.readlines()
        except AttributeError as _:
            if isinstance(stdout, str):
                return stdout.split("\n")
        return None

    @property
    def connected(self):
        return self._connected


class Server(BaseLog):
    def __init__(self, hostname):
        super().__init__(verbose=True)
        if not hostname:
            self.error(f"invalid hostname: {hostname}")
            raise ValueError("hostname not valid")
        self.set_log_prefix(f"{hostname.split('.')[0].upper()}")
        self._hostname = hostname
        self._ssh = SSHConnection()
        self._connect()
        self._file_list = None

    def _connect(self):
        if self._ssh.connected:
            self.log("already connected")
        _user = ConfigurationManager().get(SettingKeys.WB_USERNAME, section=SettingSection.WB)
        _pw = ConfigurationManager().get(SettingKeys.WB_PASSWORD, section=SettingSection.WB)
        self._ssh.connect(self._hostname, username=_user, password=_pw)

    def get_file_list(self, start_index=1) -> [FileList, None]:
        if self._file_list:
            return self._file_list
        if not self._ssh.connected:
            self.error("cannot retrieve file list, not connected")
            return None
        _file_list = FileList(start_index=start_index)
        _cmd = gen_find_cmd(extensions=["mkv", "rar"])
        _file_list.parse_find_cmd_output(self._ssh.run_command(_cmd))
        _file_list.print()
        return _file_list


class ServerHandler:
    def __init__(self):
        self._servers : List[Server] = []

    def add(self, hostname):
        self._servers.append(Server(hostname))

    def print_file_list(self):
        start_index = 1
        file_lists = []
        for server in self._servers:
            file_list = server.get_file_list(start_index=start_index)
            file_lists.append(file_list)
            start_index = file_list.last_index() + 1
        for file_list in file_lists:
            file_list.print()


def main():
    handler = ServerHandler()
    for _key in [SettingKeys.WB_SERVER_1, SettingKeys.WB_SERVER_2]:
        _hostname = ConfigurationManager().get(key=_key, section=SettingSection.WB)
        if _hostname:
            handler.add(_hostname)
        else:
            print(f"could not get hostname (key {_key.value}) from settings")
    handler.print_file_list()


if __name__ == "__main__":
    main()
