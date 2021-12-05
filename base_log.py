#!/usr/bin/env python3

from typing import Dict

from datetime import datetime
from printout import fcs, cstr, Color, print_line, pfcs
from singleton import Singleton
import random

from pyfiglet import Figlet


class BaseLogGlobalSettings(metaclass=Singleton):
    _use_ms = False
    _use_timestamp = False
    _verbose = False

    @property
    def use_milliseconds_in_timestamp(self):
        return self._use_ms

    @use_milliseconds_in_timestamp.setter
    def use_milliseconds_in_timestamp(self, state: bool):
        self._use_ms = state

    @property
    def use_timestamps(self):
        return self._use_timestamp

    @use_timestamps.setter
    def use_timestamps(self, state: bool):
        self._use_timestamp = state

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, state: bool):
        self._verbose = state


class BaseLog:
    def __init__(self, verbose=False, use_timestamps=False, use_milliseconds=False, use_global_settings=False):
        self.print_log = verbose
        self.log_prefix = "LOG"
        self._log_prefix2 = None
        self._log_prefix_color = 154  # light green / info
        self._use_timestamp = use_timestamps
        self._use_ms = use_milliseconds
        self._warned: Dict[str, bool] = {}
        if use_global_settings:  # overrides
            _settings = BaseLogGlobalSettings()
            self._use_timestamp = _settings.use_timestamps
            self.print_log = _settings.verbose
            self._use_ms = _settings.use_milliseconds_in_timestamp

    def set_prefix_color(self, color):
        if color == "random":
            color = random.randint(22, 232)
        self._log_prefix_color = color

    def set_log_prefix(self, log_prefix: str, color=None):
        self.log_prefix = log_prefix.upper()
        if color is not None:
            self.set_prefix_color(color)

    def set_log_prefix_2(self, log_prefix: str, color=Color.DarkGrey):
        self._log_prefix2 = cstr(log_prefix, color)

    def _print_fcs(self, string):
        print(self._prefix_str(), end=" ")
        pfcs(string)

    def log(self, info_str, info_str_line2="", format_string=False, force=False):
        if not force and not self.print_log:
            return
        if format_string:
            self._print_fcs(info_str)
        else:
            print(f"{self._prefix_str()} {info_str}")
        if info_str_line2:
            spaces = " " * len(f"({self.log_prefix}) ")
            _printer = pfcs if format_string else print
            _printer(f"{spaces}{info_str_line2}")

    def log_fs(self, info_str, info_str_line2="", force=False):
        self.log(info_str, info_str_line2, format_string=True, force=force)

    def log_warn(self, warn_str, format_string=False, force=False):
        self._print_with_tag(warn_str, tag=fcs("w[warning]"), format_string=format_string, force=force)

    def warn(self, warn_str, format_string=False, force=False):
        self.log_warn(warn_str, format_string, force)

    def warn_once(self, warn_str, format_string=False, force=False):
        if self._warned.get(warn_str, False):
            return
        self._warned[warn_str] = True
        self.log_warn(warn_str, format_string, force)

    def warn_fs(self, warn_str, force=False):
        self.log_warn(warn_str, format_string=True, force=force)

    def log_error(self, err_str, format_string=False, force=False):
        self._print_with_tag(err_str, tag=fcs("e[error]"), format_string=format_string, force=force)

    def error(self, err_str, format_string=False, force=False):
        self.log_error(err_str, format_string, force)

    def error_fs(self, err_str, force=False):
        self.log_error(err_str, format_string=True, force=force)

    def _print_with_tag(self, string, tag, format_string=False, force=False):
        if not force and not self.print_log:
            return
        if format_string:
            self._print_fcs(f"{tag} {string}")
        else:
            print(f"{self._prefix_str()} {tag} {string}")

    def print_large_header(self, title, no_prefix=False):
        print_line()
        _figlet = Figlet()
        for _fig_line in _figlet.renderText(title).split("\n"):
            _str = _fig_line.replace("\n", "")
            if all(" " == ch for ch in _str):
                continue
            if _str:
                if no_prefix:
                    print(_str)
                else:
                    self.log(_str)
        print_line()

    def _prefix_str(self):
        date_str = ""
        prefix2_str = f" {self._log_prefix2}" if self._log_prefix2 else ""
        if self._use_timestamp:
            _fmt = "%H:%M:%S.%f" if self._use_ms else "%H:%M:%S"
            date_str = datetime.now().strftime(_fmt)
            date_str = cstr(f"[{date_str}] ", Color.DarkGrey)
        return date_str + cstr(f"({self.log_prefix})", self._log_prefix_color) + prefix2_str

    @staticmethod
    def log_general(message):
        BaseLog(verbose=True).log(message)

    @property
    def verbose(self) -> bool:
        return self.print_log

    @verbose.setter
    def verbose(self, value: bool):
        if self.print_log == value:
            return
        self.print_log = value
        self.log("enabling logging")


if __name__ == "__main__":
    class TestLog(BaseLog):
        def __init__(self):
            super().__init__(verbose=True)
            self.set_log_prefix("TESTLOG", color="random")

        def print(self):
            self.log("log")
            self.error("error")
            self.warn("warning")


    for _ in range(10):
        tl = TestLog()
        tl.print()
        tl.print_large_header("TEST HEADER")
