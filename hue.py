#!/usr/bin/env python3.8

""" Philips Hue Tools """

import http.client
import json
import random
import time
import sys

from argparse import ArgumentParser

from config import ConfigurationManager
from enum import Enum
from printing import pfcs
from util import BaseLog

from PySide6.QtWidgets import QWidget, QApplication, QPushButton, QLabel, QVBoxLayout, QColorDialog, QGroupBox, \
QGridLayout, QSlider
from PySide6.QtGui import QColor
from PySide6.QtCore import *


class Hue(Enum):
    FULL_RED = 0xffff
    FULL_GREEN = 0x639c
    FULL_BLUE = 0xb748


class Color:
    def __init__(self, bri, hue, sat):
        self.bri = bri
        self.hue = hue
        self.sat = sat


COLORS = {
    "green": Color(bri=214, hue=24469, sat=234),
    "teal": Color(bri=214, hue=42956, sat=254),
    "blue": Color(bri=254, hue=45643, sat=254),
    "purple": Color(bri=254, hue=49968, sat=221),
    "yellow": Color(bri=214, hue=9726, sat=254),
    "red": Color(bri=214, hue=65051, sat=254),
    "orange": Color(bri=214, hue=4734, sat=254),
    "pink": Color(bri=214, hue=58710, sat=166),
    "grey": Color(bri=38, hue=41484, sat=50),
    "white": Color(bri=240, hue=41484, sat=50)
}

MAX_SATURATION = 254
MAX_HUE = 0xffff
MAX_BRIGHTNESS = 254
MIN_BRIGHTNESS = 1


class LightBulb(BaseLog):
    def __init__(self, bridge, light_id, json_data):
        super().__init__(verbose=True)
        self.raw_data = json_data
        self.id = int(light_id)
        self.name = ""
        self.product_id = ""
        self.on = False
        self.bri = None
        self.hue = None
        self.sat = None
        self.bridge = bridge
        self._parse_data()
        self.set_log_prefix(f"LIGHT_{self.name.upper().replace(' ', '_')}")
        self.log(f"init done, on: {self.on}")

    def _parse_data(self):
        state = self.raw_data.get("state", {})
        self.name = self.raw_data.get("name", "")
        self.product_id = self.raw_data.get("productid", "N/A")
        if state:
            self.on = state.get("on", False)
            self.bri = state.get("bri", 0)

    def print(self, only_color_info=False, short=False):
        if short:
            pfcs(f"id: i[{self.id}] {self.product_id}:o[{self.name}]")
            return
        print(f"id: {self.id} ({self.product_id})")
        if only_color_info:
            state = self.raw_data.get("state", {})
            string = " ".join(f"{x}: {state.get(x)}" for x in [
                "bri", "hue", "sat"])
            print(string)
        else:
            print("on:", self.on)
            print(json.dumps(self.raw_data, indent=4))
        print("*" * 20)

    def set_state(self, state: bool):
        self.on = state

    def toggle(self):
        _prev = self.on
        _new = not _prev
        self.log(f"toggling state: {_prev} --> {_new}")
        self.on = _new
        self.update()

    def set_color(self, color: Color):
        self.set_hue(color.hue)
        self.set_saturation(color.sat)
        self.set_brightness(color.bri)

    def set_hue(self, hue):
        if isinstance(hue, int):
            if hue < 0:
                hue = 0
            elif hue > MAX_HUE:
                hue = MAX_HUE
        elif isinstance(hue, Hue):
            hue = hue.value
        self.hue = hue

    def set_saturation(self, sat):
        if sat < 0:
            sat = 0
        elif sat > MAX_SATURATION:
            sat = MAX_SATURATION
        self.sat = sat

    def set_brightness(self, bri):
        if bri < MIN_BRIGHTNESS:
            bri = MIN_BRIGHTNESS
        elif bri > MAX_BRIGHTNESS:
            bri = MAX_BRIGHTNESS
        self.bri = bri

    def run_color_cycler(self, transition_time=120):  # TODO thread
        new_hue = random.randint(0, 0xffff)
        self.sat = MAX_SATURATION
        self.hue = new_hue
        time_to_sleep = transition_time
        self.update(time_to_sleep - 1)
        self.bri = None
        while True:
            self.update(time_to_sleep - 1)
            time.sleep(time_to_sleep)
            while abs(new_hue - self.hue) < 1000:
                new_hue = random.randint(0, 0xffff)
            self.sat = random.randint(
                int(MAX_SATURATION * 0.8), MAX_SATURATION + 1)
            self.hue = new_hue

    def update(self, transition_time=None):
        body = {"on": self.on}
        self.log(f"state: {self.on}")
        if self.hue is not None:
            body["hue"] = self.hue
            self.log(f"hue: {self.hue}")
        if self.sat is not None:
            body["sat"] = self.sat
            self.log(f"sat: {self.sat}")
        if self.bri is not None:
            body["bri"] = self.bri
            self.log(f"brightness: {self.bri}")
        if transition_time is not None:
            body["transitiontime"] = transition_time * 10
            self.log(f"transition time: {transition_time}")
        self.bridge.post_req(f"lights/{self.id}/state", body)

    @property
    def brightness(self):
        return self.bri


