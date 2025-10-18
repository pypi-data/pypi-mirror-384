from typing import Optional
from abc import ABC, abstractmethod
from coverdl.providers.source import Source
from coverdl.cover import ExtCover

class Provider(ABC):
    BASE_URL: Optional[str] = None
    SOURCE: Source
    API_KEY: Optional[str] = None
    SECRET_KEY: Optional[str] = None

    @abstractmethod
    def get_covers(self, artist: str, album: str) -> list[ExtCover]:
        pass
