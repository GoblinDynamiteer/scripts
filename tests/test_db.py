import json
import random
from typing import List, Dict, Union, Optional, Callable, Any

import config

from db.database import Key, KeyType
from db.db_json import JSONDatabase
from db.db_mov import MovieDatabase
from db.db_tv import EpisodeDatabase, ShowDatabase
from db.db_mongo import MongoDatabase, MongoDbSettings

import mongomock
import pymongo

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


class TestDatBaseBaseJson:
    def test_set_valid_keys_auto_primary(self):
        _db = JSONDatabase()
        _key1 = Key("Name1")
        _db.set_valid_keys([_key1, Key("Name2"), Key("Name3")])
        assert _key1 == _db.primary_key

    def test_set_valid_keys_manual_primary(self):
        _db = JSONDatabase()
        _key2 = Key("Name2", primary=True)
        _db.set_valid_keys([Key("Name1"), _key2, Key("Name3")])
        assert _key2 == _db.primary_key

    def test_set_valid_keys_disallow_multiple_primary(self):
        _db = JSONDatabase()
        _key1 = Key("Name1", primary=True)
        _key2 = Key("Name2", primary=True)
        with pytest.raises(ValueError):
            _db.set_valid_keys([_key1, _key2, Key("Name3")])

    def test_set_valid_keys_disallow_same_key(self):
        _db = JSONDatabase()
        _key1 = Key("Name1", type=KeyType.List)
        _key2 = Key("Name1", type=KeyType.List)
        with pytest.raises(ValueError):
            _db.set_valid_keys([_key1, _key2, Key("Name3")])

    def test_set_valid_keys_disallow_same_name(self):
        _db = JSONDatabase()
        _key1 = Key("Name1", type=KeyType.List)
        _key2 = Key("Name1", type=KeyType.Integer)
        with pytest.raises(ValueError):
            _db.set_valid_keys([_key1, _key2, Key("Name3")])

    def test_insert_using_kwargs(self):
        _db = JSONDatabase()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _db.set_valid_keys([_key1, _key2])
        assert _db.insert(Name="Harold", Age=82) is True
        assert _db.get("Harold", "Age") == 82

    def test_insert_using_dict(self):
        _db = JSONDatabase()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _db.set_valid_keys([_key1, _key2])
        assert _db.insert(**{"Name": "Harold", "Age": 82}) is True
        assert _db.get("Harold", "Age") == 82

    def test_insert_using_kwargs_primary_not_first(self):
        _db = JSONDatabase()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        assert _db.insert(Age=82, Name="Harold", ) is True
        assert _db.get("Harold", "Age") == 82

    def test_insert_raises_error_if_exists(self):
        _db = JSONDatabase()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        assert _db.insert(Age=82, Name="Harold") is True
        with pytest.raises(ValueError):
            _db.insert(Name="Harold", Age=12)

    def test_update_raises_error_if_not_exists(self):
        _db = JSONDatabase()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        with pytest.raises(ValueError):
            _db.update("Harold", Age=12)

    def test_update(self):
        _db = JSONDatabase()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        assert _db.insert(Age=82, Name="Harold") is True
        assert _db.get("Harold", "Age") == 82
        assert _db.update("Harold", Age=12) is True
        assert _db.get("Harold", "Age") == 12

    def test_update_raises_error_if_invalid_value_type(self):
        _db = JSONDatabase()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        assert _db.insert(Age=82, Name="Harold") is True
        with pytest.raises(TypeError):
            _db.update("Harold", Age=12.1)

    def test_update_raises_error_if_missing_key(self):
        _db = JSONDatabase()
        _key1 = Key("Name", type=KeyType.String, primary=True)
        _key2 = Key("Age", type=KeyType.Integer)
        _key3 = Key("FavoriteColor")
        _db.set_valid_keys([_key1, _key2, _key3])
        assert _db.insert(Age=82, Name="Harold") is True
        with pytest.raises(ValueError):
            _db.update("Harold", SomeWrongKey="Value")

    def test_find_duplicates(self):
        _db = JSONDatabase()
        _db.set_valid_keys([
            Key("name", primary=True),
            Key("age", type=KeyType.Integer)])
        _db.insert(name="Harold", age=55)
        _db.insert(name="Linda", age=55)
        _db.insert(name="Oscar", age=32)
        _db.insert(name="Nina", age=28)
        dupes = _db.find_duplicates("age")
        assert 32 not in dupes
        assert 28 not in dupes
        age_55_list = dupes.get(55, [])
        assert len(age_55_list) == 2
        assert "Harold" in age_55_list
        assert "Linda" in age_55_list
        _db.insert(name="Ivy", age=28)
        _db.insert(name="Carl", age=28)
        dupes = _db.find_duplicates("age")
        assert 28 in dupes
        age_28_list = dupes.get(28, [])
        assert len(age_28_list) == 3
        for name in ["Carl", "Ivy", "Nina"]:
            assert name in age_28_list

    def test_x_in(self):
        _db = JSONDatabase()
        _db.set_valid_keys([
            Key("name", primary=True),
            Key("age", type=KeyType.Integer)])
        assert _db.insert(name="Harold") is True
        assert "Harold" in _db
        assert _db.insert(name="Monica", age=32) is True
        assert "Monica" in _db
        assert "Andrea" not in _db

    def test_load_valid_file(self, tmp_path):
        _file = tmp_path / "database.json"
        _items = [
            {"name": "Sonny", "age": 43},
            {"name": "Lenny", "age": 12},
            {"name": "Eva", "age": 32},
        ]
        with open(_file, "w") as _fp:
            json.dump(_items, _fp)
        assert _file.exists()
        _db = JSONDatabase(_file)
        _db.set_valid_keys([
            Key("name", primary=True),
            Key("age", type=KeyType.Integer)])
        _db.load()
        assert "Sonny" in _db
        assert _db.get("Lenny", "age") == 12

    def test_load_invalid_file(self, tmp_path):
        _file = tmp_path / "database.json"
        assert not _file.exists()
        _db = JSONDatabase(_file)
        _db.set_valid_keys([
            Key("name", primary=True),
            Key("age", type=KeyType.Integer)])
        with pytest.raises(FileNotFoundError):
            _db.load()


