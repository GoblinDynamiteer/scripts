from typing import Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from media.base import MediaItem, Type, Language
from media.util import MediaPaths
from media.regex import parse_season_and_episode


@dataclass
class EpisodeData:
    name: Optional[str] = None  # Name of file
    show_title: Optional[str] = None
    year: Optional[int] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    title: Optional[str] = None


class Episode(MediaItem):
    def __init__(self, episode_file_path: Path):
        MediaItem.__init__(self, episode_file_path)
        self._tv_dir = MediaPaths().tv_dir()
        self._data: EpisodeData = EpisodeData(name=self.name)
        self._parse()

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def data(self) -> EpisodeData:
        return self._data

    @property
    def type(self) -> Type:
        return Type.Episode

    @property
    def season_num(self) -> Optional[int]:
        return self._data.season_number

    @property
    def episode_num(self) -> Optional[int]:
        return self._data.episode_number

    @property
    def show_path(self) -> Path:
        return self.path.parents[1]

    def has_external_subtitle(self, language: Language) -> bool:
        raise NotImplementedError()

    def is_compressed(self) -> bool:
        raise NotImplementedError()

    def get_correct_location(self) -> Path:
        raise NotImplementedError()

    def is_valid(self) -> bool:
        if self._data.episode_number is None:
            return False
        if self._data.season_number is None:
            return False
        return True

    def _parse(self) -> None:
        s, e = parse_season_and_episode(self.name)
        self._data.episode_number = e
        self._data.season_number = s
        self._data.show_title = self.show_path.name

    def __repr__(self):
        _dict = asdict(self._data)
        _dict["valid"] = self.is_valid()
        return str(_dict)


def main():
    from argparse import Namespace, ArgumentParser

    def get_args() -> Namespace:
        parser = ArgumentParser()
        parser.add_argument("--filter", default=None, type=str)
        parser.add_argument("--limit", default=None, type=int)
        return parser.parse_args()

    args = get_args()
    count = 0

    for episode in MediaPaths().episode_files():
        if args.filter is not None:
            if args.filter not in str(episode):
                continue
        count += 1
        _show = Episode(episode)
        print(_show)
        if args.limit == count:
            break


if __name__ == "__main__":
    main()
