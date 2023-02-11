import re
from enum import Enum
from pathlib import PurePosixPath, Path
from typing import Optional, Union, List

from base_log import BaseLog
from printout import cstr, Color
from wb.helper_methods import get_remote_files_path
from utils.size_utils import SizeBytes

from media.util import Util as MediaUtil
from media.episode import Episode
from media.movie import Movie

FilterType = Union[str, List[str]]


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
    def remote_download_path(self) -> PurePosixPath:
        if self.is_rar:
            if self._path.parent == get_remote_files_path():
                raise AssertionError("parent is remote file path!")
            return self._path.parent
        return self._path

    def local_destination(self, ignore_is_rar: bool = False) -> Optional[Path]:
        if not ignore_is_rar and self.is_rar:
            return None
        if self.is_tvshow:
            _ep = Episode(Path(self.path))
            _dest = _ep.get_correct_location()
            if _dest.is_dir():
                return _dest
        if self.is_movie:
            _mov = Movie(Path(self.path))
            return _mov.get_correct_location()
        return None

    def matches_filter(self, filt: Optional[FilterType] = None, case_sensitive: bool = False) -> bool:
        if not filt:
            return True

        def _match(text: str) -> bool:
            if case_sensitive:
                return text in self.name
            return text.lower() in self.name.lower()

        if isinstance(filt, str):
            filt = [filt]
        return all([_match(t) for t in filt])

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
    def size_human_readable(self) -> str:
        return SizeBytes(self._bytes).to_string()

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

    def print(self, show_additional_info: bool = False) -> None:
        def _print_info_line(_line: str, prefix: Optional[str] = None, color: Color = Color.LightGreen):
            if prefix:
                print(" " * 7 + cstr("* ", Color.Red) + f"{prefix}: " + cstr(_line, color))
            else:
                print(" " * 7 + cstr("* ", Color.Red) + cstr(_line, color))

        def _print_extras_for_episode():
            _ep = Episode(Path(self.path))
            _loc = _ep.get_correct_location()
            _loc_ok = _loc.is_dir()
            _present: str = " (present)" if _loc_ok else " (not present)"
            _color = Color.LightGreen if _loc_ok else Color.Orange
            _print_info_line(str(_loc) + _present, prefix="dest", color=_color)
            _valid = _ep.is_valid()
            _valid_color = Color.LightGreen if _valid else Color.Red
            _print_info_line(str(_valid), prefix="valid", color=_valid_color)
            _print_info_line(_ep.name, prefix="parsed name")
            _print_info_line(str(self.size_human_readable), prefix="size")  # FIXME: handle multiple RARs
            _print_info_line(str(self._path.suffix.replace(".", "")), prefix="ext")

        def _print_extras_for_movie():
            _mov = Movie(Path(self.path))
            _print_info_line(str(_mov.get_correct_location()), prefix="dest")
            _valid = _mov.is_valid(replace_filename_whitespace=False)
            _valid_color = Color.LightGreen if _valid else Color.Red
            _print_info_line(str(_valid), prefix="matches regex", color=_valid_color)
            _print_info_line(_mov.name, prefix="parsed name")
            _print_info_line(str(self.size_human_readable), prefix="size")  # FIXME: handle multiple RARs
            _print_info_line(str(self._path.suffix.replace(".", "")), prefix="ext")

        def _to_color(text: str, color: Optional[Color], hooks: bool = False) -> str:
            _ret_str = f"[{text}]" if hooks else text
            return cstr(_ret_str, color) if color else _ret_str

        _name = self.parent_name or self.path.stem
        _grey: Optional[Color] = Color.DarkGrey if self._downloaded else None

        if self.is_movie:
            _type: str = _to_color("MOVI", _grey or Color.LightBlue, hooks=True)
        elif self.is_tvshow:
            _type: str = _to_color("SHOW", _grey or Color.LightPurple, hooks=True)
            if self.parent_is_season_dir:
                _name = self.path.stem
        else:
            _type: str = _to_color("UNKN", _grey or Color.Orange, hooks=True)

        _ix: str = _to_color(f"{self.index:04d}", _grey or Color.LightGreen, hooks=True)
        _name = _to_color(_name, _grey or None)

        if self.is_rar:
            _filetype: str = _to_color("RAR", _grey or Color.LightYellow, hooks=True)
        else:
            _filetype: str = _to_color("MKV", _grey or Color.Teal, hooks=True)

        print(f"{_ix} {_type} {_filetype} {_name}")
        if show_additional_info:
            if self.is_movie:
                _print_extras_for_movie()
            elif self.is_tvshow:
                _print_extras_for_episode()
