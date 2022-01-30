import re
from enum import Enum
from pathlib import PurePosixPath
from typing import Optional

from base_log import BaseLog
from printout import fcs, pfcs, cstr, Color
from media.util import Util as MediaUtil
from wb.helper_methods import get_remote_files_path


class FileListItem(BaseLog):
    class MediaType(Enum):
        Movie = "movie"
        Episode = "episode"
        Unknown = "unknown"

    _ignore = ["sample", "subs", "subpack"]

    def __init__(self, string: str, server_id: str = ""):
        BaseLog.__init__(self, verbose=True)
        self.set_log_prefix("ITEM")
        self._raw = string.replace("\n", "").strip()
        self._index = None
        self._server_id = server_id
        self._type = None
        self._downloaded: bool = False
        self._parse()

    def _parse(self):
        self._valid = False
        try:
            _stamp, _bytes, _path = self._raw.split(" | ")
        except ValueError as _:
            self.error(f"could not split line: {self._raw}")
            return
        self._path = PurePosixPath(_path)
        _files_path = get_remote_files_path()
        if hasattr(self._path, "is_relative_to"):
            is_rel = self._path.is_relative_to(_files_path)
        else:
            is_rel = str(self._path).startswith(str(_files_path))
        if not is_rel:
            self.error(f"path {self._path} is not relative to: {_files_path}")
            return
        if not _bytes.isdigit():
            self.error(f"bytes value: {_bytes} is not an integer!")
            return
        self._bytes = int(_bytes)
        try:
            self._timestamp = int(_stamp.split(".")[0])
        except ValueError as _:
            self.error(f"could not parse timestamp from: {_stamp}")
            return
        self._valid = True

    def _determine_type(self):
        self._type = self.MediaType.Unknown
        if MediaUtil.is_movie(self.name):
            self._type = self.MediaType.Movie
        elif MediaUtil.is_episode(self.name):
            self._type = self.MediaType.Episode
        elif self._path.parent != get_remote_files_path():
            _parent_name = self._path.parent.name
            if MediaUtil.is_movie(_parent_name):
                self._type = self.MediaType.Movie
            elif MediaUtil.is_episode(_parent_name):
                self._type = self.MediaType.Episode

    @property
    def index(self) -> Optional[int]:
        return self._index

    @index.setter
    def index(self, index_val: int):
        self._index = index_val

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def parent_name(self) -> Optional[str]:
        if self._path.parent != get_remote_files_path():
            return self._path.parent.name
        return None

    @property
    def parent_is_season_dir(self) -> bool:
        if self.parent_name:
            return MediaUtil.is_season(self.parent_name)
        return False

    @property
    def path(self) -> PurePosixPath:
        return self._path

    @property
    def download_path(self) -> PurePosixPath:
        if self.is_rar:
            if self._path.parent == get_remote_files_path():
                raise AssertionError("parent is remote file path!")
            return self._path.parent
        return self._path

    @property
    def is_movie(self):
        if self._type is None:
            self._determine_type()
        return self._type == self.MediaType.Movie

    @property
    def is_tvshow(self):
        if self._type is None:
            self._determine_type()
        return self._type == self.MediaType.Episode

    @property
    def media_type(self) -> MediaType:
        if self._type is None:
            self._determine_type()
        return self._type

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
    def server_id(self) -> str:
        return self._server_id

    @property
    def downloaded(self) -> bool:
        return self._downloaded

    @downloaded.setter
    def downloaded(self, state: bool) -> None:
        if self._downloaded == state:
            return
        self._downloaded = True

    @property
    def valid(self) -> bool:
        if not self._valid:
            return False
        if any([_i in self.name.lower() for _i in self._ignore]):
            return False
        if self.is_rar:
            _match = re.search(r"\.part\d{2,3}\.rar", self._path.name)
            if _match:
                return self._path.name.endswith("part01.rar")
            if any([s in self._path.parent.name.lower() for s in ["subpack", "subs"]]):
                return False
        if self.is_video:
            if "sample" in self._path.parent.name.lower():
                return False
        return True

    def print(self):
        _name = self.parent_name or self.path.stem
        _type_str = fcs("o[UNKN]")
        if self.is_movie:
            _type_str = fcs("b[MOVI]")
        elif self.is_tvshow:
            _type_str = fcs("p[SHOW]")
            if self.parent_is_season_dir:
                _name = self.path.stem
        _dl_str = f"DL:{'Y' if self._downloaded else 'N'}"
        _ix_fcs_c = "i"
        if self._downloaded:
            _ix_fcs_c = "dg"
            _name = cstr(_name, Color.DarkGrey)
        pfcs(f"{_ix_fcs_c}<[{self.index:04d}]> [{_type_str}] [{_dl_str}] {_name}", format_chars=("<", ">"))
