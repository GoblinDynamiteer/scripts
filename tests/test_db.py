import os
import unittest

import db_json


class TestDb(unittest.TestCase):
    def setUp(self):
        self.file = "_testdb.json"
        self.db = db_json.JSONDatabase(self.file)
        self.db.set_valid_keys(['name', 'age', 'sex'])
        self.db.set_key_type('name', str)
        self.db.set_key_type('age', int)
        self.db.set_key_type('sex', str)

    def test_ok(self):
        self.assertTrue(self.db.insert({'name': 'Harold'}))
        self.assertFalse(self.db.insert({'name': 'Harold'}))
        self.assertTrue(self.db.update('Harold', 'age', 72))
        self.assertTrue(self.db.update('Harold', 'sex', 'male'))
        self.assertFalse(self.db.update('Harold', 'age', []))
        self.assertTrue(self.db.insert(
            {'name': 'Andrea', 'sex': 'female', 'age': 32}))
        self.assertFalse(self.db.insert(
            {'name': 'Leah', 'sex': 2, 'age': 32}))
        self.assertTrue(self.db.insert(
            {'name': 'Leah', 'sex': 'N/A', 'age': 32}))
        self.assertTrue('Harold' in self.db)
        self.assertFalse('Monica' in self.db)
        name_list = ['Harold', 'Andrea', 'Leah']
        for num, name in enumerate(self.db):
            self.assertTrue(name == name_list[num])
        self.assertEqual(self.db.find('age', 32), ['Andrea', 'Leah'])
        self.assertEqual(self.db.find_duplicates(
            'age'), {32: ['Andrea', 'Leah']})
        self.db.insert({'name': 'Boris', 'age': 72})
        self.assertEqual(self.db.find_duplicates(
            'age'), {32: ['Andrea', 'Leah'], 72: ['Harold', 'Boris']})

    def tearDown(self):
        try:
            os.remove(self.file)
        except FileNotFoundError:
            pass