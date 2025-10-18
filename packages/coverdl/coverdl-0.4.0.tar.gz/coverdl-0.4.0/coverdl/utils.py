import os
import mimetypes
import click
from coverdl.metadata import SUPPORTED_SONG_EXTENSIONS
from coverdl.cover import Cover
from difflib import SequenceMatcher

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]

def error(message):
    click.echo(f"{click.style('Error:', fg='red')} {message}")

def warn(message, silence=False):
    if silence:
        return
    click.echo(f"{click.style('Warn:', fg='yellow')} {message}")

def compare(title1: str, title2: str) -> float:
    return SequenceMatcher(None, title1.lower().strip(), title2.lower().strip()).ratio()

def get_album_paths(path, must_have_cover=True) -> list[str]:
    paths = []
    for root, dirs, _ in os.walk(path):
        for current_dir in dirs:
            full_dir = os.path.join(root, current_dir)
            if is_album_dir(full_dir) or (has_song(full_dir) and not must_have_cover):
                paths.append(full_dir)
    return paths

def get_base_path(path):
    if os.path.isfile(path):
        return os.path.dirname(path)
    return os.path.normpath(path)

def get_extension_from_url(url):
    guessed_type = mimetypes.guess_type(url)

    if guessed_type and len(guessed_type) > 0 and guessed_type[0]:
        return mimetypes.guess_extension(guessed_type[0])

def get_cover(path) -> Cover | None:
    if os.path.isfile(path):
        path = os.path.dirname(os.path.abspath(path))

    files = os.listdir(path)

    for file in files:
        name, ext = os.path.splitext(file)
        if ext in IMAGE_EXTENSIONS and name in ["folder", "poster", "cover", "default"]:
            return Cover(path=os.path.join(path, file))

def has_song(dir_path: str):
    for f in os.listdir(dir_path):
        _, ext = os.path.splitext(f)
        if ext in SUPPORTED_SONG_EXTENSIONS:
            return True
    return False

def has_cover(path) -> bool:
    return bool(get_cover(path))

def is_album_dir(dir_path: str):
    return has_cover(dir) and has_song(dir_path)
