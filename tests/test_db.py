from db import db_json
from db.database import DataBase, Key, KeyType

import pytest


class TestKey:
    def test_equal(self):
        _key1 = Key("SomeKeyName", KeyType.Integer)
        _key2 = Key(name="SomeKeyName", type=KeyType.Integer)
        assert _key1 == _key2
        assert _key1 is not _key2

    def test_default(self):
        _key = Key("SomeKeyName")
        assert _key.type == KeyType.String
        assert _key.primary is False

    def test_primary(self):
        _key = Key("SomeKeyName", primary=True)
        assert _key.primary is True
        _key = Key("SomeKeyName", primary=False)
        assert _key.primary is False

    def test_in_list(self):
        _key1 = Key("SomeKeyName")
        _list = [_key1]
        _key2 = Key("SomeKeyName")
        assert _key2 in _list
        assert _key1 is not _key2

    def test_matches_type(self):
        _key = Key("SomeKeyName")
        assert _key.matches_type("some_string")
        _key = Key("SomeKeyName", type=KeyType.Integer)
        assert _key.matches_type(123)
        _key = Key("SomeKeyName", type=KeyType.List)
        assert _key.matches_type(["some_string_in_list"])
        _key = Key("SomeKeyName", type=KeyType.Boolean)
        assert _key.matches_type(True)

    def test_not_matches_type(self):
        _key = Key("SomeKeyName")
        assert _key.matches_type(123) is False
        _key = Key("SomeKeyName", type=KeyType.Integer)
        assert _key.matches_type(["some_string_in_list"]) is False
        _key = Key("SomeKeyName", type=KeyType.List)
        assert _key.matches_type(False) is False
        _key = Key("SomeKeyName", type=KeyType.Boolean)
        assert _key.matches_type("some_string") is False
        assert _key.matches_type(123.123) is False


class TestDatBaseBaseClass:
    class _DB(DataBase):
        def save(self) -> bool:
            ...

    def test_set_valid_keys_auto_primary(self):
        _db = self._DB()
        _key1 = Key("Name1")
        _db.set_valid_keys([_key1, Key("Name2"), Key("Name3")])
        assert _key1 == _db.primary_key

    def test_set_valid_keys_manual_primary(self):
        _db = self._DB()
        _key2 = Key("Name2", primary=True)
        _db.set_valid_keys([Key("Name1"), _key2, Key("Name3")])
        assert _key2 == _db.primary_key

    def test_set_valid_keys_disallow_multiple_primary(self):
        _db = self._DB()
        _key1 = Key("Name1", primary=True)
        _key2 = Key("Name2", primary=True)
        with pytest.raises(ValueError):
            _db.set_valid_keys([_key1, _key2, Key("Name3")])

    def test_set_valid_keys_disallow_same_key(self):
        _db = self._DB()
        _key1 = Key("Name1", type=KeyType.List)
        _key2 = Key("Name1", type=KeyType.List)
        with pytest.raises(ValueError):
            _db.set_valid_keys([_key1, _key2, Key("Name3")])

    def test_set_valid_keys_disallow_same_name(self):
        _db = self._DB()
        _key1 = Key("Name1", type=KeyType.List)
        _key2 = Key("Name1", type=KeyType.Integer)
        with pytest.raises(ValueError):
            _db.set_valid_keys([_key1, _key2, Key("Name3")])

    def test_insert_using_kwargs(self):
        _db = self._DB()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _db.set_valid_keys([_key1, _key2])
        assert _db.insert(Name="Harold", Age=82) is True
        assert _db.get("Harold", "Age") == 82

    def test_insert_using_dict(self):
        _db = self._DB()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _db.set_valid_keys([_key1, _key2])
        assert _db.insert(**{"Name": "Harold", "Age": 82}) is True
        assert _db.get("Harold", "Age") == 82

    def test_insert_using_kwargs_primary_not_first(self):
        _db = self._DB()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        assert _db.insert(Age=82, Name="Harold", ) is True
        assert _db.get("Harold", "Age") == 82

    def test_insert_raises_error_if_exists(self):
        _db = self._DB()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        assert _db.insert(Age=82, Name="Harold") is True
        with pytest.raises(ValueError):
            _db.insert(Name="Harold", Age=12)

    def test_update_raises_error_if_not_exists(self):
        _db = self._DB()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        with pytest.raises(ValueError):
            _db.update("Harold", Age=12)

    def test_update(self):
        _db = self._DB()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        assert _db.insert(Age=82, Name="Harold") is True
        assert _db.get("Harold", "Age") == 82
        assert _db.update("Harold", Age=12) is True
        assert _db.get("Harold", "Age") == 12

    def test_update_raises_error_if_invalid_value_type(self):
        _db = self._DB()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        assert _db.insert(Age=82, Name="Harold") is True
        with pytest.raises(TypeError):
            _db.update("Harold", Age=12.1)

    def test_update_raises_error_if_missing_key(self):
        _db = self._DB()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        assert _db.insert(Age=82, Name="Harold") is True
        with pytest.raises(ValueError):
            _db.update("Harold", SomeWrongKey="Value")


