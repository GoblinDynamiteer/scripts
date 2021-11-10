import unittest

import tvmaze


class TestTvMaze(unittest.TestCase):

    def test_id_from_show_name(self):
        m = tvmaze.id_from_show_name
        self.assertEqual(m('Game of Thrones'), 82)
        self.assertEqual(m('westworld'), 1371)
        self.assertEqual(m('vi på saltkråkan'), 36783)
        self.assertEqual(m('purple tentacles evil comeback'), None)

    def test_show_search(self):
        m = tvmaze.show_search
        self.assertRaises(ValueError, m, '')
        self.assertRaises(TypeError, m, None)
        self.assertRaises(TypeError, m, 123)