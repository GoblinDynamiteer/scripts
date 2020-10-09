#!/usr/bin/env python3.8

""" Philips Hue Tools """


import http.client
import json

from argparse import ArgumentParser

from config import ConfigurationManager
from enum import Enum

class Hue(Enum):
    FULL_RED = 0xffff
    FULL_GREEN = 0x639c
    FULL_BLUE = 0xb748

MAX_SATURATION = 254
MAX_HUE = 0xffff
MAX_BRIGHTNESS = 254
MIN_BRIGHTNESS = 1

class LightBulb():
    def __init__(self, bridge, light_id, json_data):
        self.raw_data = json_data
        self.id = int(light_id)
        self.name = ""
        self.product_id = ""
        self.on = False
        self.bri = False
        self.hue = None
        self.sat = None
        self.bridge = bridge
        self._parse_data()

    def _parse_data(self):
        state = self.raw_data.get("state", {})
        self.name = self.raw_data.get("name", "")
        self.product_id = self.raw_data.get("productid", "N/A")
        if state:
            self.on = state.get("on", False)

    def print(self):
        print(f"id: {self.id} ({self.product_id})")
        print("on:", self.on)
        print(json.dumps(self.raw_data, indent=4))
        print("*" * 20)

    def set_state(self, state: bool):
        self.on = state

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

    def update(self, transition_time):
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


class Bridge():
    def __init__(self, ip, key):
        self.ip = ip
        self.key = key
        self.lights = []
        self._populate_lights()

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

    def _populate_lights(self):
        for key, val in self.get_req("lights").items():
            self.lights.append(LightBulb(self, key, val))


def gen_args():
    parser = ArgumentParser("Hue Tools")
    parser.add_argument("id",
                        help="lightbulb id",
                        nargs="?",
                        default=-1,
                        type=int)
    parser.add_argument("--state",
                        type=int,
                        default=None)
    parser.add_argument("--hue",
                        type=int,
                        default=None)
    parser.add_argument("--saturation",
                        "-s",
                        type=int,
                        dest="sat",
                        default=None)
    parser.add_argument("--brightness",
                        "-b",
                        type=int,
                        dest="bri",
                        default=None)
    parser.add_argument("--transition-time",
                        "-t",
                        default=None,
                        type=int,
                        dest="delay",
                        help="transition time in seconds")
    parser.add_argument("--list",
                        action="store_true",
                        dest="list_lights")
    return parser.parse_args()


def main():
    args = gen_args()
    key = ConfigurationManager().get("hue_api_key")
    hue_ip = ConfigurationManager().get("hue_ip")
    bridge = Bridge(hue_ip, key)
    for bulb in bridge.lights:
        if bulb.id == args.id:
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
            if need_update:
                bulb.update(args.delay)
        if args.list_lights:
            bulb.print()


if __name__ == "__main__":
    main()
