#!/usr/bin/env python3.6

'''HP Scanner helper on linux'''

import argparse
import os
import sys
import printing
import run

HOME = os.path.expanduser("~")
DEFAULT_SAVE_PATH = os.path.join(HOME, "temp")
PRINT = printing.PrintClass(os.path.basename(__file__))

# hp-scan --size = a4 - -resolution = 300 - -mode = color - -file = /home/johan/Temp/nathalie-anstallningsavtal-chopchop-sida2.png - -compression = raw

if __name__ == "__main__":
    if not os.path.exists(DEFAULT_SAVE_PATH):
        os.makedirs(DEFAULT_SAVE_PATH)
        PRINT.info(f"creating temp directory: {DEFAULT_SAVE_PATH}")
    try:
        assert os.path.exists(DEFAULT_SAVE_PATH)
    except AssertionError:
        PRINT.error(
            f"temporary directory {DEFAULT_SAVE_PATH} doesn't exist and could not be created!")
        sys.exit(1)
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--size", help="scan format size",
                        type=str, default="a4")
    PARSER.add_argument("--resolution", help="scan dpi", type=int, default=300)
    PARSER.add_argument("--mode", help="color/gray", type=str, default="color")
    PARSER.add_argument("--dest", help="destination directory (full path)",
                        type=str, default=DEFAULT_SAVE_PATH)
    PARSER.add_argument("--file", help="file name",
                        type=str, default="scan.png")
    ARGS = PARSER.parse_args()

    FILE_OUTPUT = os.path.join(ARGS.dest, ARGS.file)
    COMMAND = f"hp-scan --size {ARGS.size} --resolution {ARGS.resolution} --mode {ARGS.mode} --file {FILE_OUTPUT}"
    run.local_command(COMMAND)
