from pathlib import PurePosixPath, Path
from typing import Optional, List, Union
from dataclasses import dataclass
import time

from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

from base_log import BaseLog
from config import ConfigurationManager, SettingKeys, SettingSection
from wb.helper_methods import gen_find_cmd
from wb.list import FileList
from util import bytes_to_human_readable


@dataclass
class ConnectionSettings:
    use_rsa_key: bool = True
    use_password: bool = False
    use_system_scp: bool = True


def scp_progress_callback(filename, size, sent):
    _size = bytes_to_human_readable(size)
    _dl = bytes_to_human_readable(sent)
    print(f"\r{filename}: {_dl} / {_size}", end="")


class Server(BaseLog):
    class Connection(BaseLog):
        def __init__(self):
            BaseLog.__init__(self, use_global_settings=True)
            self._ssh_client = SSHClient()
            self._ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            self._connected = False
            self._used_password: Optional[bool] = None
            self._scp = None

        def _init_scp(self) -> bool:
            if not self._connected:
                self.error("need to be connected to init SCP")
                return False
            self._scp = SCPClient(self._ssh_client.get_transport(), progress=scp_progress_callback)
            self.log("SCP initialized")
            return True

        def connect(self, hostname, use_rsa_key: bool, username: Optional[str] = None, password: Optional[str] = None):
            self.set_log_prefix(f"SSH_CONN_{hostname.split('.')[0].upper()}")
            self.log(f"connecting to {hostname}...")
            try:
                self._ssh_client.connect(hostname, username=username, password=password, look_for_keys=use_rsa_key)
                self._connected = True
                self._used_password = self._ssh_client.get_transport().auth_handler.auth_method == "password"
                if self._used_password:
                    self.log("OK [connected using password]")
                else:
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
        def used_password_to_connect(self) -> bool:
            if not self._connected:
                return False
            if self._used_password is None:
                return False
            return self._used_password

        @property
        def scp(self) -> Optional[SCPClient]:
            if not self._scp:
                if not self._init_scp():
                    return None
            return self._scp

    def __init__(self, hostname: str, settings: ConnectionSettings):
        BaseLog.__init__(self, use_global_settings=True)
        if not hostname:
            self.error(f"invalid hostname: {hostname}")
            raise ValueError("hostname not valid")
        self._settings = settings
        self.set_log_prefix(f"{hostname.split('.')[0].upper()}")
        self._hostname = hostname
        self._user: Optional[str] = None
        self._ssh = self.Connection()
        self._connect()

    def _connect(self):
        if self._ssh.connected:
            self.log("already connected")
        if self._settings.use_password:
            _pw = ConfigurationManager().get(SettingKeys.WB_PASSWORD, section=SettingSection.WB)
        else:
            _pw = None
        self._user = ConfigurationManager().get(SettingKeys.WB_USERNAME, section=SettingSection.WB)
        self._ssh.connect(self._hostname, username=self._user, password=_pw, use_rsa_key=self._settings.use_rsa_key)

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
        if self._settings.use_system_scp:
            return self._download_with_system_scp(remote_path, local_path)
        _scp_client = self._ssh.scp
        if not _scp_client:
            return False
        self.log_fs(f"downloading i[{remote_path.name}]")
        _scp_client.get(str(remote_path), str(local_path), recursive=True)
        print()
        return True

    def _download_with_system_scp(self, remote_path: PurePosixPath, local_path: Path) -> bool:
        from run import local_command
        _cmd = f"scp -r {self._user}@{self._hostname}:\"{remote_path}\" {local_path}"
        return local_command(_cmd, hide_output=False)


class ServerHandler(BaseLog):
    def __init__(self, settings: ConnectionSettings):
        BaseLog.__init__(self, use_global_settings=True)
        self.set_log_prefix("ServerHandler")
        self._settings: ConnectionSettings = settings
        self._servers: List[Server] = []
        self._file_list: FileList = FileList()

    def add(self, hostname):
        self._servers.append(Server(hostname, settings=self._settings))

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
