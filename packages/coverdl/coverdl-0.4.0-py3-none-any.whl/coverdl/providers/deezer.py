import requests
from coverdl.providers.base import Provider
from coverdl.cover import ExtCover
from coverdl.providers.source import Source
from coverdl.exceptions import ProviderRequestFailed
from coverdl.utils import get_extension_from_url

class DeezerProvider(Provider):
    BASE_URL = "https://api.deezer.com"
    SOURCE = Source.DEEZER

    def get_covers(self, artist, album) -> list[ExtCover]:
        results = []
        params={
            "q": f"artist:\"{artist}\" album:\"{album}\""
        }
        r = requests.get(self.BASE_URL + "/search/album", params=params, timeout=10)

        if r.ok:
            data = r.json()

            for item in data["data"]:
                results.append(
                    ExtCover(
                        artist=item["artist"]["name"],
                        title=item["title"],
                        source=self.SOURCE,
                        cover_url=item["cover_xl"],
                        ext=get_extension_from_url(item["cover_xl"])
                    )
                )
        else:
            raise ProviderRequestFailed(self.SOURCE, r.text)
        
        return results
