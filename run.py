'''Run commands on local system'''

import os
import subprocess
import str_o

PRINT = str_o.PrintClass(os.path.basename(__file__))


def local_command(command, hide_output=True):
    "Run a local command"
    print(f"{PRINT.color_str('local', 'blue')} : {command}")
    if hide_output:
        ret = subprocess.run(command, shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        ret = subprocess.run(command, shell=True)
    return ret
