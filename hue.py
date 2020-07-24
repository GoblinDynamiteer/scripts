#!/usr/bin/env python3.8

""" Philips Hue Tools """


import http.client
import json

from argparse import ArgumentParser

from config import ConfigurationManager


class LightBulb():
    def __init__(self, bridge, light_id, json_data):
        self.raw_data = json_data
        self.id = int(light_id)
        self.name = ""
        self.on = False
        self.bridge = bridge
        self._parse_data()
        self.print()

    def _parse_data(self):
        state = self.raw_data.get("state", {})
        self.name = self.raw_data.get("name", "")
        if state:
            self.on = state.get("on", False)

    def print(self):
        print(f"id: {self.id}")
        print("on:", self.on)
        print("*" * 100)

    def set_state(self, state: bool):
        body = {"on": state}
        print(f"setting \"{self.name}\" {state}")
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
    parser.add_argument("id", help="lightbulb id", type=int)
    parser.add_argument("--state", type=int, default=0)
    return parser.parse_args()


def main():
    key = ConfigurationManager().get("hue_api_key")
    hue_ip = ConfigurationManager().get("hue_ip")
    bridge = Bridge(hue_ip, key)
    args = gen_args()
    for bulb in bridge.lights:
        if bulb.id == args.id:
            bulb.set_state(bool(args.state))


if __name__ == "__main__":
    main()
