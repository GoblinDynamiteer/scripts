#!/usr/bin/env python3

from pathlib import Path
from typing import List
from enum import Enum

from util import BaseLog
from config import ConfigurationManager, SettingSection, SettingKeys

from paramiko.client import SSHClient, AutoAddPolicy


class FileListItem:
    class ItemType(Enum):
        Dir = "directory"
        File = "File"

    _ignore_dirs = ["Sample", "Proof", "Subs"]
    _valid_file_ext = [".mkv", ".rar"]

    def __init__(self, string: str, item_type: ItemType):
        self._type = item_type
        self._raw = string.replace("\n", "").strip()
        self._path = Path(self._raw)
        self._sub_items = []
        _user = ConfigurationManager().get(key=SettingKeys.WB_USERNAME, section=SettingSection.WB)
        self._top_level = Path("/home/") / _user / "files"

    def add_sub_item(self, item):
        self._sub_items.append(item)

    def sub_items(self):
        for item in self._sub_items:
            yield item

    def is_parent_of(self, other: "FileListItem"):
        if other.is_top_level():
            return False
        if self.is_file:
            return False
        return self._path == other.parent()

    def is_relative_of(self, other: "FileListItem"):
        if other.is_top_level():
            return False
        if self.is_file:
            return False
        try:
            return other.path.is_relative_to(self._path)
        except AttributeError as _:
            pass
        return str(other).startswith(str(self))

    def is_top_level(self):
        return self._path.parent == self._top_level

    @property
    def is_dir(self):
        return self._type == self.ItemType.Dir

    @property
    def is_file(self):
        return self._type == self.ItemType.File

    @property
    def valid(self):
        if self.is_dir:
            if self._path == self._top_level:
                return False
            if self._path.name in self._ignore_dirs:
                return False
        if self.is_file:
            if self._path.suffix not in self._valid_file_ext:
                return False
            if self.parent().name in self._ignore_dirs:
                return False
        return True

    def __str__(self):
        _ret = str(self._path).replace(f"{self._top_level}/", "")
        if self.is_dir and not _ret.endswith("/"):
            return f"{_ret}/"
        return _ret

    @property
    def name(self) -> str:
        return self._path.name

    def parent(self):
        return self._path.parent

    @property
    def path(self):
        return self._path


class FileList:
    def __init__(self):
        self._items: List[FileListItem] = []

    def parse_find_d_output(self, lines: List[str]):
        for line in lines:
            self._add_item(FileListItem(line, item_type=FileListItem.ItemType.Dir))

    def parse_find_f_output(self, lines: List[str]):
        for line in lines:
            self._add_item(FileListItem(line, item_type=FileListItem.ItemType.File))

    def _add_item(self, item: FileListItem):
        if not item.valid:
            return
        if item.is_top_level():
            self._items.append(item)
            return
        _parent = self._get_parent_item(self._items, item)
        if _parent is not None:
            _parent.add_sub_item(item)
        else:
            self._items.append(item)

    def _get_parent_item(self, items: List[FileListItem], item: FileListItem) -> [FileListItem, None]:
        for _item in items:
            if _item.is_parent_of(item):
                return _item
            if _item.is_relative_of(item):
                return self._get_parent_item(list(_item.sub_items()), item)
        return None

    def print(self):
        for item in self._items:
            self.print_item(item)

    def print_item(self, item: FileListItem, indent=0):
        prefix = "[DIR]" if item.is_dir else "[FIL]"
        print(prefix + " " * indent, item.name)
        for sub_item in item.sub_items():
            self.print_item(sub_item, indent+4)


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

    def _connect(self):
        if self._ssh.connected:
            self.log("already connected")
        _user = ConfigurationManager().get(SettingKeys.WB_USERNAME, section=SettingSection.WB)
        _pw = ConfigurationManager().get(SettingKeys.WB_PASSWORD, section=SettingSection.WB)
        self._ssh.connect(self._hostname, username=_user, password=_pw)

    def list_files(self) -> [FileList, None]:
        if not self._ssh.connected:
            self.error("cannot retrieve file list, not connected")
            return None
        _file_list = FileList()
        _file_list.parse_find_d_output(self._ssh.run_command(r"find ~/files -type d"))
        _file_list.parse_find_f_output(self._ssh.run_command(r"find ~/files -type f"))
        _file_list.print()
        return _file_list


class ServerHandler:
    def __init__(self):
        self._servers = []

    def add(self, hostname):
        self._servers.append(Server(hostname))

    def get_file_list(self):
        for _server in self._servers:
            _server.list_files()


def main():
    handler = ServerHandler()
    for _key in [SettingKeys.WB_SERVER_1, SettingKeys.WB_SERVER_2]:
        _hostname = ConfigurationManager().get(key=_key, section=SettingSection.WB)
        if _hostname:
            handler.add(_hostname)
        else:
            print(f"could not get hostname (key {_key.value}) from settings")
    handler.get_file_list()


if __name__ == "__main__":
    main()
