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
            if value.is_file():
                self._parse_file(value)
            elif value.is_dir():
                self._parse_dir(value)
            else:
                raise FileNotFoundError(f"{value} does not exist!")
        else:
            raise TypeError(f"invalid type of value ({value}): {type(value)}!")

    def _parse_file(self, file_path: Path):
        if file_path.suffix not in [".nfo", ".txt"]:  # TODO: add better check, how to mimic ("file xxx" command?)
            self.warn(f"processing (possibly) non-text/ascii file: {file_path}")
        if file_path.stat().st_size > 1024 * 10:  # TODO: what is a reasonable file size for nfo files?
            self.warn(f"processing \"large\" file: {file_path}")
        _found = False
        with open(file_path, "r") as fp:
            for _line in fp.readlines():
                if self._parse_str(_line):
                    _found = True
        if _found:
            self.log(f"found id in file: {file_path}")

    def _parse_dir(self, dir_path: Path):
        for _item in dir_path.iterdir():
            if _item.is_file() and _item.suffix in [".nfo", ".txt"]:
                self._parse_file(_item)

    def _parse_str(self, string: str) -> bool:
        matches = re.findall(self.REGEX, string)
        if not matches:
            return False
        _ret = False
        for match in matches:
            _num = match.lower().replace("tt", "")
            if _num not in self._ids:
                self.log(f"found id: {_num}")
                self._ids.append(_num)
                _ret = True
        return _ret

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
    parser.add_argument("--path", action="store_true", help="pass as path")
    args = parser.parse_args()
    iid = IMDBId(Path(args.string) if args.path else args.string)
    print(iid)


if __name__ == "__main__":
    main()
