from pathlib import PurePosixPath, Path
from typing import Optional, List, Union, Callable

from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

from base_log import BaseLog
from config import ConfigurationManager, SettingKeys, SettingSection
from util import bytes_to_human_readable
from utils.external_app_utils import UnrarOutputParser
from utils.dir_util import DirectoryInfo
from utils.file_utils import FileInfo

from wb.helper_methods import gen_find_cmd, get_remote_tmp_dir
from wb.list import FileList
from wb.settings import WBSettings


def scp_progress_callback(filename, size, sent) -> None:
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

        def run_command(self, command: str,
                        read_line_cb: Optional[Callable[[str], None]] = None) -> Optional[List[str]]:
            if not self._connected:
                return None
            _, stdout, _ = self._ssh_client.exec_command(command, get_pty=True)
            _ret = []
            for line in iter(stdout.readline, ""):
                _ret.append(line)
                if read_line_cb:
                    read_line_cb(line)
            return _ret

        @property
        def connected(self) -> bool:
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

    def __init__(self, hostname: str, settings: WBSettings):
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
    def hostname(self) -> str:
        return self._hostname

    @property
    def connected(self) -> bool:
        return self._ssh.connected

    def download_with_scp(self, remote_path: PurePosixPath, local_path: Path) -> bool:
        if self._settings.use_system_scp:
            return self._download_with_system_scp(remote_path, local_path)
        if not (_scp_client := self._ssh.scp):
            return False
        self.log_fs(f"downloading i[{remote_path.name}]")
        _scp_client.get(str(remote_path), str(local_path), recursive=True)
        print()
        return True

    def remove_directory(self, remote_path: PurePosixPath, raise_if_nontmp: bool = True) -> None:
        if not self.connected:
            return
        _tmp = get_remote_tmp_dir()
        if not remote_path.is_relative_to(_tmp) and raise_if_nontmp:
            raise RuntimeError("Will not attempt to remove non-temp directory!")
        self.log_fs(f"removing: w[{remote_path}]")
        self._ssh.run_command(f"rm -r {remote_path}")

    def extract_to_temp_dir(self, rar_file_path: PurePosixPath,
                            dest_path: Optional[PurePosixPath] = None) -> PurePosixPath:
        if not self._ssh.connected:
            raise ConnectionError("Not connected to server! Cannot do extract operation!")
        if dest_path is None:
            _cmd = f"unrar e {rar_file_path} $(mktemp -d --tmpdir={get_remote_tmp_dir()})"
        else:
            _cmd = f"unrar e {rar_file_path} {dest_path}"

        parser = UnrarOutputParser()

        def _cb(line: str):
            if parser.parse_output(line):
                _str = parser.to_current_status_string()
                if not _str:
                    return
                print(_str, end="")

        self._ssh.run_command(_cmd, read_line_cb=_cb)
        if parser.destination is None or not parser.current_file:
            raise RuntimeError("could not determine destination of extracted file(s)")
        if len(parser.extracted_files) != 1:
            self.warn_fs("extracted more than one file!")
        return PurePosixPath(parser.destination / parser.current_file)

    def _download_with_system_scp(self, remote_path: PurePosixPath, local_path: Path) -> bool:
        from run import local_command
        _remote = str(remote_path)
        _local_dest = str(local_path)
        # Make sure to escape spaces
        _remote = _remote.replace(" ", r"\ ")
        _local_dest = _local_dest.replace(" ", r"\ ")
        _cmd = f"scp -r {self._user}@{self._hostname}:\"{_remote}\" \"{local_path}\""
        return local_command(_cmd, hide_output=False)


class ServerHandler(BaseLog):
    def __init__(self, settings: WBSettings):
        BaseLog.__init__(self, use_global_settings=True)
        self.set_log_prefix("ServerHandler")
        self._settings: WBSettings = settings
        self._servers: List[Server] = []
        self._file_list: FileList = FileList()

    def add(self, hostname: str) -> None:
        self._servers.append(Server(hostname, settings=self._settings))

    def print_file_list(self) -> None:
        if self._file_list.empty():
            self._init_file_list()
        self._file_list.print(show_additional_info=self._settings.show_extra_info)

    def _init_file_list(self) -> None:
        self.log("gathering item from server(s)")
        for server in self._servers:
            self._file_list.parse_find_cmd_output(server.list_files(), server_id=server.hostname)
        self.log(f"found {len(self._file_list)} number of items")

    def number_of_items(self) -> int:
        if self._file_list.empty():
            self._init_file_list()
        return len(self._file_list)

    def download(self, key: Union[str, int]) -> bool:
        if self._file_list.empty():
            self._init_file_list()
        _item = self._file_list.get(key)
        if not _item:
            print(f"could not retrieve item with key: {key}")
            return False

        def _get_dest() -> Path:
            _dest = _item.local_destination(ignore_is_rar=self._settings.extract)
            if not _dest:  # Fallback to download directory
                return ConfigurationManager().path("download",
                                                   convert_to_path=True,
                                                   assert_path_exists=True)
            return _dest

        _do_unrar: bool = _item.is_rar and self._settings.extract
        _is_single_file: bool = _do_unrar or _item.is_video

        for server in self._servers:
            if server.hostname != _item.server_id:
                continue
            if _do_unrar:
                _remote_path = server.extract_to_temp_dir(_item.path)
                _local_path = _get_dest()
            else:
                _remote_path = _item.remote_download_path
                _local_path = _get_dest()
            if not _local_path.is_dir():
                _local_path.mkdir(mode=0o755, parents=True)
                self.log(f"created directory: {_local_path}")
            elif not DirectoryInfo(_local_path).has_permissions(0o755):
                self.log(f"changing permissions of directory: {_local_path} to 0o755")
                _local_path.chmod(0o755)
            if server.download_with_scp(_remote_path, _local_path) and _is_single_file:
                _file = _local_path / _remote_path.name
                if not FileInfo(_file).has_permissions(0o644):
                    self.log(f"changing permissions of file: {_file} to 0o644")
                    _file.chmod(0o644)
            if _do_unrar:
                server.remove_directory(_remote_path.parent)
            break

    def valid(self) -> bool:
        for server in self._servers:
            if server.connected:
                return True
        return False

    def __len__(self) -> int:
        return len(self._servers)
