#!/usr/bin/env python3.6

'''Personal script to interact with torrent-server'''

import subprocess
import shlex
import os
import re
import argparse
import filetools
from datetime import datetime
from printout import print_class as pr
from config import configuration_manager as cfg
import db_mov as movie_database
import db_tv as tv_database
import tvshow


DB_MOV = movie_database.database()
DB_TV = tv_database.database()

assert DB_MOV.load_success(), "Movie database could not be loaded!"
assert DB_TV.load_success(), "TV database could not be loaded!"

PRINT = pr(os.path.basename(__file__))
CONFIG = cfg()
PARSER = argparse.ArgumentParser(description='WBTools')
PARSER.add_argument('func', type=str, help='WB command: new, get')
PARSER.add_argument('-t', '--type', dest='type', default=None,
                    help='filter new list by types: m, t, s')
PARSER.add_argument('-f', '--filter', dest='filter', default=None,
                    help='filter new list by string')
PARSER.add_argument('-nodb', dest='nodb', action="count", default=False,
                    help='Display only items not in db')
PARSER.add_argument('-dl', dest='dl', default=None,
                    help='Files to download, name or number. Can be comma separated,'
                    'or span (numbers only)')
ARGS = PARSER.parse_args()


class FileList:
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.raw_lines = self._raw_data_to_lines(raw_data)
        self.line_data = []
        counter = 1
        for line in self.raw_lines:
            d = self._line_to_dict(line)
            if d:
                d["count"] = counter
                counter += 1
                self.line_data.append(d)

    def print_list(self, list_type, name_filter, nodb):
        for line in self.line_data:
            if line['guessed_type']:
                type = line['guessed_type'][0]
            else:
                type = "-"
            name = line['name']
            if name_filter:
                na = re.compile(name_filter)
                result = na.search(name)
                if result is None:
                    continue
            if list_type and list_type != type:
                continue
            if nodb and line['in_db']:
                continue
            dtstr = line['date'].strftime("%Y-%m-%d %H:%M:%S")
            PRINT.info(dtstr, end_line=False)
            if line['in_db']:
                PRINT.color_brackets(" [indb]", "green", end_line=False)
            else:
                PRINT.color_brackets(" [nodb]", "yellow", end_line=False)
            if line['guessed_type']:
                PRINT.color_brackets("[{}]".format(
                    type), "green", end_line=False)
            else:
                PRINT.color_brackets("[{}]".format("-"), "red", end_line=False)
            PRINT.output(" {0:0>3} ".format(line['count']), end_line=False)
            PRINT.color_brackets("[ {} ]".format(name), "blue")

    def has_file(self, string):
        for line in self.line_data:
            if line['name'] == string:
                return True
        return False

    def get_file_from_num(self, num):
        if int(num) > len(self.line_data) or int(num) < 1:
            return None
        for line in self.line_data:
            if str(line['count']) == str(num):
                return line['name']
        return None

    def _raw_data_to_lines(self, raw_data):
        lines = str(raw_data).split("\\n")
        return lines

    def _line_to_dict(self, raw_line):
        splits = raw_line.split()
        if len(splits) < 8:
            return None
        name = splits[7]
        if len(splits) > 8:
            for i in range(8, len(splits)):
                name += " " + splits[i]
        dt_str = "{} {}".format(splits[5], splits[6])
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
        type_guess = filetools.guess_folder_type(name)
        in_db = False
        if type_guess == "movie":
            mov_fixed = filetools.fix_invalid_folder_or_file_name(name)
            in_db = DB_MOV.exists(mov_fixed.replace(".mkv", ""))
        if type_guess == "episode":
            show_s = tvshow.guess_ds_folder(name)
            if DB_TV.exists(show_s):
                in_db = DB_TV.has_ep(show_s, name)
                if not in_db:
                    in_db = DB_TV.has_ep(show_s, f"{name}.mkv")
        return {'name': name, 'date': dt, 'in_db': in_db,
                'guessed_type': type_guess}


class ListCommand:
    def __init__(self, directory, remote=False):
        self.dir = directory
        self.ssh_server = remote
        self.command = self._generate_command()
        self.args = self._command_to_args(self.command)
        self.output = self._run()
        self.files = FileList(self.output)

    def print_files(self, list_type=None, name_filter=None, nodb=False):
        self.files.print_list(list_type, name_filter, nodb)

    def get_file_list(self):
        return self.files

    def _generate_command(self):
        lsc = "ls -trl --time-style=\"+%Y-%m-%d %H:%M\" {}".format(self.dir)
        if self.ssh_server:
            lsc = "ssh {} {}".format(self.ssh_server, lsc)
        return lsc

    def _command_to_args(self, command):
        arg = shlex.shlex(command)
        arg.quotes = '"'
        arg.whitespace_split = True
        arg.commenters = ''
        return list(arg)

    def _run(self):
        PRINT.info("running command: [ {} ]".format(self.command))
        process = subprocess.Popen(self.args, stdout=subprocess.PIPE)
        out, err = process.communicate()
        return out


class SCPCommand:
    def __init__(self, server=None, queue_list=[]):
        self.dldir = CONFIG.get_setting("path", "download")
        self.ssh_server = server
        self.queue = queue_list
        self.command_queue = []
        for item in self.queue:
            if item:
                self.command_queue.append(self._generate_scp_dl_command(item))
        self._run()

    def _generate_scp_dl_command(self, dl_item):
        escape_chars = [' ', '(', ')', '[', ']', "'"]
        for char in escape_chars:
            replacement = f"\\\\\\{char}"
            dl_item = dl_item.replace(char, replacement)
        scp_command = f"scp -r {self.ssh_server}:~/files/{dl_item} {self.dldir}"
        return scp_command

    def _run(self):
        PRINT.info("will download {} file{}!".format(len(self.command_queue),
                                                     "" if len(self.command_queue) == 1 else "s"))
        count = 1
        for command in self.command_queue:
            PRINT.info(f"item [ {count} of {len(self.command_queue)} ]")
            count += 1
            PRINT.info("running command: [ {} ]".format(command))
            subprocess.call(command, shell=True)


def list_new_files(args):
    lsc = ListCommand("~/files", remote="wb")
    lsc.print_files(list_type=args.type, name_filter=args.filter,
                    nodb=args.nodb)


def download_files(args):
    if not args.dl:
        PRINT.info("wbget: Did not supply any dl!", category="error")
        exit()
    dl_list = args.dl.split(',')
    number_span_regex = re.compile("^\\d{1,3}-\\d{1,3}$")
    number_regex = re.compile("^\\d{1,3}$")
    lsc = ListCommand("~/files", remote="wb")
    file_list = lsc.get_file_list()
    queue = []
    for item in dl_list:
        result = number_span_regex.search(item)
        if result != None:
            span = item.split('-')
            for i in range(int(span[0]), int(span[1]) + 1):
                queue.append(file_list.get_file_from_num(i))
                continue
        result = number_regex.search(item)
        if result != None:
            queue.append(file_list.get_file_from_num(item))
            continue
        if file_list.has_file(item):
            queue.append(item)
    scpc = SCPCommand("wb", queue)


if(ARGS.func == "new"):
    list_new_files(ARGS)
elif(ARGS.func == "get"):
    download_files(ARGS)
else:
    PRINT.error("Wrong command: [{}".format(ARGS.func))
