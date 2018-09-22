#!/usr/bin/env python3.6

'''File renaming functions pass --dir file/dir to process'''

import os
import argparse
import sys
import re


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
    for rep in ["_-_", " - ", "_--_"]:
        new_file_name = new_file_name.replace(rep, "-")
    # replace excess underscores
    while "__" in new_file_name:
        new_file_name = new_file_name.replace("__", "_")
    return new_file_name


def op_remove_special_chars(file_path):
    '''Removes special characters like !#, '''
    file_name = str(os.path.basename(file_path))
    new_file_name = file_name
    spec_chars = ["#", ",", "!", "’", "'"]
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


def rename_operation(file_path, operations):
    '''Runs string operations on filename, then renames the file'''
    file_name = str(os.path.basename(file_path))
    new_file_name = file_name
    for operation in operations:
        new_file_name = operation(new_file_name)
    os.rename(file_path, new_file_name)


PARSER = argparse.ArgumentParser()
PARSER.add_argument("--dir", help="directory or file to process", type=str)
ARGS = PARSER.parse_args()
FILES = []
OPERATIONS = [op_spaces_to_char,
              op_tolower,
              op_trim_extras,
              op_replace_special_chars,
              op_remove_special_chars,
              op_add_leading_zeroes]
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
else:
    print("no files to process")
