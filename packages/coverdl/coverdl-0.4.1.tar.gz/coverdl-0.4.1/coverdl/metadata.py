from dataclasses import dataclass
import os
import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from coverdl.exceptions import MetadataNotFound, MissingMetadata, TriesExceeded

SUPPORTED_SONG_EXTENSIONS = [".mp3", ".flac", ".m4a"]

@dataclass
class Metadata:
    album: str
    artist: str

METADATA_MAPPING = {
    MP3: {
        "album": "TALB",
        "artist": "TPE1"
    },
    FLAC: {
        "album": "album",
        "artist": "artist"
    },
    MP4: {
        "album": "©alb",
        "artist": "©ART"
    }
}

def get_metadata_from_file(path: str):
    metadata: dict[str, str] = {}
    file = mutagen.File(path)

    for filetype, mapping in METADATA_MAPPING.items():
        if isinstance(file, filetype):
            for item, val in mapping.items():
                metadata[item] = dict(file)[val][0] if val in file else None

    if not metadata["album"] or not metadata["artist"]:
        raise MissingMetadata()

    return Metadata(**metadata)

def get_metadata_from_directory(path: str):
    tries = 0
    for root, _, files in os.walk(path):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext.lower() in SUPPORTED_SONG_EXTENSIONS:
                try:
                    metadata = get_metadata_from_file(os.path.join(root, file))
                    return metadata
                except (mutagen.MutagenError, MissingMetadata):
                    pass

                tries += 1

                if tries > 3:
                    raise TriesExceeded()
    raise MetadataNotFound()

def get_metadata_from_path(path: str):
    if os.path.isdir(path):
        return get_metadata_from_directory(path)
    else:
        return get_metadata_from_file(path)
