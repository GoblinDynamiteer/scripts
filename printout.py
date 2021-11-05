#!/usr/bin/env python3.8

import shutil
from enum import Enum
import os

_COLOR_END = "\033[0m"
_CLR_DICT = {"black": 0,
             "red": 196,
             "dred": 88,
             "lblue": 74,
             "blue": 33,
             "dblue": 21,
             "purple": 171,
             "lpurple": 183,
             "orange": 214,
             "teal": 123,
             "green": 70,
             "dgreen": 28,
             "lgreen": 46,
             "pink": 218,
             "lyellow": 229,
             "yellow": 226,
             "dyellow": 220,
             "warning": 221,
             "brown": 130,
             "lgrey": 250,
             "grey": 244,
             "dgrey": 239,
             "white": 256}

_ORANGE_GREEN_GRAD = {0: 196, 1: 202, 10: 208, 20: 215,
                      30: 184, 40: 148, 50: 190, 60: 118, 70: 46}

_FORMAT_CODES = {
    "mg[": 243,  # medium grey
    "dg[": 239,  # dark grey
    "lg[": 252,  # light grey
    "lb[" : 74, # light blue
    "e[": 196,  # error
    "g[": 154,  # green
    "b[": 74,  # blue
    "i[": 154,  # info
    "o[": 214,  # orange
    "d[": 239,  # dark /grey
    "y[": 229,  # yellow
    "r[": _CLR_DICT["red"],
    "w[": _CLR_DICT["warning"],
    "p[": _CLR_DICT["purple"]}


class Color(Enum):
    Black = _CLR_DICT["black"]
    LightGreen = _CLR_DICT["lgreen"]
    Orange = _CLR_DICT["orange"]
    Purple = _CLR_DICT["purple"]
    Pink = _CLR_DICT["pink"]
    Teal = _CLR_DICT["teal"]
    LightBlue = _CLR_DICT["lblue"]
    DarkYellow = _CLR_DICT["dyellow"]
    LightYellow = _CLR_DICT["lyellow"]
    LightGrey = _CLR_DICT["lgrey"]
    DarkGrey = _CLR_DICT["dgrey"]
    Grey = _CLR_DICT["grey"]
    Red = _CLR_DICT["red"]
    Error = _CLR_DICT["red"]
    Warning = _CLR_DICT["warning"]


def _is_win():
    return os.name == "nt"


def _to_index_str(color_value):
    if isinstance(color_value, int):
        return str(color_value)
    if isinstance(color_value, str):
        return str(_CLR_DICT.get(color_value, Color.LightGreen.value))
    if isinstance(color_value, Color):
        return str(color_value.value)
    return str(Color.LightGreen.value)


def test_colors():
    for color_value in range(0, 257):
        pcstr(f": {color_value} ##################", color_value)

    for color_str, color_val in _CLR_DICT.items():
        pcstr(color_str.upper() + f": {color_val}", color_str)


def cstr(string, foreground, background=None, bold=False):
    if _is_win():
        return string
    _color_str = "\033[38;5;" + _to_index_str(foreground) + "m"
    if background:
        _color_str += "\033[48;5;" + _to_index_str(background) + "m"
    if bold:
        _color_str += "\033[1m"
    return f"{_color_str}{str(string)}{_COLOR_END}"


def pcstr(string, foreground, background=None, bold=False):
    print(cstr(string, foreground, background, bold))


def percentage_to_cstr(percentage: str) -> str:
    percentage_val = int(percentage.replace('%', ''))
    for key, val in _ORANGE_GREEN_GRAD.items():
        if percentage_val > key:
            continue
        return cstr(percentage, val)
    return cstr(percentage, Color.LightGreen)


def print_color_format_string(string, format_chars=("[", "]"), show=True, end="\n", get_str=False):
    if len(format_chars) != 2 or not show:
        return
    for code, color_val in _FORMAT_CODES.items():
        begin_code = code.replace("[", format_chars[0])
        _rep = "\033[38;5;" + str(color_val) + "m" if not _is_win() else ""
        string = string.replace(begin_code, _rep)
    _rep = _COLOR_END if not _is_win() else ""
    colored_str = string.replace(format_chars[1], _rep)
    if get_str:
        return colored_str
    print(colored_str, end=end)


def pfcs(string, format_chars=('[', ']'), show=True, end='\n'):
    print_color_format_string(
        string, format_chars=format_chars, show=show, end=end)


def pcfs(string, format_chars=('[', ']'), show=True, end='\n'):
    print_color_format_string(
        string, format_chars=format_chars, show=show, end=end)


def fcs(string, format_chars=('[', ']')):
    return print_color_format_string(string, format_chars, get_str=True)


def print_line(color=239, adapt_to_terminal_width=True, length=100, char="="):
    if adapt_to_terminal_width:
        length = shutil.get_terminal_size()[0] - 1
    pcstr(char * length, color)


def to_color_str(
        string: str, foreground, background=None, bold: bool = False) -> str:
    """ Wrapper for cstr """
    return cstr(string, foreground, background, bold)


if __name__ == "__main__":
    print("colors:\n")
    test_colors()
    pfcs(f"Hello I am dg[dark grey] i am g[green]")
    pfcs(f"Hello I am e[error] and I am b[info]")
    pfcs(f"Hello I am e.error- and I am b.info-", format_chars=('.', '-'))
    print(cstr("Hello I am orange using enum", Color.Orange))
    print(cstr("Hello I am black/orange using enum", Color.Black, Color.Orange))
    print_line(color="blue")
    print_line(color="red")
    print_line()
