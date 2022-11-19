from pathlib import Path
from os import stat_result
import stat
from typing import Optional

from utils.size_utils import SizeBytes

class FileInfo:
    ST_MODE_PERMISSIONS_MASK = 0o777

    def __init__(self, path_to_file: Path):
        if not path_to_file.is_file():
            raise FileNotFoundError(f"{path_to_file} is not a file!")
        self._path = path_to_file
        self._stat_res: Optional[stat_result] = None

    def _stat(self) -> stat_result:
        if self._stat_res is None:
            self._stat_res = self._path.stat()
        return self._stat_res

    @property
    def stat(self) -> stat_result:
        return self._stat()

    @property
    def all_readable(self) -> bool:
        return all((self.user_readable, self.group_readable, self.others_readable))

    @property
    def user_readable(self) -> bool:
        return bool(self._stat().st_mode & stat.S_IRUSR)

    @property
    def group_readable(self) -> bool:
        return bool(self._stat().st_mode & stat.S_IRGRP)

    @property
    def others_readable(self) -> bool:
        return bool(self._stat().st_mode & stat.S_IROTH)

    @property
    def size(self) -> SizeBytes:
        return SizeBytes(self._stat().st_size)

    def has_permissions(self, permissions_bits: int) -> bool:
        return (self._stat().st_mode & self.ST_MODE_PERMISSIONS_MASK) == permissions_bits


def main():
    import argparse
    parser = argparse.ArgumentParser("FileUtils")
    parser.add_argument("file_path", type=Path)
    args = parser.parse_args()
    fi = FileInfo(args.file_path)
    print(f"{fi.stat=}")
    print(f"{fi.all_readable=}")
    print(f"{fi.user_readable=}")
    print(f"{fi.group_readable=}")
    print(f"{fi.others_readable=}")
    print(f"{fi.size=}")
    print(f"has 644: {fi.has_permissions(0o644)}")


if __name__ == "__main__":
    main()