class Room(BaseLog):
    def __init__(self, bridge, json_data: dict):
        super().__init__(verbose=True)
        self._data = json_data
        self._lights = []
        self._bridge: Bridge = bridge
        self.name = self._data.get("name", "N/A")
        self.set_log_prefix(f"ROOM_{self.name.upper().replace(' ', '_')}")
        self._init_lights()
        self.log("init done")

    def _init_lights(self):
        for light_id in self._data.get("lights", []):
            self.add_light(self._bridge.get_light_with_id(int(light_id)))

    def add_light(self, light: [LightBulb, None]):
        if light is None:
            return
        _id = light.id
        if _id in [_light.id for _light in self._lights]:
            return
        self._lights.append(light)
        self.log(f"added light {light.name} with id {light.id}")

    @property
    def light_count(self) -> int:
        return len(self._lights)

    @property
    def lights(self) -> list:
        return self._lights


class Bridge(BaseLog):
    class GroupType(Enum):
        Zone = "Zone",
        Room = "Room"

    def __init__(self, ip, key):
        super().__init__(verbose=True)
        self.ip = ip
        self.key = key
        self.lights = []
        self.rooms = []
        self.zones = []
        self._skip_req = False
        self._populate_lights()
        self._populate_groups()
        self.set_log_prefix(f"BRIDGE")
        self.log(f"init done -> num lights {len(self.lights)} num rooms: {len(self.rooms)}")

    def disable_req(self):
        self.log("skipping PUT requests")
        self._skip_req = True

    def get_req(self, path: str) -> dict:
        url = f"https://{self.ip}/api/{self.key}/{path}"
        conn = http.client.HTTPConnection(self.ip, timeout=10)
        conn.request("GET", url)
        result = conn.getresponse()
        res = result.read().decode('utf-8')
        conn.close()
        return json.loads(res)

    def post_req(self, path, body: dict):
        url = f"https://{self.ip}/api/{self.key}/{path}"
        self.log(f">> PUT {url} - {body}")
        if self._skip_req:
            return {}
        conn = http.client.HTTPConnection(self.ip, timeout=10)
        conn.request("PUT", url, json.dumps(body))
        result = conn.getresponse()
        res = result.read().decode('utf-8')
        conn.close()
        return json.loads(res)

    def get_light_with_id(self, light_id: int) -> [LightBulb, None]:
        for _light in self.lights:
            if light_id == _light.id:
                return _light
        return None

    def get_room_with_name(self, name: str) -> [Room, None]:
        for _room in self.rooms:
            if _room.name.lower() == name.lower():
                return _room
        return None

    def _populate_lights(self):
        for key, val in self.get_req("lights").items():
            self.lights.append(LightBulb(self, key, val))

    def _populate_groups(self):
        for _grp in self.get_req("groups").values():
            try:
                _type = self.GroupType(_grp.get("type", None))
            except ValueError as _:
                continue
            if _type == self.GroupType.Room:
                _room = Room(self, _grp)
                self.rooms.append(_room)


