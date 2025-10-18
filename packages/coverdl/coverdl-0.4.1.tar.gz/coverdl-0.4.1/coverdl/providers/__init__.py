from .base import Provider
from .deezer import DeezerProvider
from .itunes import ITunesProvider
from .apple_music import AppleMusicProvider
from .discogs import DiscogsProvider

providers: list[Provider] = [
    AppleMusicProvider(),
    DeezerProvider(),
    DiscogsProvider(),
    ITunesProvider()
]
