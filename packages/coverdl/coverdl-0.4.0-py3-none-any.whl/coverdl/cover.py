from PIL import Image
from coverdl.providers.source import Source
import imagehash
import requests
import os
import io

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.0; BLN-L22) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Mobile Safari/537.36"
}

class ExtCover:
    """
    Represents an external cover art.
    """
    artist: str
    title: str
    source: Source
    cover_url: str
    ext: str
    confidence: float = 1

    def __init__(self, artist: str, title: str, source: Source,
                 cover_url: str, ext: str, confidence: float = 1) -> None:
        self.artist = artist
        self.title = title
        self.source = source
        self.cover_url = cover_url
        self.ext = ext
        self.confidence = confidence
        self._buffer = None

    def get_buffer(self) -> io.BytesIO | None:
        """
        Fetches the cover art as a buffer and caches it
        """
        if self._buffer:
            return self._buffer

        r = requests.get(self.cover_url, headers=DEFAULT_HEADERS, timeout=60)

        if r.ok:
            self._buffer = io.BytesIO(r.content)
            return self._buffer
        
    def get_buffer_size(self):
        buffer = self.get_buffer()

        if buffer:
            return buffer.getbuffer().nbytes

    def download(self, path: str):
        """
        Download the cover art
        """
        buffer = self.get_buffer()

        if buffer:
            with open(path, 'wb') as f:
                f.write(buffer.getbuffer())

class Cover:
    """
    Represents a cover art file
    """
    path: str

    def __init__(self, path: str):
        self.path = path
        self.img = Image.open(self.path)

    @property
    def size(self):
        return os.path.getsize(self.path)

    @property
    def shape(self):
        return self.img.size

    def compare(self, ext_cover: ExtCover):
        """
        Compare similarity between an external cover art
        """
        hash_0 = imagehash.average_hash(self.img)
        buffer = ext_cover.get_buffer()

        if buffer:
            hash_1 = imagehash.average_hash(Image.open(buffer))

            return hash_0 - hash_1
    
    def delete(self):
        """
        Delete the current cover art file
        """
        os.remove(self.path)

    def backup(self):
        """
        Renames the current cover art to a .bk file
        """
        i = 0
        new_name = self.path + '.bk'
        while os.path.exists(new_name):
            i += 1
            name, ext = os.path.splitext(self.path)
            new_name = name + str(i) + ext + '.bk'
        os.rename(self.path, new_name)
        self.path = new_name
