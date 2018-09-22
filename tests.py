#!/usr/bin/env python3.6

''' Subtitle tools '''

import unittest
import filetools


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


if __name__ == '__main__':
    unittest.main()
