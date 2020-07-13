#!/usr/bin/env python3

import re
from enum import Enum
from pathlib import Path

from printing import fcs


class SrtFileEncoding(Enum):
    UTF8_BOM = "utf-8-sig"


class RegexStr(Enum):
    TimeStamps = r"(?P<start_time>\d{2}\:\d{2}\:\d{2}\,\d{3})\s" \
                 r"-->\s(?P<end_time>\d{2}\:\d{2}\:\d{2}\,\d{3})"
    Index = r"(?P<index>^\d{1,5}$)"
    TimeParts = r"(?P<hh>\d{2})\:(?P<mm>\d{2})\:(?P<ss>\d{2})\,(?P<ms>\d{3})"


class SrtEntry():
    def __init__(self, index, start_time: str, end_time: str, lines: list):
        self.index = int(index)
        self.start_time_str = start_time
        self.end_time_str = end_time
        self.lines = lines
        self.start_ms = 0
        self.end_ms = 0
        self.parse_ok = self._process()

    def _process(self):
        for time_str in [self.start_time_str, self.end_time_str]:
            match = re.match(RegexStr.TimeParts.value, time_str)
            if match and all(x in match.groupdict() for x in ["hh", "mm", "ss", "ms"]):
                gdict = match.groupdict()
                time_ms = int(gdict["ms"])
                time_ms += int(gdict["ss"]) * 1000
                time_ms += int(gdict["mm"]) * 1000 * 60
                time_ms += int(gdict["hh"]) * 1000 * 60 * 60
                if time_str == self.start_time_str:
                    self.start_ms = time_ms
                else:
                    self.end_ms = time_ms
            else:
                return False
        return True

    def duration(self):
        return self.end_ms - self.start_ms

    def valid(self):
        return self.parse_ok


class SrtFile():
    LOG_PREFIX = "SRT_FILE"

    def __init__(self, path: Path = None, verbose=False):
        self.path = path
        self.file_contents = []
        self.entries = []
        self.print_log = verbose

        self.load_srt()

    def log(self, info_str, info_str_line2=""):
        if not self.print_log:
            return
        print(fcs(f"i[({self.LOG_PREFIX})]"), info_str)
        if info_str_line2:
            spaces = " " * len(f"({self.LOG_PREFIX}) ")
            print(f"{spaces}{info_str_line2}")

    def set_path(self, path: Path):
        self.path = path

    def load_srt(self):
        with open(self.path, encoding=SrtFileEncoding.UTF8_BOM.value, errors="replace") as subf:
            self.file_contents = subf.read().splitlines()
        matches = {}
        lines = []
        for line in self.file_contents:
            found_regex = False
            for rex in [RegexStr.Index, RegexStr.TimeStamps]:
                match = re.match(rex.value, line)
                if match:
                    found_regex = True
                    matches.update(match.groupdict())
            if not found_regex and line != "":
                lines.append(line)
            if line == "" and all(x in matches for x in ["start_time", "end_time", "index"]):
                matches["lines"] = lines
                entry = SrtEntry(**matches)
                if not entry.valid():
                    index = matches["index"]
                    self.log(
                        fcs(f"e[error] failed parse entry for index {index}!"))
                self.entries.append(entry)
                matches = {}
                lines = []
        self.log(f"loaded {len(self.entries)} entries from srt file")


def main():
    srt_file = SrtFile(Path("ref/sub.sv.srt"), verbose=True)


if __name__ == "__main__":
    main()
