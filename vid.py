#!/usr/bin/env python3.8

""" Movie/Video Tools """

from pathlib import Path
from argparse import ArgumentParser

from run import command_exists, local_command_get_output


class MissingExternalApplication(Exception):
    pass


class VideoFileMetadata():
    def __init__(self, file_path):
        self.title = ""
        self.res = 0
        self.path = file_path
        self._extract_metadata()

    def _extract_metadata(self):
        if self.path.suffix.lower().endswith("mp4"):
            self._extract_metadata_mp4()

    def _extract_metadata_mp4(self):
        if not command_exists("mediainfo"):
            raise MissingExternalApplication(
                "mediainfo is not available for parsing MP4")
        mediainfo_ret = local_command_get_output(
            f"mediainfo {self.path.resolve()}")
        if not mediainfo_ret:
            return
        for line in mediainfo_ret.split("\n"):
            if not ":" in line:
                continue
            if "Movie name" in line:
                try:
                    self.title = line.split(":")[1].strip()
                    print(f"extracted name/title: {self.title}")
                except Exception as error:
                    print(error)
            if "Height" in line:
                try:
                    self.res = int(line.split(
                        ":")[1].strip().replace(" pixels", ""))
                    print(f"extracted height/res: {self.res}")
                except Exception as error:
                    print(error)


def main():
    parser = ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()
    VideoFileMetadata(Path(args.file))


if __name__ == "__main__":
    main()
