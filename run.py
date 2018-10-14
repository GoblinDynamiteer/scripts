'''Run commands on local system'''

import subprocess
import str_o

CSTR = str_o.to_color_str


def local_command(command, hide_output: bool = True, print_info: bool = True):
    "Run a local command"
    if print_info:
        print(f"{CSTR('local', 'blue')} : {command}")
    if hide_output:
        ret = subprocess.run(command, shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        ret = subprocess.run(command, shell=True)
    return ret