def get_bridge() -> [Bridge, None]:
    key = ConfigurationManager().get("hue_api_key", default=None)
    hue_ip = ConfigurationManager().get("hue_ip", default=None)
    if not hue_ip:
        print("cannot load hue_ip from settings, aborting")
        return None
    if not key:
        print("cannot load hue_api_key from settings, aborting")
        return None
    return Bridge(hue_ip, key)


def run_cli(args):
    bridge = get_bridge()
    if not bridge:
        return
    for bulb in bridge.lights:
        if bulb.id == args.id:
            if args.print_info:
                bulb.print()
            if args.print_color:
                bulb.print(only_color_info=True)
            need_update = False
            if args.state is not None:
                bulb.set_state(bool(args.state))
                need_update = True
            if args.hue is not None:
                bulb.set_hue(args.hue)
                need_update = True
            if args.sat is not None:
                bulb.set_saturation(args.sat)
                need_update = True
            if args.bri is not None:
                bulb.set_brightness(args.bri)
                need_update = True
            if args.color is not None:
                bulb.set_color(COLORS[args.color])
                need_update = True
            if need_update:
                bulb.update(args.delay)
            if args.run_cycler:
                try:
                    bulb.run_color_cycler()
                except KeyboardInterrupt:
                    return
        if args.list_lights:
            bulb.print(short=True)


class LightControl(QWidget, BaseLog):
    def __init__(self, light: LightBulb):
        QWidget.__init__(self)
        BaseLog.__init__(self, verbose=True)
        self._light: LightBulb = light
        self._btn = self._init_toggle_button()
        self._update_button()
        self._slider = self._init_brightness_slider()
        self._update_timer = self._init_update_timer()
        self._color_picker = self._init_color_picker()
        self._cp_btn = QPushButton("Set Color")
        self._cp_btn.clicked.connect(self._open_color_picker)
        self._need_update = False
        self.set_log_prefix(f"CONTROL_{self._light.name.upper().replace(' ', '_')}")
        self.log("init")

    @Slot()
    def toggle(self):
        self._light.toggle()
        self._update_button()

    @Slot()
    def _handle_slider_val(self, value):
        self._light.set_brightness(value)
        self.log(f"brightness: {value}")
        self._need_update = True

    @Slot()
    def _update_light(self):
        if not self._need_update:
            return
        self.log("updating light")
        self._light.update()
        self._need_update = False

    @Slot()
    def _handle_color_picker_changed(self, color: QColor):
        self._light.set_hue(color.hue() * 257) # TODO: fix hue vals
        self._light.set_saturation(color.saturation())
        self._need_update = True

    @property
    def name(self):
        return self._light.name

    @property
    def toggle_btn(self):
        return self._cp_btn

    @property
    def show_color_picker_btn(self):
        return self._btn

    @property
    def slider(self):
        return self._slider

    def _update_button(self):
        self._btn.setText(f"Toggle {'OFF' if self._light.on else 'ON'}")

    def _init_toggle_button(self):
        _btn = QPushButton("--")
        _btn.clicked.connect(self.toggle)
        return _btn

    def _init_brightness_slider(self):
        _slider = QSlider(Qt.Orientation.Horizontal)
        _slider.setMaximum(MAX_BRIGHTNESS)
        _slider.setMinimum(MIN_BRIGHTNESS)
        _slider.setFixedWidth(250)
        _slider.valueChanged.connect(self._handle_slider_val)
        try:
            _slider.setValue(self._light.brightness)
        except TypeError:
            self.warn("light brightness is not int")
        return _slider

    def _init_update_timer(self):
        _timer = QTimer()
        _timer.setInterval(100)
        _timer.timeout.connect(self._update_light)
        _timer.start()
        return _timer

    def _init_color_picker(self):
        _cp = QColorDialog()
        _cp.currentColorChanged.connect(self._handle_color_picker_changed)
        return _cp

    @Slot()
    def _open_color_picker(self):
        self._color_picker.open()

    @property
    def color_picker(self):
        return self._color_picker


