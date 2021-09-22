#!/usr/bin/python3

from printout import fcs
from run import local_command

from argparse import ArgumentParser
from pathlib import Path


def gen_args():
    parser = ArgumentParser("finder script")
    parser.add_argument("--full-paths",
                        "-p",
                        action="store_true",
                        dest="full_paths")
    parser.add_argument("--highlight",
                        "-c",
                        dest="highlight",
                        default="")
    parser.add_argument("--filter",
                        "-f",
                        dest="filter",
                        default="")
    parser.add_argument("--first",
                        action="store_true",
                        help="show only first match")
    parser.add_argument("--subprocess",
                        "-s",
                        default="",
                        help="run command, use {} to insert filename")
    return parser.parse_args()


class FileInfo():
    def __init__(self, file_path, args):
        self.path = file_path
        self.args = args
        if args.highlight:
            self.highlighted = str(file_path).replace(
                args.highlight, fcs(f"b[{args.highlight}]"))
        else:
            self.highlighted = ""
        self.filename = file_path.name
        self.colorized_filename = fcs(f"i[{file_path.name}]")

    def print(self):
        if self.args.full_paths:
            if self.args.highlight:
                print(self.highlighted)
            else:
                print(str(self.path).replace(
                    self.filename, self.colorized_filename))
        else:
            print(self.filename)

    def subp(self, command):
        command = command.replace("{}", self.filename)
        local_command(command, hide_output=False, print_info=True)

    def matches_filter(self) -> bool:
        if not self.args.filter:
            return True
        if not "*" in self.args.filter:
            return self.args.filter.lower() in self.filename.lower()
        if self.args.filter == "*":
            return True
        strs = self.args.filter.lower().split("*")
        return all(st in self.filename.lower() for st in strs)


def main():
    args = gen_args()
    current_path = Path.cwd()
    files = current_path.glob("*.*")
    for file_path in sorted(files):
        file_info = FileInfo(file_path, args)
        if not file_info.matches_filter():
            continue
        file_info.print()
        if args.subprocess:
            file_info.subp(args.subprocess)
        if args.first:
            break


if __name__ == "__main__":
    main()
