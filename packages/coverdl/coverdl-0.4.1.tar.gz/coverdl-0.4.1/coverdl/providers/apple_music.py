from coverdl.providers.base import Provider
from coverdl.providers.itunes import ITunesProvider
from coverdl.providers.source import Source
from coverdl.utils import get_extension_from_url
from coverdl.cover import ExtCover
import requests

class AppleMusicProvider(Provider):
    SOURCE = Source.APPLE_MUSIC

    def __init__(self):
        super().__init__()
        self.itunes_provider = ITunesProvider()

    def _transform_url(self, itunes_url):
        # Convert the iTunes url into a higher-quality Apple Music equivalent
        cover_url = itunes_url.replace("is1-ssl", "a1")
        cover_url = cover_url.replace("/image/", "/us/")
        cover_url = cover_url.replace("/thumb/", "/r1000/063/")

        cover_url = '/'.join(cover_url.split('/')[:-1])

        return cover_url
    
    def _test_url(self, url):
        r = requests.head(url, timeout=10)

        return r.ok

    def get_covers(self, artist, album) -> list[ExtCover]:
        results = []
        covers = self.itunes_provider.get_covers(artist, album)

        for cover in covers:
            cover.cover_url = self._transform_url(cover.cover_url)
            cover.ext = get_extension_from_url(cover.cover_url)
            cover.source = self.SOURCE
            if self._test_url(cover.cover_url):
                results.append(cover)

        return results
