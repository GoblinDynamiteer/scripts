#!/usr/bin/env python3.6

'''String input'''

import sys
import os
import printing

PRINT = printing.PrintClass(os.path.basename(__file__))


def yes_no(question, default="yes", script_name=None):
    valid = {"yes": True, "y": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        PRINT.error("wrong default")
        quit()
    if script_name:
        print_class = printing.PrintClass(script_name)
    else:
        print_class = PRINT
    while True:
        print_class.info("{} {}".format(question, prompt), end_line=False)
        choice = input().lower()
        if default is not None and choice is '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print_class.error("Enter Yes/No!")


def get_string(display_text, script_name=None, allow_empty=False):
    if script_name:
        print_class = printing.PrintClass(script_name)
    else:
        print_class = PRINT
    while True:
        print_class.info("{}: ".format(display_text), end_line=False)
        user_input = input()
        if not allow_empty and user_input == "":
            print_class.error("empty strings not allowed! try again!")
        else:
            return user_input
