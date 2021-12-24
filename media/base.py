from pathlib import Path
from abc import ABC, abstractmethod

from media.enums import Type, Language


class MediaItem(ABC):
    def __init__(self, path: Path):
        self._path = path

    @property
    def filename(self) -> str:
        return self._path.name

    def exists_on_disk(self) -> bool:
        return self._path.exists()

    def __repr__(self):
        return self.filename

    @property
    @abstractmethod
    def name(self) -> Type:
        raise NotImplementedError

    @property
    @abstractmethod
    def type(self) -> Type:
        raise NotImplementedError

    @abstractmethod
    def has_external_subtitle(self, language: Language) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_compressed(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_correct_location(self):
        raise NotImplementedError
