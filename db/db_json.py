#!/usr/bin/env python3

import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import datetime

from config import ConfigurationManager, SettingKeys

from db.database import DataBase, Entry, Key


class JSONDatabase(DataBase):
    def __init__(self, file_path: Optional[Path] = None):
        super().__init__()
        self._path: Optional[Path] = file_path
        self._entries: List[Entry] = []
        self._need_save: bool = False

    def save(self, create_backup: bool = True) -> bool:
        if not self._need_save:
            return True
        if not self._path.exists():
            return False
        if create_backup:
            self._backup()
        with open(self._path, "w") as _fp:
            json.dump([e.data() for e in self._entries], _fp)
        return True

    def load(self) -> bool:
        if not self.primary_key or not self._keys:
            raise ValueError(f"keys are not yet set, will not load file, {self._path}")
        if not self._path.exists():
            raise FileNotFoundError(f"cannot load file: {self._path}")
        with open(self._path, "r") as _fp:
            for _item in json.load(_fp):
                self.insert(**_item)
        self._need_save = False
        return True

    def find_duplicates(self, key: Union[Key, str]) -> Dict[Any, List[str]]:
        _all = {}
        for entry in self._entries:
            _val = entry.get(str(key))
            if _val is not None:
                if _val in _all:
                    _all[_val].append(entry.get(self.primary_key.name))
                else:
                    _all[_val] = [entry.get(self.primary_key.name)]
        return {k: v for k, v in _all.items() if len(v) > 1}

    def get_entry(self, entry_primary_value: str) -> Optional[Entry]:
        for entry in self._entries:
            if entry.get(self.primary_key.name) == entry_primary_value:
                return entry
        return None

    def update_entry(self, _):
        self._need_save = True
        return True

    def insert_entry(self, new_entry: Entry):
        self._entries.append(new_entry)
        self._need_save = True
        return True

    def entry_primary_values(self) -> Tuple[Any]:
        return tuple([e.get(self.primary_key.name) for e in self._entries])

    def find(self,
             filter_by: Optional[Dict[str, Any]] = None,
             limit: Optional[int] = None,
             sort_by_key: Optional[str] = None,
             reversed_sort: bool = False) -> List[Dict]:
        _matches = []
        for entry in self._entries:
            if filter_by is None:
                _matches.append(entry.data())
            else:
                _add = True
                for k, v in filter_by:
                    if entry.get(k) != v:
                        _add = False
                if _add:
                    _matches.append(entry.data())
        if sort_by_key is not None:
            if self._get_key(sort_by_key) is None:
                raise ValueError(f"invalid key: {sort_by_key}")
            _matches.sort(key=lambda i: i[sort_by_key], reverse=reversed_sort)
        return _matches[:limit] if limit is not None else _matches

    def _backup(self):
        _backup_path = ConfigurationManager().path(SettingKeys.PATH_BACKUP, assert_path_exists=True)
        _destination = _backup_path / f"{self._path.name}_{datetime.now().timestamp()}"
        try:
            shutil.copy(self._path, _destination)
        except PermissionError:
            shutil.copyfile(self._path, _destination)
