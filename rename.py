#!/usr/bin/env python3.7

"File renaming functions pass --dir file/dir to process, requires unidecode library"

import os
import argparse
import re
from pathlib import Path

from printout import to_color_str, print_line

UNIDECODE_LIB_AVAILABLE = False
try:
    from unidecode import unidecode
    UNIDECODE_LIB_AVAILABLE = True
except ImportError:
    pass


def op_replace_umlauts(string):
    for char, rep in [("Å", "A"),
                      ("å", "a"),
                      ("Ä", "A"),
                      ("ä", "a"),
                      ("Ö", "O"),
                      ("ö", "o")]:
        string = string.replace(char, rep)
    return string


def op_spaces_to_char(string, replace_char='_'):
    "Replace spaces in string"
    return string.replace(" ", replace_char)


def op_tolower(string):
    "Lowercases string"
    return string.lower()


def op_trim_extras(string):
    "Trims unneeded extras"
    renamed_string = string
    # replace _-_ or " - " with -
    for rep in ["_-_", " - ", "_--_", ".-."]:
        renamed_string = renamed_string.replace(rep, "-")
    # replace excess underscores
    while "__" in renamed_string:
        renamed_string = renamed_string.replace("__", "_")
    return renamed_string


def op_remove_special_chars(string):
    "Removes special characters like !#, "
    renamed_string = string
    for search in ["#", ",", "!", "’", "'", ":"]:
        renamed_string = renamed_string.replace(search, "")
    return renamed_string


def op_replace_special_chars(string):
    "Replaces special characters like & "
    renamed_string = string
    for search, replacement in [("&", "and")]:
        renamed_string = renamed_string.replace(search, replacement)
    return renamed_string


def op_add_leading_zeroes(string):
    " Adds leding zeroes filenames starting with one digit "
    digit_match = re.search(r"^\d+", string)
    if digit_match:
        digit = digit_match.group(0)
        length = len(digit)
        return f"{int(digit):02}{string[length:]}"
    return string


def op_unidecode(string):
    " Runs unidecode lib on string/filename "
    if not UNIDECODE_LIB_AVAILABLE:
        return string
    return unidecode(string)


def rename_operation(file_path, operations, dont_rename=False, space_replace_char: str = '_'):
    "Runs string operations on filename, then renames the file"
    new_file_name = file_path.name
    for operation in operations:
        if operation is op_spaces_to_char:
            new_file_name = operation(
                new_file_name, replace_char=space_replace_char)
        else:
            new_file_name = operation(new_file_name)
    renamed_file_path = file_path.parent / new_file_name
    old = to_color_str(file_path.relative_to(Path.cwd()), 'orange')
    new = to_color_str(renamed_file_path.relative_to(Path.cwd()), 'green')
    if new_file_name == file_path.name:
        print(f'kept filename: {to_color_str(file_path.name, "green")}')
    else:
        if not dont_rename:
            os.rename(file_path, renamed_file_path)
        print(f"renamed {old}\n"
              f" -->    {new}")
    print_line()


def rename_string(string_to_rename, space_replace_char: str = '_'):
    " Run rename on a string, when script is used as lib "
    for operation in OPERATIONS:
        if operation is op_spaces_to_char:
            string_to_rename = operation(string_to_rename, space_replace_char)
            continue
        string_to_rename = operation(string_to_rename)
    return string_to_rename


OPERATIONS = [op_spaces_to_char,
              op_tolower,
              op_replace_special_chars,
              op_remove_special_chars,
              op_add_leading_zeroes,
              op_trim_extras,
              op_replace_umlauts]

if UNIDECODE_LIB_AVAILABLE:
    OPERATIONS.append(op_unidecode)

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument(
        "location",
        help="directory or file to process",
        type=str)
    PARSER.add_argument(
        "--rename-dirs",
        "-d",
        help="also rename directories",
        action="store_true",
        dest="renamedirs")
    PARSER.add_argument(
        "--simulate",
        "-s",
        help="only show new filenames, dont actually rename",
        action="store_true")
    PARSER.add_argument(
        "--spaces-to-dots",
        help="only replace spaces with dots",
        action="store_true",
        dest="space_op")
    ARGS = PARSER.parse_args()
    FILES = []
    DIRECTORIES = []
    ROOT_ITEM_FULL_PATH = Path(ARGS.location).resolve()
    REP_CHAR = "_"
    if ROOT_ITEM_FULL_PATH.is_dir():
        for root_path, dir_list, file_list in os.walk(ROOT_ITEM_FULL_PATH):
            for file_item in file_list:
                FILES.append(Path(root_path) / file_item)
            for dir_item in dir_list:
                DIRECTORIES.append(Path(root_path) / dir_item)
    elif ROOT_ITEM_FULL_PATH.is_file():
        FILES.append(ROOT_ITEM_FULL_PATH)
    if ARGS.simulate:
        print("running simulation!")
    if ARGS.space_op:
        OPERATIONS = [op_spaces_to_char]
        REP_CHAR = "."
    if FILES or DIRECTORIES:
        for f in FILES:
            rename_operation(
                f, OPERATIONS, dont_rename=ARGS.simulate, space_replace_char=REP_CHAR)
        if ARGS.renamedirs:
            for d in DIRECTORIES:
                rename_operation(
                    d, OPERATIONS, dont_rename=ARGS.simulate, space_replace_char=REP_CHAR)
        print("rename operations complete")
    else:
        print("no files to process")
