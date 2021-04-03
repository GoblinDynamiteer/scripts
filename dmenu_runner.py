#!/usr/bin/env python3

import subprocess
import time
import webbrowser
from dataclasses import dataclass
from enum import Enum
from config import ConfigurationManager
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
    font: str = "Monospace-{}:normal".format(ConfigurationManager().get("dmenu_font_size", default=10))
    lines: int = 40


class WorkspaceName(Enum):
    GnomeSettings = "settings"

    def __str__(self):
        return str(self.value)


def show_notification(message, title=None, time_ms=1200):
    if title:
        subprocess.Popen(['notify-send', title, message, "-t", str(time_ms)])
    else:
        subprocess.Popen(['notify-send', message, "-t", str(time_ms)])


def show_notification_error(message):
    subprocess.Popen(['notify-send', "ERROR:" + str(__file__),
                      str(message), "-t", str(5000), "-u", "critical"])


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


def dmenu_show(command_list: list, config: DmenuConfig = None):
    if config is None:
        config = DmenuConfig()
    return dmenu.show(command_list,
                      font=config.font,
                      case_insensitive=config.case_insensitive,
                      foreground_selected=config.color_selected_foreground,
                      background=config.color_bar_background,
                      lines=config.lines)


def dmenu_poweroff():
    cmd_str_pwr_off = "Power off computer"
    commands = [cmd_str_pwr_off, "Cancel"]
    config = DmenuConfig()
    config.color_selected_foreground = "red"
    ret = dmenu_show(commands, config)
    if cmd_str_pwr_off == ret:
        i3_exec("poweroff")


def open_web(url: str):
    webbrowser.open_new_tab(url)
    i3_conn = i3ipc.Connection()
    i3_conn.command("workspace 3:web")


def subprocces_popen(cmd: str):
    if not cmd:
        return
    subprocess.Popen(cmd.split(" "))


def get_pycharm_path():
    bin_path = Path.home() / "bin"
    for item in bin_path.glob("**/pycharm.sh"):
        return item
    return None


class Entry:
    def __init__(self, label, func=None, args=None):
        if isinstance(label, list):
            self.labels = label
        else:
            self.labels = [label]
        if func is None:
            self.funcs = []
        else:
            self.funcs = [(func, args)]

    def execute(self):
        for func, args in self.funcs:
            if args is None:
                func()
            elif isinstance(args, str):
                func(*args.split(" "))
            elif type(args) in [list, tuple]:
                func(*args)
            elif isinstance(args, dict):
                func(**args)

    def add_label(self, label):
        self.labels.append(label)

    def add_func(self, func, args=None, sleep_time_before_exec: int = 0):
        try:
            if sleep_time_before_exec > 0:
                self.funcs.append((time.sleep, [sleep_time_before_exec]))
            self.funcs.append((func, args))
        except Exception as _error:
            show_notification_error("Entry::add_func:\n" + str(_error))


def init_entries():
    ret_list = []
    ret_list.append(Entry("Firefox", i3_exec, "firefox"))
    ret_list.append(Entry("Settings",
                          i3_exec,
                          {"command": "env XDG_CURRENT_DESKTOP=GNOME gnome-control-center",
                           "workspace_name": str(WorkspaceName.GnomeSettings)}))
    ret_list.append(Entry("PowerOff", dmenu_poweroff))
    pycharm_path = get_pycharm_path()
    if pycharm_path:
        ret_list.append(Entry("PyCharm", i3_exec, {"command": pycharm_path}))
    return ret_list


def main():
    try:
        entries = init_entries()
    except Exception as _error:
        show_notification_error("init_entries:\n" + str(_error))
        return
    label_list = []
    for e in entries:
        label_list.extend(e.labels)
    ret = dmenu_show(sorted(label_list, key=str.casefold), config=DmenuConfig())
    for entry in entries:
        if ret in entry.labels:
            entry.execute()
            break


if __name__ == "__main__":
    main()
