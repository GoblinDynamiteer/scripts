from typing import Optional
from dataclasses import dataclass


@dataclass
class ShowData:
    name: Optional[str] = None  # Name of directory
    year: Optional[int] = None
    title: Optional[str] = None
