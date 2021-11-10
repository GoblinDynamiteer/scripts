import os
import platform
import string
import tempfile
import unittest
from pathlib import Path

import util


class TestUtilStr(unittest.TestCase):

    def test_remove_chars(self):
        self.assertEqual(
            "ab", util.remove_chars_from_string("abcd", ["c", "d"]))
        self.assertEqual(
            "WoodPecker", util.remove_chars_from_string("W,ood.Peck_er", string.punctuation))

    def test_string_similarity(self):
        self.assertEqual(util.check_string_similarity(
            "a.b", "a_b,", remove_chars=string.punctuation), 1.0)
        string_orig = "The.Good.the.Bad.and.the.Ugly.1966.iNTERNAL" \
                      ".1080p.EXTENDED.REMASTERED.BluRay.X264-CLASSiC"
        check1 = "The Good The Bad & The Ugly Bluray"
        check2 = "The Good The Weird and the Looney BLuray 1080p"
        ratio1 = util.check_string_similarity(
            string_orig, check1, remove_chars=string.punctuation)
        ratio2 = util.check_string_similarity(
            string_orig, check2, remove_chars=string.punctuation)
        self.assertGreater(ratio1, ratio2)


class TestUtilPaths(unittest.TestCase):
    def test_direname_of_file(self):
        if platform.system() == "Linux":
            path_to_file_str = "/home/user_name/folder_8271/filename.txt"
            correct_path = "/home/user_name/folder_8271"
        elif platform.system() == "Windows":
            path_to_file_str = "D:\\dirdir\\user_name\\folder_8271\\filename.txt"
            correct_path = "D:\\dirdir\\user_name\\folder_8271"
        else:
            return
        self.assertEqual(util.dirname_of_file(path_to_file_str), correct_path)
        self.assertEqual(util.dirname_of_file(
            Path(path_to_file_str)), correct_path)

    def test_filename_of_path(self):
        if platform.system() == "Linux":
            path_to_file_str = "/home/user_name/folder_8271/filename.txt"
            correct_path = "filename.txt"
        elif platform.system() == "Windows":
            path_to_file_str = "D:\\dirdir\\user_name\\folder_8271\\filename.txt"
            correct_path = "filename.txt"
        else:
            return
        self.assertEqual(util.filename_of_path(path_to_file_str), correct_path)
        self.assertEqual(util.filename_of_path(
            Path(path_to_file_str)), correct_path)

    def test_get_file_contents(self):
        contents = "HellOWWOOORLD12344$£@"
        fp = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        fp.write(contents)
        fp.close()
        self.assertEqual(util.get_file_contents(fp.name), [contents])
        self.assertEqual(util.get_file_contents(Path(fp.name)), [contents])
        os.remove(fp.name)
