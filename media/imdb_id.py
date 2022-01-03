from pathlib import Path
from typing import Optional, Union, List
import re

from base_log import BaseLog


class IMDBId(BaseLog):
    REGEX = r"([tT]{2}[0-9]{7,})"

    def __init__(self, value: Optional[Union[str, Path]] = None):
        BaseLog.__init__(self, verbose=True)
        self.set_log_prefix("IMDB_ID")
        self._ids: List[str] = []
        if value is not None:
            self._parse(value)

    def _parse(self, value: Union[str, Path]) -> None:
        if isinstance(value, str):
            self._parse_str(value)
        elif isinstance(value, Path):
            pass

    def _parse_str(self, string: str) -> None:
        matches = re.findall(self.REGEX, string)
        if not matches:
            return
        for match in matches:
            _num = match.lower().replace("tt", "")
            if _num not in self._ids:
                self._ids.append(_num)

    def has_multiple_ids(self) -> bool:
        return len(self._ids) > 1

    def valid(self) -> bool:
        return len(self._ids) > 0

    def __repr__(self) -> str:
        if not self._ids:
            return ""
        return f"tt{self._ids[0]}"


def main():
    import argparse
    parser = argparse.ArgumentParser("IMDbId Helper")
    parser.add_argument("string")
    args = parser.parse_args()
    iid = IMDBId(args.string)
    print(iid)


if __name__ == "__main__":
    main()
