#!/usr/bin/env python3

from util import BaseLog

from config import ConfigurationManager, SettingSection, SettingKeys
from paramiko.client import SSHClient, AutoAddPolicy


class FileList:
    def __init__(self, ls_output: list):
        self._raw = ls_output
        for line in ls_output:
            print(line)


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
        return stdout.readlines()

    @property
    def connected(self):
        return self._connected


class Server(BaseLog):
    def __init__(self, hostname):
        super().__init__(verbose=True)
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
        return FileList(self._ssh.run_command(r"ls -latr ~/files"))


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
        handler.add(ConfigurationManager().get(key=_key, section=SettingSection.WB))
    handler.get_file_list()


if __name__ == "__main__":
    main()
