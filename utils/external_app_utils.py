import re
from pathlib import Path
from typing import Optional, List, Tuple

from utils.text_utils import parse_percentage_from_string


class UnrarOutputParser:
    def __init__(self):
        self._percentage: int = 0
        self._src_path: Optional[Path] = None
        self._dest_path: Optional[Path] = None
        self._current_file: str = ""
        self._current_rar: str = ""
        self._extracted_files: List[str] = []
        self._unrar_version: str = ""
        self._changed: bool = False
        self._returned_header_str: bool = False

    def to_current_status_string(self) -> Optional[str]:
        """ Get current status as a string, intended for print(), with end='' """
        if not self._returned_header_str:
            if not self.current_rar or self._src_path is None:
                return None
            self._returned_header_str = True
            return f"UNRAR: extracting from {self._src_path / self.current_rar} ...\n"
        if not self._current_file:
            return None
        if self._percentage == 100:
            _done_str = f"DONE: {self._dest_path}" if self._dest_path is not None else "DONE!"
            return f" \r{self.current_file}: {self.percentage_done} %\n{_done_str}\n"
        return f"\r {self.current_file}: {self.percentage_done} %"

    def parse_output(self, unrar_output_line: str) -> bool:
        """ Parses the output of the unrar executable

        Keyword arguments:
        unrar_output_line -- a line from the unrar executable progress output
        """

        def _parse_all_ok(_line: str) -> None:
            if "all ok" not in _line.lower():
                return
            if self._current_file not in self._extracted_files:
                self._extracted_files.append(self._current_file)
            self._update_percentage(100)

        def _parse_file_and_percentage(_line: str) -> None:
            if not _line.startswith("..."):
                return
            _, _f, *_ = re.split(r"\s+", _line)
            self._update_percentage(parse_percentage_from_string(_line.replace("\b", " ")))
            self._update_current_file(_f)

        def _parse_from(_line: str) -> None:
            if not _line.lower().startswith("extracting from"):
                return
            _, _, _f, *_ = re.split(r"\s+", _line)
            self._update_src_path(Path(_f))

        def _parse_to(_line: str) -> None:
            _handle = _line.lower().startswith("extracting") and "from" not in _line.lower()
            if not _handle:
                return
            _, _f, _p, *_ = re.split(r"\s+", _line)
            self._update_dest_path(Path(_f))

        self._changed = False  # reset

        unrar_output_line = unrar_output_line.replace("\n", "").strip()
        if unrar_output_line.isspace():
            return False

        _parse_from(unrar_output_line)
        _parse_to(unrar_output_line)
        _parse_file_and_percentage(unrar_output_line)
        _parse_all_ok(unrar_output_line)
        return self._changed

    def _update_percentage(self, perc: int) -> None:
        if perc is None or self._percentage == perc:
            return
        self._changed = True
        self._percentage = perc

    def _update_src_path(self, src: Optional[Path]) -> None:
        if src is None:
            return
        if self._src_path != src.parent:
            self._src_path = src.parent
            self._changed = True
        if self.current_rar != src.name:
            self._current_rar = src.name
            self._changed = True

    def _update_current_file(self, file_name: Optional[str]) -> None:
        if file_name is None:
            return
        if self._current_file == file_name:
            return
        if self._current_file != "" and self._current_file not in self._extracted_files:
            self._extracted_files.append(self._current_file)
        self._current_file = file_name
        self._changed = True

    def _update_dest_path(self, dst: Optional[Path]) -> None:
        if dst is None:
            return
        if self._dest_path != dst.parent:
            self._dest_path = dst.parent
            self._changed = True
        self._update_current_file(dst.name)

    @property
    def percentage_done(self) -> int:
        return self._percentage

    @property
    def destination(self) -> Path:
        return self._dest_path

    @property
    def source_path(self) -> Path:
        return self._src_path

    @property
    def current_file(self) -> str:
        return self._current_file

    @property
    def current_rar(self) -> str:
        return self._current_rar

    @property
    def extracted_files(self) -> List[str]:
        return self._extracted_files
