'''Run commands on local system'''

import os
import subprocess

import printing

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
