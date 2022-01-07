from typing import FrozenSet
from enum import Enum, auto


class Type(Enum):
    Movie = auto()
    Episode = auto()
    Show = auto()


class Language(Enum):
    English = auto()
    Swedish = auto()


MOVIE_LETTERS: FrozenSet = frozenset({'#', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
                                      'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'VW', 'X', 'Y', 'Z'})
MOVIE_EXTRAS: FrozenSet = frozenset({"REPACK",
                                     "LiMiTED",
                                     "EXTENDED",
                                     "UNRATED",
                                     "SWEDiSH",
                                     "REMASTERED",
                                     "FESTiVAL",
                                     "DOCU",
                                     "RERiP",
                                     "iNTERNAL",
                                     "FiNNISH",
                                     "DANiSH",
                                     "DC.REMASTERED",
                                     "PROPER",
                                     "JPN",
                                     "HYBRiD",
                                     "UNCUT"})
