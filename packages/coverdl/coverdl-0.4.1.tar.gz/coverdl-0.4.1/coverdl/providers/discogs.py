from coverdl import __version__
from coverdl.cover import ExtCover
from coverdl.exceptions import ProviderRequestFailed
from coverdl.providers.base import Provider
from coverdl.providers.source import Source
from coverdl.utils import get_extension_from_url, compare
import requests

class DiscogsProvider(Provider):
    BASE_URL = "https://api.discogs.com"
    SOURCE = Source.DISCOGS
    API_KEY = "yoVukqDuMTyrckrqJdfc"
    SECRET_KEY = "PRCvdLuRMVghFrNtRRvylkDZEKCiLUbI" # not secret

    def get_headers(self):
        return {
            "User-Agent": f"coverdl/{__version__}",
            "Authorization": f"Discogs key={self.API_KEY}, secret={self.SECRET_KEY}"
        }

    def get_covers(self, artist, album) -> list[ExtCover]:
        params = {
            "artist": artist,
            "release_title": album
        }
        r = requests.get(self.BASE_URL + "/database/search",
                         headers=self.get_headers(),
                         params=params,
                         timeout=10)

        if r.ok:
            results = []
            data = r.json()

            for item in data["results"]:
                similarity_ratio = compare(item["title"], f"{artist} - {album}")

                if similarity_ratio > 0.8:
                    results.append(
                        ExtCover(
                            artist=artist,
                            title=album,
                            source=self.SOURCE,
                            cover_url=item["cover_image"],
                            ext=get_extension_from_url(item["cover_image"]),
                            confidence=similarity_ratio
                        )
                    )

            return sorted(results, key=lambda c: c.confidence, reverse=True)
        raise ProviderRequestFailed(self.SOURCE, r.text)