class HueControlWindow(QWidget, BaseLog):
    def __init__(self, bridge):
        QWidget.__init__(self)
        BaseLog.__init__(self, verbose=True)
        self.setWindowTitle("Hue Controller")
        self._light_ctrl = []
        self._bridge = bridge
        self.layout = QVBoxLayout(self)
        for _room in self._bridge.rooms:
            self.layout.addWidget(self._setup_room_widget(_room))
        self.set_log_prefix("HUE_CONTROL_WINDOW")

    def _setup_room_widget(self, room: Room):
        _grp = QGroupBox(title=room.name)
        _layout = QGridLayout()
        _row_num = 0
        for _light in room.lights:
            _lc = LightControl(_light)
            self._light_ctrl.append(_lc)
            _lbl = QLabel(f" > {_light.name}")
            _layout.addWidget(_lbl, _row_num, 0)
            _layout.addWidget(_lc.toggle_btn, _row_num, 1)
            _layout.addWidget(_lc.show_color_picker_btn, _row_num, 2)
            _layout.addWidget(_lc.slider, _row_num, 3)
            _row_num += 1
        _grp.setLayout(_layout)
        return _grp

    @Slot()
    def show_diag(self):
        self._color_diag.setWindowFlag(Qt.WindowStaysOnTopHint)
        self._color_diag.show()

    @Slot()
    def color_picker_color_changed(self, color):
        print(color)


def run_gui(args):
    bridge = get_bridge()
    if not bridge:
        return
    if args.skip_req:
        bridge.disable_req()
    app = QApplication([])
    widget = HueControlWindow(bridge)
    widget.resize(600, 600)
    widget.show()

    sys.exit(app.exec())


def gen_args():
    parser = ArgumentParser("Hue Tools")
    sub_parsers = parser.add_subparsers(required=False)
    sub_gui = sub_parsers.add_parser("gui")
    sub_gui.set_defaults(func=run_gui)
    sub_gui.add_argument("--no-req", action="store_true", dest="skip_req")
    sub_cli = sub_parsers.add_parser("cli")
    sub_cli.set_defaults(func=run_cli)
    sub_cli.add_argument("id",
                         help="lightbulb id",
                         nargs="?",
                         default=-1,
                         type=int)
    sub_cli.add_argument("--state",
                         type=int,
                         default=None)
    sub_cli.add_argument("--hue",
                         type=int,
                         default=None)
    sub_cli.add_argument("--saturation",
                         "-s",
                         type=int,
                         dest="sat",
                         default=None)
    sub_cli.add_argument("--color",
                         "-c",
                         type=str,
                         choices=[x for x in COLORS],
                         dest="color",
                         default=None)
    sub_cli.add_argument("--brightness",
                         "-b",
                         type=int,
                         dest="bri",
                         default=None)
    sub_cli.add_argument("--transition-time",
                         "-t",
                         default=None,
                         type=int,
                         dest="delay",
                         help="transition time in seconds")
    sub_cli.add_argument("--list",
                         action="store_true",
                         dest="list_lights")
    sub_cli.add_argument("--info",
                         action="store_true",
                         dest="print_info")
    sub_cli.add_argument("--info-color",
                         action="store_true",
                         dest="print_color")
    sub_cli.add_argument("--cycler",
                         action="store_true",
                         dest="run_cycler")
    return parser.parse_args()


def main():
    args = gen_args()
    try:
        args.func(args)
    except AttributeError as _:
        pass


if __name__ == "__main__":
    main()
