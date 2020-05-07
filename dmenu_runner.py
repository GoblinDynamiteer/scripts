#!/usr/bin/env python3

import configparser
import re
import subprocess
import time
import webbrowser
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import dmenu
import i3ipc


@dataclass
class DmenuConfig:
    """ Set/Get colors for dmenu"""
    case_insensitive: bool = True
    color_selected_foreground: str = "white"
    color_selected_background: str = "#042C44"
    color_bar_background: str = "black"
    lines: int = 40


def show_notification(message, title=None, time_ms=1200):
    if title:
        subprocess.Popen(['notify-send', title, message, "-t", str(time_ms)])
    else:
        subprocess.Popen(['notify-send', message, "-t", str(time_ms)])


DMENU_COLORS = {"sf": "red", "sb": "orange", "nb": "black"}
SOURCE_PENV_CMD = r"source ~/scripts/python-venv/bin/activate.fish"


def i3_exec(command, workspace_name=None, layout=None, sleep_time=1, notify=False):
    i3_conn = i3ipc.Connection()
    if workspace_name:
        i3_conn.command(f"workspace {workspace_name}")
        time.sleep(0.1)
    if not isinstance(command, list):
        command = [command]
    for cmd in command:
        if notify:
            show_notification(cmd, title="Starting application", time_ms=1000)
        i3_conn.command(f"exec {cmd}")
        time.sleep(sleep_time)


def new_terminal(start_command="", workspace_name=None):
    cmd = f'gnome-terminal -- fish -C "{start_command}"'
    i3_exec(cmd, workspace_name=workspace_name)


def dmenu_show(command_list: list):
    return dmenu.show(command_list,
                      case_insensitive=DmenuConfig.case_insensitive,
                      foreground_selected=DmenuConfig.color_selected_foreground,
                      background=DmenuConfig.color_bar_background,
                      lines=DmenuConfig.lines)


def open_web(url: str):
    webbrowser.open_new_tab(url)
    i3_conn = i3ipc.Connection()
    i3_conn.command("workspace 3:web")


def subprocces_popen(cmd: str):
    if not cmd:
        return
    subprocess.Popen(cmd.split(" "))


if __name__ == "__main__":
    COMMANDS = {"Firefox": "firefox",
                "VsCode": "code",
                "Lock": "i3lock --c 000000",
                "Shutdown": "poweroff",
                "Poweroff": "poweroff",
                "xkill": "xkill",
                "Okular": "okular",
                "PDF Viewer": "okular",
                "Nautilus": "nautilus",
                "arandr": "arandr",
                "Weather": None
                }
    RET = dmenu_show(sorted(COMMANDS.keys(), key=str.casefold))
    if "Weather" in RET:
        new_terminal(start_command="curl https://wttr.in/Norrkoping",
                     workspace_name="wttr.in")
    elif "ssh " in RET:
        SERVER = RET.replace('ssh ', '')
        show_notification(
            f"connecting to: {SERVER}", title="ssh command")
        new_terminal(start_command=RET, workspace_name=f"ssh:{SERVER}")
    elif "google " in RET:
        QUERY = RET.replace('google ', '')
        open_web(f"https://www.google.com/search?q={QUERY.replace(' ', '+')}")
    else:
        RET_OP = COMMANDS.get(RET, None)
        if RET_OP:
            i3_exec(RET_OP)
