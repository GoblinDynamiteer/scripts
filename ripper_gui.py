from pathlib import Path
from typing import List
import sys
import argparse
import os
import json

from dataclasses import dataclass

from PySide6.QtWidgets import QWidget, QApplication, QPushButton, QGridLayout, QStyleFactory, QLineEdit, QListWidget, \
    QListWidgetItem, QFileDialog, QLabel
from PySide6.QtCore import Slot

from ripper import download_episodes
from ripper_helpers import EpisodeLister, EpisodeData

from base_log import BaseLog


def get_args():  # TODO: hack to make it work, create new Settings class or similar to pass to download_episodes
    parser = argparse.ArgumentParser(description="ripper")
    parser.add_argument("--dir", type=str, default=os.getcwd())
    parser.add_argument("--title-in-filename",
                        action="store_true", dest="use_title")
    parser.add_argument("--sub-only", "-s",
                        action="store_true", dest="sub_only")
    parser.add_argument("--get-last", default=0, dest="get_last")
    parser.add_argument("--download-last-first", "-u",
                        action="store_false", dest="use_ep_order")
    parser.add_argument("--filter", "-f", type=str, default="")
    parser.add_argument("--simulate", action="store_true", help="run tests")
    parser.add_argument("--verbose", "-v", action="store_true", dest="verb")
    parser.add_argument("--save-json-to-file", "-j", action="store_true", dest="save_debug_json")
    return parser.parse_args()


@dataclass
class GuiSettings:
    dl_dir: str = ""


def load_settings() -> GuiSettings:
    _file = Path(__file__).parent / "ripper_settings.json"
    with open(_file, "r") as fp:
        _settings = json.load(fp)
        return GuiSettings(dl_dir=_settings.get("gui", {}).get("dl_dir", ""))


class Window(QWidget, BaseLog):
    def __init__(self):
        QWidget.__init__(self)
        BaseLog.__init__(self, verbose=True)
        self.setWindowTitle("Ripper! ;D")
        self._args = get_args()
        self._grid = QGridLayout()
        self.button_change_style = QPushButton("Change Style")
        self._url_input = QLineEdit()
        self._btn_list = QPushButton("List Episodes")
        self._btn_download = QPushButton("Download Selected Episodes")
        self._btn_dest = QPushButton("Select Destination")
        self._lbl_dest = QLabel("")
        self._btn_download.setDisabled(True)
        # self._grid.addWidget(self.button_change_style, 3, 1)
        self._grid.addWidget(self._btn_download, 3, 0)
        self._grid.addWidget(self._lbl_dest, 4, 0)
        self._grid.addWidget(self._btn_dest, 4, 1)
        self._grid.addWidget(self._url_input, 0, 0)
        self._grid.addWidget(self._btn_list, 0, 1)
        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self._ep_list: List[EpisodeData]
        self._grid.addWidget(self._list, 1, 0, 1, 1)
        self._init()
        self.setLayout(self._grid)

    def _init(self):
        self._update_dest()
        self._btn_list.clicked.connect(self._list_eps)
        self._btn_download.clicked.connect(self._download)
        self._btn_dest.clicked.connect(self._select_dest)

    def _update_dest(self):
        _settings: GuiSettings = load_settings()
        self._lbl_dest.setText(f"dest: {_settings.dl_dir}")

    @Slot()
    def _select_dest(self):
        _dialog = QFileDialog()
        _dialog.setFileMode(QFileDialog.FileMode.Directory)
        _dialog.exec()
        _selected = _dialog.selectedFiles()
        if _selected:
            self._args.dir = _selected[0]
            self._update_dest()

    @Slot()
    def _list_eps(self):
        _lister = EpisodeLister.get_lister(self._url_input.text())
        _eps = _lister.get_episodes()
        if _eps:
            self._ep_list = _eps
            self._btn_download.setDisabled(False)
            self._add_to_list()

    @Slot()
    def _download(self):
        _selected = [i.text() for i in self._list.selectedItems()]
        _eps_to_dl = [e for e in self._ep_list if str(e) in _selected]
        download_episodes(_eps_to_dl, self._args)

    def _add_to_list(self):
        for ep in self._ep_list:
            _item = QListWidgetItem(str(ep))
            self._list.addItem(_item)


def main():
    app = QApplication([])

    # print(QStyleFactory.keys())

    def change_style():
        _valid = QStyleFactory.keys()
        _now = app.style().name()
        print(_now)
        try:
            _next_ix = _valid.index(_now) + 1
        except ValueError as _:
            _next_ix = _valid.index(_now.title()) + 1
        try:
            _next_str = _valid[_next_ix]
        except IndexError as _:
            _next_str = _valid[0]
        app.setStyle(QStyleFactory.create(_next_str))

    widget = Window()
    widget.resize(600, 600)
    widget.button_change_style.clicked.connect(change_style)
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