class TestMovieDatabaseJSON:
    def _gen_list(self, items=100):
        _ret = []
        for index in range(items):
            _item = {
                "folder": f"SomeMovie{index:05d}",
                "title": f"Some Movie {index}",
                "year": random.choice(range(1950, 2020)),
                "scanned": 1262304061 + index
            }
            _ret.append(_item)
        assert len(_ret) == items
        return _ret

    def test_all_movies(self, tmp_path):
        _file = tmp_path / "database.json"
        _items = self._gen_list(items=2000)
        with open(_file, "w") as _fp:
            json.dump(_items, _fp)
        assert _file.exists()
        _db = MovieDatabase(file_path=_file, use_json_db=True)
        _all = list(_db.all_movies())
        assert len(_all) == 2000
        assert _items[0]["folder"] in [m["folder"] for m in _all]

    def test_in(self, tmp_path):
        _file = tmp_path / "database.json"
        _items = self._gen_list(items=2000)
        with open(_file, "w") as _fp:
            json.dump(_items, _fp)
        assert _file.exists()
        _db = MovieDatabase(file_path=_file, use_json_db=True)
        for m in _items:
            assert m["folder"] in _db

    def test_mark_removed(self, tmp_path):
        _file = tmp_path / "database.json"
        _items = self._gen_list(items=2000)
        with open(_file, "w") as _fp:
            json.dump(_items, _fp)
        assert _file.exists()
        _db = MovieDatabase(file_path=_file, use_json_db=True)
        _item = _items[0]
        assert _db.is_removed(_item["folder"]) is False
        _db.mark_removed(_item["folder"])
        assert _db.is_removed(_item["folder"]) is True

    def test_add(self, tmp_path):
        _file = tmp_path / "database.json"
        _items = self._gen_list(items=20)
        with open(_file, "w") as _fp:
            json.dump(_items, _fp)
        assert _file.exists()
        _db = MovieDatabase(file_path=_file, use_json_db=True)
        assert len(list(_db.all_movies())) == 20
        _db.add(folder="SomeNewCoolMovie", title="Some New Cool Movie", year=2022, scanned=16623040613)
        assert "SomeNewCoolMovie" in _db
        assert len(list(_db.all_movies())) == 21


class TestShowDatabaseJSON:
    def _gen_list(self, items=100):
        _ret = []
        for index in range(items):
            _item = {
                "folder": f"SomeShow{index:05d}",
                "title": f"Some Show {index}",
                "year": random.choice(range(1950, 2020)),
                "scanned": 1262304061 + index
            }
            _ret.append(_item)
        assert len(_ret) == items
        return _ret

    def test_all_shows(self, tmp_path):
        _file = tmp_path / "database.json"
        _items = self._gen_list(items=2000)
        with open(_file, "w") as _fp:
            json.dump(_items, _fp)
        assert _file.exists()
        _db = ShowDatabase(file_path=_file, use_json_db=True)
        _all = list(_db.all_shows())
        assert len(_all) == 2000
        assert _items[0]["folder"] in [m["folder"] for m in _all]

    def test_in(self, tmp_path):
        _file = tmp_path / "database.json"
        _items = self._gen_list(items=2000)
        with open(_file, "w") as _fp:
            json.dump(_items, _fp)
        assert _file.exists()
        _db = ShowDatabase(file_path=_file, use_json_db=True)
        for m in _items:
            assert m["folder"] in _db


