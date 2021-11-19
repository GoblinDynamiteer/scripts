from db import db_json


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
