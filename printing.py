#!/usr/bin/env python3.8

'''String output'''

import shutil

COLORS = {"black": 0,
          "red": 196,
          "dred": 88,
          "lblue": 74,
          "blue": 33,
          "dblue": 21,
          "purple": 171,
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


ORANGE_GREEN_GRAD = {0: 196, 1: 202, 10: 208, 20: 215,
                     30: 184, 40: 148, 50: 190, 60: 118, 70: 46}


FORMAT_CODES = {
    'dg[': 70,  # dark green
    'e[': 196,  # error
    'g[': 154,  # green
    'b[': 74,   # blue
    'i[': 154,  # info
    'o[': 214,  # orange
    'd[': 239,  # dark /grey
    'y[': 229,  # yellow
    'w[': COLORS['warning'],
    'r[': COLORS['red'],
    'p[': COLORS['purple']}


def test_colors():
    for color_value in range(0, 257):
        pcstr(f": {color_value} ##################", color_value)

    for color_str, color_val in COLORS.items():
        pcstr(color_str.upper() + f": {color_val}", color_str)


def cstr(string, foreground, background=None, bold=False):
    colstring = ""
    if isinstance(foreground, int):
        colstring = "\033[38;5;" + str(foreground) + "m"
    else:
        colstring = "\033[38;5;" + str(COLORS[foreground]) + "m"
    if background:
        colstring += "\033[48;5;" + str(COLORS[background]) + "m"
    if bold:
        colstring += "\033[1m"
    return colstring + str(string) + "\033[0m"


def pcstr(string, foreground, background=None, bold=False):
    print(cstr(string, foreground, background, bold))


def print_color_format_string(string, format_chars=('[', ']'), show=True, end='\n', get_str=False):
    "Prints with color, based on a special format in the passed string"
    if len(format_chars) != 2 or not show:
        return
    for code, color_val in FORMAT_CODES.items():
        begin_code = code.replace('[', format_chars[0])
        string = string.replace(
            begin_code, "\033[38;5;" + str(color_val) + "m")
    colored_str = string.replace(format_chars[1], "\033[0m")
    if get_str:
        return colored_str
    print(string.replace(format_chars[1], "\033[0m"), end=end)


def pfcs(string, format_chars=('[', ']'), show=True, end='\n'):
    "Short for PrintFormatColorString, same as pcfs method"
    print_color_format_string(
        string, format_chars=format_chars, show=show, end=end)


def pcfs(string, format_chars=('[', ']'), show=True, end='\n'):
    "Short for PrintColorFormatString, same as pfcs method"
    print_color_format_string(
        string, format_chars=format_chars, show=show, end=end)


def fcs(string, format_chars=('[', ']')):
    return print_color_format_string(string, format_chars, get_str=True)


def percentage_to_cstr(percentage: str) -> str:
    percentage_val = int(percentage.replace('%', ''))
    for key, val in ORANGE_GREEN_GRAD.items():
        if percentage_val > key:
            continue
        return cstr(percentage, val)
    return cstr(percentage, 'lgreen')


def print_line(color=239, adapt_to_terminal_width=True, length=100, char="="):
    if adapt_to_terminal_width:
        length = shutil.get_terminal_size()[0] - 1
    pcstr(char * length, color)


def to_color_str(
        string: str, foreground, background=None, bold: bool = False) -> str:
    "wrapper for cstr"
    return cstr(string, foreground, background, bold)


if __name__ == "__main__":
    print("colors:\n")
    test_colors()
    pfcs(f"Hello I am dg[dark green] i am g[green]")
    pfcs(f"Hello I am e[error] and I am b[info]")
    pfcs(f"Hello I am e.error- and I am b.info-", format_chars=('.', '-'))
    print_line(color="blue")
    print_line(color="red")
    print_line()
