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

try:
    from PySide6.QtWidgets import QWidget, QApplication, QPushButton, QLabel, QVBoxLayout
    from PySide6.QtCore import *
    QT_AVAILABLE = True
except ImportError as _:
    QT_AVAILABLE = False


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
        print(f"setting \"{self.name}\":")
        print(f"state: {self.on}")
        if self.hue is not None:
            body["hue"] = self.hue
            print(f"hue: {self.hue}")
        if self.sat is not None:
            body["sat"] = self.sat
            print(f"sat: {self.sat}")
        if self.bri is not None:
            body["bri"] = self.bri
            print(f"brightness: {self.bri}")
        if transition_time is not None:
            body["transitiontime"] = transition_time * 10
            print(f"transition time: {transition_time}")
        self.bridge.post_req(f"lights/{self.id}/state", body)


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
        self._populate_lights()
        self._populate_groups()
        self.log(f"init done -> num lights {len(self.lights)} num rooms: {len(self.rooms)}")

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


class HueControlWindow(QWidget, BaseLog):
    def __init__(self, bridge):
        QWidget.__init__(self)
        BaseLog.__init__(self, verbose=True)
        self._bridge = bridge
        self._room = bridge.get_room_with_name("sovrum")
        self.button = QPushButton("TOGGLE TEST!")
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.toggle)
        self.set_log_prefix("HUE_CONTROL_WINDOW")

    @Slot()
    def toggle(self):
        if not self._room:
            self.log("no room....")
        for light in self._room.lights:
            light.toggle()


def run_gui(args):
    if not QT_AVAILABLE:
        print("QT/GUI not available")
        return
    bridge = get_bridge()
    if not bridge:
        return
    app = QApplication([])
    widget = HueControlWindow(bridge)
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())


def gen_args():
    parser = ArgumentParser("Hue Tools")
    sub_parsers = parser.add_subparsers(required=False)
    sub_gui = sub_parsers.add_parser("gui")
    sub_gui.set_defaults(func=run_gui)
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
