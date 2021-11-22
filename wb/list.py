import re
from typing import List
from timeit import default_timer

from wb.item import FileListItem
from base_log import BaseLog


class FileList(BaseLog):
    def __init__(self):
        BaseLog.__init__(self, use_global_settings=True)
        self.set_log_prefix("FileList")
        self._items: List[FileListItem] = []
        self._sorted: bool = False
        self._compared_to_database: bool = False

    def __len__(self):
        return len([i for i in self._items if i.valid])

    def parse_find_cmd_output(self, lines: List[str], server_id: str):
        for line in lines:
            _item = FileListItem(line, server_id)
            if _item.valid:
                self._items.append(_item)

    def print(self):
        _start = default_timer()
        if not self._sorted:
            self._sort()
        if not self._compared_to_database:
            self.log("comparing items to database...")
            self._compare_to_database()
        for item in self._items:
            item.print()
        _elapsed = default_timer() - _start
        self.log(f"listing operation took: {_elapsed}s")

    def empty(self):
        return len(self._items) == 0

    def get_regex(self, regex_pattern: str) -> List:
        if not self._sorted:
            self._sort()
        matches = []
        for item in self._items:
            _match = re.search(regex_pattern, item.name)
            if _match:
                matches.append(item)
        return matches

    def get(self, key: [str, int]) -> FileListItem:
        if isinstance(key, int):
            return self._get_item_from_index(key)
        if isinstance(key, str):
            return self._get_item_from_string(key)
        raise TypeError("key must be str or int")

    def items(self) -> List:
        if not self._sorted:
            self._sort()
        return self._items

    def _get_item_from_index(self, index: int) -> [FileListItem, None]:
        if not self._sorted:
            self._sort()
        for item in self._items:
            if item.index == index:
                return item
        return None

    def _get_item_from_string(self, item_name: str) -> [FileListItem, None]:
        for item in self._items:
            if item.name == item_name:
                return item
        return None

    def _sort(self):
        self._sorted = True
        self._items.sort(key=lambda x: x.timestamp)
        for _ix, _item in enumerate(self._items, 1):
            _item.index = _ix

    def _compare_to_database(self):
        self._compared_to_database = True
        import db.db_mov
        import db.db_tv
        _movdb = db.db_mov.MovieDatabase()
        _epdb = db.db_tv.EpisodeDatabase()
        for item in self._items:
            if item.is_movie:
                _folder = item.parent_name or item.path.stem
                if _folder in _movdb:
                    item.downloaded = True
            elif item.is_tvshow:
                if item.name in _epdb:
                    item.downloaded = True
