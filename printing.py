#!/usr/bin/env python3.6

'''String output'''

import platform


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
          "dyellow": 220,
          "brown": 130,
          "lgrey": 250,
          "grey": 244,
          "dgrey": 239,
          "white": 256}


def to_color_str(
        string: str, foreground: str, background: str = None, bold: bool = False) -> str:
    '''Returns "colorized" string'''
    colstring = "\033[38;5;" + str(COLORS.get(foreground, '46')) + "m"
    if background:
        colstring += "\033[48;5;" + str(COLORS.get(foreground, '0')) + "m"
    if bold:
        colstring += "\033[1m"
    return colstring + string + "\033[0m"


class PrintClass:
    def __init__(self, script_name):
        self.script_file_name = script_name
        self.color = {
            'black': 30, 'red': 31, 'green': 32,
            'yellow': 33, 'blue': 34, 'magenta': 35,
            'cyan': 36}
        self.color_end_color = {'end': 0}
        self.default_color = {
            "script_name": "green",
            "info_brackets": "blue",
            "warning_brackets": "yellow",
            "error_brackets": "red",
            "success_brackets": "green"}

    def info(self, string, end_line=True, brackets_color=None, print_script_name=True):
        if print_script_name:
            self.__print_script_name()
        if string.find('[') >= 0 and string.find(']') > 0:
            if not brackets_color:
                self.__print_color_between(string,
                                           self.default_color['info_brackets'])
            else:
                self.__print_color_between(string, brackets_color)
        else:
            self.__print_no_line(string)
        if end_line:
            print("")

    def warning(self, string, end_line=True):
        self.__print_script_name()
        self.__print_with_color("WARNING ", "yellow")
        if string.find('[') >= 0 and string.find(']') > 0:
            self.__print_color_between(string,
                                       self.default_color['warning_brackets'])
        else:
            self.__print_no_line(string)
        if end_line:
            print("")

    def success(self, string, end_line=True):
        self.__print_script_name()
        self.__print_with_color("SUCCESS ", "green")
        if string.find('[') >= 0 and string.find(']') > 0:
            self.__print_color_between(string,
                                       self.default_color['success_brackets'])
        else:
            self.__print_no_line(string)
        if end_line:
            print("")

    def error(self, string, end_line=True):
        self.__print_script_name()
        self.__print_with_color("ERROR ", "red")
        if string.find('[') >= 0 and string.find(']') > 0:
            self.__print_color_between(string,
                                       self.default_color['error_brackets'])
        else:
            self.__print_no_line(string)
        if end_line:
            print("")

    def output(self, string, end_line=True):
        self.__print_no_line(string)
        if end_line:
            print("")

    def color_print(self, string, foreground, end_line=True, background=None, light=True):
        self.__print_with_color(string, foreground, background, light)
        if end_line:
            print("")

    def color_brackets(self, string, foreground, background=None, end_line=True):
        self.__print_color_between(string, foreground, background)
        if end_line:
            print("")

    def __print_with_color(self, string, foreground, background=None, light=True):
        self.__set_color(foreground, background, light)
        self.__print_no_line(string)
        self.__color_off()

    def __print_color_between(self, string, foreground, background=None,
                              char_begin='[', char_end=']', light=True):
        start_index = string.find(char_begin) + 1
        end_index = string.find(char_end)
        self.__print_no_line(string[0:start_index])
        self.__print_with_color(string[start_index:end_index], foreground)
        self.__print_no_line(string[end_index:])

    def __print_script_name(self):
        self.__print_color_between("[ {} ] ".format(self.script_file_name),
                                   self.default_color['script_name'])

    def __print_no_line(self, string):
        print(string, end='')

    def __set_color(self, foreground, background, light=True):
        if platform.system() == 'Windows':
            return ""
        fg = self.color[foreground]
        if light:
            fg += 60
        self.__print_no_line("\033[{}m".format(fg))

    def __color_off(self):
        if platform.system() == 'Windows':
            return ""
        self.__print_no_line("\033[{}m".format(self.color_end_color['end']))
