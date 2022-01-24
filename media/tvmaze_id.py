from typing import Optional, Union, List
import re

from base_log import BaseLog


class TvMazeId(BaseLog):
    REGEX = r"\d{1,10}"  # TODO: improve, this matches alot of numbers

    def __init__(self, value: Optional[Union[str, int]] = None):
        BaseLog.__init__(self, verbose=True)
        self.set_log_prefix("TVMAZE_ID")
        self._ids: List[int] = []
        if value is not None:
            self._parse(value)

    def _parse(self, value: Union[str, int]) -> None:
        if isinstance(value, str):
            self._parse_str(value)
        elif isinstance(value, int):
            self._add_int(value)
        else:
            raise TypeError(f"invalid type of value ({value}): {type(value)}!")

    def _parse_str(self, string: str) -> bool:
        matches = re.findall(self.REGEX, string)
        if not matches:
            return False
        _ret = False
        for match in matches:
            _num = int(match)
            if _num not in self._ids:
                self.log(f"found (possible) id: {_num}")
                self._ids.append(_num)
                _ret = True
        return _ret

    def _add_int(self, value: int):
        if value <= 0:
            raise ValueError("id must be greater than zero")
        if value not in self._ids:
            self._ids.append(value)

    def has_multiple_ids(self) -> bool:
        return len(self._ids) > 1

    def valid(self) -> bool:
        return len(self._ids) > 0

    def __repr__(self) -> str:
        if not self._ids:
            return ""
        return f"{self._ids[0]}"