class TestJsonDatabase:
    def test_insert(self, tmp_path):
        self.db_file = tmp_path / "__db__.json"
        database = db_json.JSONDatabase(self.db_file.name)
        database.set_valid_keys(["name", "age"])
        database.set_key_type("name", str)
        assert database.insert({"name": "Harold"}) is True
        assert database.insert({"name": "Monica", "age": 32}) is True
        assert database.insert({"name": "Harold"}) is False

    def test_update(self, tmp_path):
        self.db_file = tmp_path / "__db__.json"
        database = db_json.JSONDatabase(self.db_file.name)
        database.set_valid_keys(["name", "age"])
        database.set_key_type("name", str)
        assert database.insert({"name": "Harold"}) is True
        assert database.update("Harold", "age", 72) is True

    def test_x_in(self, tmp_path):
        self.db_file = tmp_path / "__db__.json"
        database = db_json.JSONDatabase(self.db_file.name)
        database.set_valid_keys(["name", "age"])
        database.set_key_type("name", str)
        assert database.insert({"name": "Harold"}) is True
        assert "Harold" in database
        assert database.insert({"name": "Monica", "age": 32}) is True
        assert "Monica" in database
        assert "Andrea" not in database

    def test_type_check(self, tmp_path):
        self.db_file = tmp_path / "__db__.json"
        database = db_json.JSONDatabase(self.db_file.name)
        database.set_valid_keys(["name", "age"])
        database.set_key_type("name", str)
        database.set_key_type("age", int)
        assert database.insert({"name": 123}) is False
        assert database.insert({"name": "Carl", "age": "five"}) is False

    def test_find_duplicates(self, tmp_path):
        self.db_file = tmp_path / "__db__.json"
        database = db_json.JSONDatabase(self.db_file.name)
        database.set_valid_keys(["name", "age"])
        database.set_key_type("name", str)
        database.set_key_type("age", int)
        database.insert({"name": "Harold", "age": 55})
        database.insert({"name": "Linda", "age": 55})
        database.insert({"name": "Oscar", "age": 32})
        database.insert({"name": "Nina", "age": 28})
        dupes = database.find_duplicates("age")
        assert 32 not in dupes
        assert 28 not in dupes
        age_55_list = dupes.get(55, [])
        assert len(age_55_list) == 2
        assert "Harold" in age_55_list
        assert "Linda" in age_55_list
        database.insert({"name": "Ivy", "age": 28})
        database.insert({"name": "Carl", "age": 28})
        dupes = database.find_duplicates("age")
        assert 28 in dupes
        age_28_list = dupes.get(28, [])
        assert len(age_28_list) == 3
        for name in ["Carl", "Ivy", "Nina"]:
            assert name in age_28_list