class TestEpisodeDatabaseJSON:
    def _gen_list(self, items=100):
        _ret = []
        for index in range(items):
            _item = {
                "filename": f"SomeShow{index:05d}.mkv",
                "released": 1099173600 + index,
                "season_number": random.randint(1, 20),
                "episode_number": random.randint(1, 20),
                "tvshow": "SomeShow",
                "scanned": 1262304061 + index
            }
            _ret.append(_item)
        assert len(_ret) == items
        return _ret

    def test_all_episodes(self, tmp_path):
        _file = tmp_path / "database.json"
        _items = self._gen_list(items=2000)
        with open(_file, "w") as _fp:
            json.dump(_items, _fp)
        assert _file.exists()
        _db = EpisodeDatabase(file_path=_file, use_json_db=True)
        _all = list(_db.all_episodes())
        assert len(_all) == 2000
        assert _items[0]["filename"] in [m["filename"] for m in _all]

    def test_in(self, tmp_path):
        _file = tmp_path / "database.json"
        _items = self._gen_list(items=2000)
        with open(_file, "w") as _fp:
            json.dump(_items, _fp)
        assert _file.exists()
        _db = EpisodeDatabase(file_path=_file, use_json_db=True)
        for m in _items:
            assert m["filename"] in _db


class TestEpisodeDatabaseMongo:
    def mocked_config_get(self,
                          key: Union[config.SettingKeys, str],
                          convert: Optional[Callable] = None,
                          section: Optional[Union[str, config.SettingSection]] = None,
                          assert_exists: bool = False,
                          default: Any = None) -> Any:

        if isinstance(key, config.SettingKeys):
            key = key.value
        if key == "mongo_ip":
            return "mocked.server.com"
        return None

    def _gen_list(self, items=100) -> List[Dict]:
        _ret = []
        for index in range(items):
            _item = {
                "filename": f"SomeShow{index:05d}.mkv",
                "released": 1099173600 + index,
                "season_number": random.randint(1, 20),
                "episode_number": random.randint(1, 20),
                "tvshow": "SomeShow",
                "scanned": 1262304061 + index
            }
            _ret.append(_item)
        assert len(_ret) == items
        return _ret

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_mock_config(self, mocker):
        client = pymongo.MongoClient("mocked.server.com")
        client.media.episodes.insert_many(self._gen_list())
        mocker.patch.object(config.ConfigurationManager, "get", self.mocked_config_get)
        assert config.ConfigurationManager().get("mongo_ip") == "mocked.server.com"
        assert config.ConfigurationManager().get(config.SettingKeys.MONGO_IP) == "mocked.server.com"
        _db = EpisodeDatabase(use_json_db=False)

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_all_episodes(self, mocker):
        client = pymongo.MongoClient("mocked.server.com")
        _items = self._gen_list(items=2000)
        client.media.episodes.insert_many(_items)
        mocker.patch.object(config.ConfigurationManager, "get", self.mocked_config_get)
        _db = EpisodeDatabase(use_json_db=False)
        _all = list(_db.all_episodes())
        assert len(_all) == 2000
        assert _items[0]["filename"] in [m["filename"] for m in _all]

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_in(self, mocker):
        client = pymongo.MongoClient("mocked.server.com")
        _items = self._gen_list(items=2000)
        client.media.episodes.insert_many(_items)
        mocker.patch.object(config.ConfigurationManager, "get", self.mocked_config_get)
        _db = EpisodeDatabase(use_json_db=False)
        for m in _items:
            assert m["filename"] in _db
        _db.add(filename="new_cool_show_s01e02.mkv", season_number=1, episode_number=2, tvshow="New Cool Show",
                scanned=123)
        assert "new_cool_show_s01e02.mkv" in _db


