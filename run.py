'''Run commands on local system'''

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
        print(f"{CSTR('command failed with return code: {ret.returncode}', 'red')}")
    return ret.returncode == 0
