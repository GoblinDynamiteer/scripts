'''Run commands on local system'''

import os
import shlex
import subprocess

import printing
import util

CSTR = printing.to_color_str


def local_command(command, hide_output: bool = True, print_info: bool = True) -> bool:
    "Run a local command, returns True if command was successful"
    if print_info:  # prints what command is run
        print(f"{CSTR('local', 'blue')} : {command}")
    if hide_output:  # hides shell ouput from command
        ret = subprocess.run(command, shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        ret = subprocess.run(command, shell=True)
    if ret.returncode:
        print(f"{CSTR(f'command failed with return code: {ret.returncode}', 'red')}")
    return ret.returncode == 0


def local_command_get_output(command):
    "Run a local command, returns the output"
    ret = subprocess.run(command, shell=True, encoding='utf-8',
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ret.returncode == 0:
        return ret.stdout if ret.stdout else ret.stderr
    return False


def remote_command_get_output(command, host):
    "Run a command on a remote host, returns the output"
    command = f"ssh {host} '{command}'"
    return local_command_get_output(command)


def _executable(file_path):
    return os.path.isfile(file_path) and os.access(file_path, os.X_OK)


def program_exists(program):
    "Determine if a command/program is available"
    return command_exists(program)


def command_exists(command):
    "Determine if a command/program is available"
    fpath, _ = os.path.split(command)
    if fpath and _executable(command):
        return True
    for path in os.environ["PATH"].split(os.pathsep):
        exe_file = os.path.join(path, command)
        if _executable(exe_file):
            return True
    return False


def extract(compressed_file: 'full path', destination, create_dirs=True, overwrite=True):
    "Extract files with fancy color output"
    if not util.is_file(compressed_file):
        print(
            f'compressed_file {CSTR(compressed_file, "orange")} does not exist!')
        return False
    if not util.is_dir(destination):
        if create_dirs:
            os.makedirs(destination)
            print(f'extract: created dir {CSTR(destination, "lblue")}')
        else:
            print(
                f'extract: destination {CSTR(destination, "orange")} does not exist!')
            return False
    # just support rar for now
    file_name = util.filename_of_path(compressed_file)
    print(f'extracting  {CSTR(file_name, "lblue")}')
    print(f'destination {CSTR(destination, "lblue")}')
    overwrite_arg = '-o+' if overwrite else ''
    command = shlex.split(
        f'unrar e {overwrite_arg} "{compressed_file}" "{destination}"')
    process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=1)
    while process.poll() is None:
        byte_line = process.stdout.readline()
        line = byte_line.decode()
        if '%' in line:
            percentage_done = util.parse_percent(line)
            print(f'\r{file_name}  {CSTR(percentage_done, "lgreen")}', end='')
    print()
    if process.returncode == 0:
        print(CSTR('done!', 'lgreen'))
        return True
    print(CSTR('extract failed!', 'red'))
    return False


def move_file(source_file, destination, create_dirs=False, new_filename=None):
    "Custom file move method using mv command in the background"
    if not util.is_file(source_file):
        print(
            f'source {CSTR(source_file, "orange")} does not exist!')
        return False
    if not util.is_dir(destination) and create_dirs:
        os.makedirs(destination)
        print(f'extract: created dir {CSTR(destination, "lblue")}')
    elif not util.is_dir(destination) and not create_dirs:
        print(f'destination {CSTR(destination, "red")} does not exists!')
        return False
    print(f'moving  {CSTR(source_file, "lblue")}')
    if new_filename:
        command = f'mv {source_file} \"{destination}/{new_filename}\"'
        print(f'destination {CSTR(f"{destination}/{new_filename}", "lblue")}')
    else:
        command = f'mv {source_file} \"{destination}\"'
        print(f'destination {CSTR(destination, "lblue")}')
    if local_command(command, hide_output=True, print_info=False):
        print(CSTR('done!', 'lgreen'))
        return True
    print(CSTR('move failed!', 'red'))
    return False


def rename_file(source_file, destination):
    "Custom file move/rename method using mv command in the background"
    if not util.is_file(source_file):
        print(
            f'source {CSTR(source_file, "orange")} does not exist!')
        return False
    command = f'mv {source_file} \"{destination}\"'
    return local_command(command, hide_output=True, print_info=False)
