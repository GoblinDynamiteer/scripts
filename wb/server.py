from pathlib import PurePosixPath, Path
from typing import Optional, List, Union

from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

from base_log import BaseLog
from config import ConfigurationManager, SettingKeys, SettingSection
from wb.helper_methods import gen_find_cmd
from wb.list import FileList


class Server(BaseLog):
    class Connection(BaseLog):
        def __init__(self):
            BaseLog.__init__(self, use_global_settings=True)
            self._ssh_client = SSHClient()
            self._ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            self._connected = False
            self._scp = None

        @staticmethod
        def _scp_progress_callback(filename, size, sent):
            print(filename, size, sent)

        def _init_scp(self) -> bool:
            if not self._connected:
                self.error("need to be connected to init SCP")
                return False
            self._scp = SCPClient(self._ssh_client.get_transport(), progress=self._scp_progress_callback)
            self.log("SCP initialized")
            return True

        def connect(self, hostname, username=None, password=None):
            self.set_log_prefix(f"SSH_CONN_{hostname.split('.')[0].upper()}")
            self.log(f"connecting to {hostname}...")
            try:
                self._ssh_client.connect(hostname, username=username, password=password, look_for_keys=False)
                self._connected = True
                self.log("OK")
            except Exception as error:
                self.error(f"FAIL: {error}")
                self._connected = False

        def run_command(self, command):
            if not self._connected:
                return None
            _, stdout, _ = self._ssh_client.exec_command(command)
            try:
                return stdout.readlines()
            except AttributeError as _:
                if isinstance(stdout, str):
                    return stdout.split("\n")
            return None

        @property
        def connected(self):
            return self._connected

        @property
        def scp(self) -> Optional[SCPClient]:
            if not self._scp:
                if not self._init_scp():
                    return None
            return self._scp

    def __init__(self, hostname):
        BaseLog.__init__(self, use_global_settings=True)
        if not hostname:
            self.error(f"invalid hostname: {hostname}")
            raise ValueError("hostname not valid")
        self.set_log_prefix(f"{hostname.split('.')[0].upper()}")
        self._hostname = hostname
        self._ssh = self.Connection()
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
        _cmd = gen_find_cmd(extensions=["mkv", "rar"])
        return self._ssh.run_command(_cmd)

    @property
    def hostname(self):
        return self._hostname

    @property
    def connected(self) -> bool:
        return self._ssh.connected

    def download_with_scp(self, remote_path: PurePosixPath, local_path: Path) -> bool:
        _scp_client = self._ssh.scp
        if not _scp_client:
            return False
        _scp_client.get(str(remote_path), str(local_path), recursive=True)


class ServerHandler(BaseLog):
    def __init__(self):
        BaseLog.__init__(self, use_global_settings=True)
        self.set_log_prefix("ServerHandler")
        self._servers: List[Server] = []
        self._file_list: FileList = FileList()

    def add(self, hostname):
        self._servers.append(Server(hostname))

    def print_file_list(self):
        if self._file_list.empty():
            self._init_file_list()
        self._file_list.print()

    def _init_file_list(self):
        self.log("gathering item from server(s)")
        for server in self._servers:
            self._file_list.parse_find_cmd_output(server.list_files(), server_id=server.hostname)
        self.log(f"found {len(self._file_list)} number of items")

    def download(self, key: Union[str, int], destination: Path) -> bool:
        if self._file_list.empty():
            self._init_file_list()
        _item = self._file_list.get(key)
        if not _item:
            print(f"could not retrieve item with key: {key}")
            return False
        for server in self._servers:
            if server.hostname == _item.server_id:
                server.download_with_scp(_item.download_path, destination)

    def valid(self) -> bool:
        for server in self._servers:
            if server.connected:
                return True
        return False
