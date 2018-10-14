#!/usr/bin/env python3.6

''' Subtitle tools '''

import unittest
import filetools
import str_o


class TestFileTools(unittest.TestCase):

    def test_fix_invalid_folder_or_file_name(self):
        self.assertEqual(
            filetools.fix_invalid_folder_or_file_name('A B'), 'A.B')
        self.assertEqual(
            filetools.fix_invalid_folder_or_file_name('Name.blu-ray.- SceNE'), 'Name.BluRay-SceNE')
        self.assertEqual(
            filetools.fix_invalid_folder_or_file_name('name-'), 'name')

    def test_guess_folder_type(self):
        self.assertEqual(filetools.guess_folder_type(
            'TvShow.S02.720p.HDTV.x264-SceneName'), 'season')
        self.assertEqual(filetools.guess_folder_type(
            'MovieName.2014.720p.BluRay.x264-aFP'), 'movie')
        self.assertEqual(filetools.guess_folder_type(
            'MovieName.2160p.BluRay.x264-aFP'), 'movie')


class TestStrOut(unittest.TestCase):

    def to_color_str(self):
        self.assertEqual(str_o.to_color_str("ToColor", "red"),
                         "\033[38;5;196mToColor\033[0m")


if __name__ == '__main__':
    unittest.main()
