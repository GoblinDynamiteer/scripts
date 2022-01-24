from typing import Optional
from dataclasses import dataclass


@dataclass
class EpisodeData:
    name: Optional[str] = None
    year: Optional[int] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    title: Optional[str] = None
