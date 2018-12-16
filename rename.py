#!/usr/bin/env python3.6

'''File renaming functions pass --dir file/dir to process, requires unidecode library'''

import os
import argparse
import sys
import re

from printing import to_color_str

UNIDECODE_LIB_AVAILABLE = False
try:
    from unidecode import unidecode
    UNIDECODE_LIB_AVAILABLE = True
except ImportError:
    pass


def op_spaces_to_char(file_path, replace_char='_'):
    '''Replace spaces in filename'''
    file_name = str(os.path.basename(file_path))
    new_file_name = file_name.replace(" ", replace_char)
    return new_file_name


def op_tolower(file_path):
    '''Lowercases filename'''
    file_name = str(os.path.basename(file_path))
    return file_name.lower()


def op_trim_extras(file_path):
    '''Trims unneeded extras'''
    file_name = str(os.path.basename(file_path))
    new_file_name = file_name
    # replace _-_ or " - " with -
    for rep in ["_-_", " - ", "_--_", ".-."]:
        new_file_name = new_file_name.replace(rep, "-")
    # replace excess underscores
    while "__" in new_file_name:
        new_file_name = new_file_name.replace("__", "_")
    return new_file_name


def op_remove_special_chars(file_path):
    '''Removes special characters like !#, '''
    file_name = str(os.path.basename(file_path))
    new_file_name = file_name
    spec_chars = ["#", ",", "!", "’", "'", ":"]
    for sc in spec_chars:
        new_file_name = new_file_name.replace(sc, "")
    return new_file_name


def op_replace_special_chars(file_path):
    '''Replaces special characters like & '''
    file_name = str(os.path.basename(file_path))
    new_file_name = file_name
    spec_chars = [("&", "and")]
    for sc, rep in spec_chars:
        new_file_name = new_file_name.replace(sc, rep)
    return new_file_name


def op_add_leading_zeroes(file_path):
    ''' Adds leding zeroes filenames starting with one digit '''
    file_name = str(os.path.basename(file_path))
    digit_match = re.search(r"^\d+", file_name)
    if digit_match:
        digit = digit_match.group(0)
        length = len(digit)
        return f"{int(digit):02}{file_name[length:]}"
    return file_name


def op_unidecode(file_path):
    ''' Runs unidecode lib on string/filename '''
    file_name = str(os.path.basename(file_path))
    if not UNIDECODE_LIB_AVAILABLE:
        print('unidecode not available, skipping operation')
        return file_name
    return unidecode(file_name)


def rename_operation(file_path, operations):
    '''Runs string operations on filename, then renames the file'''
    file_name = str(os.path.basename(file_path))
    new_file_name = file_name
    for operation in operations:
        new_file_name = operation(new_file_name)
    old = to_color_str(file_name, 'orange')
    new = to_color_str(new_file_name, 'green')
    if new_file_name == file_name:
        print(f'kept filename: {to_color_str(file_name, "green")}')
    else:
        print(f'renamed {old} --> {new}')
        os.rename(file_path, new_file_name)


def rename_string(string_to_rename, space_replace_char: str = '_'):
    ''' Run rename on a string, when script is used as lib '''
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
              op_trim_extras]

if UNIDECODE_LIB_AVAILABLE:
    OPERATIONS.append(op_unidecode)

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--dir", help="directory or file to process", type=str)
    ARGS = PARSER.parse_args()
    FILES = []
    try:
        if os.path.isdir(ARGS.dir):
            FILES = os.listdir(ARGS.dir)
        elif os.path.isfile(ARGS.dir):
            FILES.append(ARGS.dir)
    except TypeError:
        print("could not process passed directory or file!")
        sys.exit()

    if FILES:
        for f in FILES:
            rename_operation(f, OPERATIONS)
        print("rename operations complete")
    else:
        print("no files to process")