class TestMongoDatabase:
    def _gen_items(self, num=100) -> List[Dict]:
        _ret = []
        for i in range(num):
            _ret.append(dict(Name=f"Harold{i + 1}", Age=random.randint(10, 99)))
        return _ret

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_connection_ok(self):
        objects = self._gen_items(100)
        client = pymongo.MongoClient("mocked.server.com")
        client.test_db.test_collection.insert_many(objects)
        _settings = MongoDbSettings(
            ip="mocked.server.com",
            username="none",
            password="none",
            collection_name="test_collection",
            database_name="test_db"
        )
        _db = MongoDatabase(settings=_settings)

    def test_connection_error_raises_exception(self):
        _settings = MongoDbSettings(
            ip="some.non-existing.server.org.123456",
            username="none",
            password="none",
            collection_name="test_collection",
            database_name="test_db"
        )
        with pytest.raises(ConnectionError):
            _ = MongoDatabase(settings=_settings)

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_connection_missing_db_raises_exception(self):
        objects = self._gen_items(100)
        client = pymongo.MongoClient("mocked.server.com")
        client.test_db.test_collection.insert_many(objects)
        _settings = MongoDbSettings(
            ip="mocked.server.com",
            username="none",
            password="none",
            collection_name="test_collection",
            database_name="non_existing_db"
        )
        with pytest.raises(ValueError):
            _ = MongoDatabase(settings=_settings)

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_connection_missing_collection_raises_exception(self):
        objects = self._gen_items(100)
        client = pymongo.MongoClient("mocked.server.com")
        client.test_db.test_collection.insert_many(objects)
        _settings = MongoDbSettings(
            ip="mocked.server.com",
            username="none",
            password="none",
            collection_name="non_existing_collection",
            database_name="test_db"
        )
        with pytest.raises(ValueError):
            _ = MongoDatabase(settings=_settings)

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_basic_retrieval(self):
        objects = self._gen_items(100)
        client = pymongo.MongoClient("mocked.server.com")
        client.test_db.test_collection.insert_many(objects)
        _settings = MongoDbSettings(
            ip="mocked.server.com",
            username="none",
            password="none",
            collection_name="test_collection",
            database_name="test_db"
        )
        _db = MongoDatabase(settings=_settings)
        _db.set_valid_keys([Key("Name"), Key("Age", type=KeyType.Integer)])
        assert len(_db.entry_primary_values()) == 100
        _age = objects[10].get("Age", None)
        _name = objects[10].get("Name", None)
        assert _age is not None
        assert _name is not None
        assert _db.get(_name, "Age") == _age

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_x_in(self):
        objects = self._gen_items(10)
        client = pymongo.MongoClient("mocked.server.com")
        client.test_db.test_collection.insert_many(objects)
        _settings = MongoDbSettings(
            ip="mocked.server.com",
            username="none",
            password="none",
            collection_name="test_collection",
            database_name="test_db"
        )
        _db = MongoDatabase(settings=_settings)
        _db.set_valid_keys([Key("Name"), Key("Age", type=KeyType.Integer)])
        for _obj in objects:
            assert _obj.get("Name", None) in _db

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_insert(self):
        objects = self._gen_items(10)
        client = pymongo.MongoClient("mocked.server.com")
        client.test_db.test_collection.insert_many(objects)
        _settings = MongoDbSettings(
            ip="mocked.server.com",
            username="none",
            password="none",
            collection_name="test_collection",
            database_name="test_db"
        )
        _db = MongoDatabase(settings=_settings)
        _db.set_valid_keys([Key("Name"), Key("Age", type=KeyType.Integer)])
        _db.insert(Name="Linda", Age=23)
        assert "Linda" in _db
        assert _db.get("Linda", "Age") == 23

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_update(self):
        objects = self._gen_items(10)
        client = pymongo.MongoClient("mocked.server.com")
        client.test_db.test_collection.insert_many(objects)
        _settings = MongoDbSettings(
            ip="mocked.server.com",
            username="none",
            password="none",
            collection_name="test_collection",
            database_name="test_db"
        )
        _db = MongoDatabase(settings=_settings)
        _db.set_valid_keys([Key("Name"), Key("Age", type=KeyType.Integer)])
        _db.insert(Name="Linda", Age=23)
        assert "Linda" in _db
        assert _db.get("Linda", "Age") == 23
        _db.update("Linda", Age=33)
        assert _db.get("Linda", "Age") == 33

    @mongomock.patch(servers=(("mocked.server.com", 27017),))
    def test_find_duplicates(self):
        client = pymongo.MongoClient("mocked.server.com")
        client.test_db.test_collection.insert_many([
            dict(Name="Harold", Age=55),
            dict(Name="Linda", Age=55),
            dict(Name="Oscar", Age=32),
            dict(Name="Nina", Age=28)])
        _settings = MongoDbSettings(
            ip="mocked.server.com",
            username="none",
            password="none",
            collection_name="test_collection",
            database_name="test_db"
        )
        _db = MongoDatabase(settings=_settings)
        _db.set_valid_keys([
            Key("Name", primary=True),
            Key("Age", type=KeyType.Integer)])
        dupes = _db.find_duplicates("Age")
        assert 32 not in dupes
        assert 28 not in dupes
        age_55_list = dupes.get(55, [])
        assert len(age_55_list) == 2
        assert "Harold" in age_55_list
        assert "Linda" in age_55_list
        _db.insert(Name="Ivy", Age=28)
        _db.insert(Name="Carl", Age=28)
        dupes = _db.find_duplicates("Age")
        assert 28 in dupes
        age_28_list = dupes.get(28, [])
        assert len(age_28_list) == 3
        for name in ["Carl", "Ivy", "Nina"]:
            assert name in age_28_list
