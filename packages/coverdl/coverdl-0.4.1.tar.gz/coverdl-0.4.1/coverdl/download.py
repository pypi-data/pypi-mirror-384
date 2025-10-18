import os
import click
from requests import HTTPError, Timeout
from mutagen import MutagenError
from coverdl.console import Console
from coverdl.cover import ExtCover
from coverdl.exceptions import MetadataNotFound, ProviderRequestFailed, TriesExceeded
from coverdl.metadata import get_metadata_from_path
from coverdl.options import Options
from coverdl.providers.base import Provider
from coverdl.utils import IMAGE_EXTENSIONS, has_cover


class DownloadService:
    def __init__(self, path_locations: list[str], options: Options, providers: list[Provider]) -> None:
        self.console = Console(options.silence_warnings)
        self.path_locations = path_locations
        self.options = options
        self.providers = providers

        self.completed = 0
        self.failed = 0

    def download(self):
        for path in self.path_locations:
            self._download_cover_art(path)

        self.console.echo()
        self.console.echo(f"{click.style('Completed:', bold=True)} {self.completed}, {click.style('Failed:', bold=True)} {self.failed}")

    def _get_results_from_providers(self, artist: str, album: str) -> list[ExtCover]:
        results: list[ExtCover] = []

        for provider in self.providers:
            try:
                results = results + provider.get_covers(artist, album)

                if len(results) != 0:
                    # There is no need to fetch from the next provider if we already have results.
                    break
            except ProviderRequestFailed as e:
                self.console.warn(f"Failed to fetch cover art data from provider: {e.args[0].value}. Got error: {e.args[1]}")

        return results

    def _download_cover_art(self, path: str):
        self.console.echo(f"Fetching metadata from {path}")

        try:
            metadata = get_metadata_from_path(path)
        except (TriesExceeded, MetadataNotFound):
            self.console.error(f"Failed to fetch sufficient metadata from album: {click.style(path, bold=True)}")
            self.failed += 1
            return
        except MutagenError:
            self.console.error(f"Failed to read file: {click.style(path, bold=True)}, possibly invalid or corrupt")
            self.failed += 1
            return
        
        if has_cover(path):
            self.console.warn(f"{click.style(path, bold=True)} already has a cover. Skipping.")
            return
        
        if not metadata:
            self.console.error(f"Could not fetch metadata from path: {click.style(path, bold=True)}")
            self.failed += 1
            return
        
        results = self._get_results_from_providers(metadata.artist, metadata.album)

        if len(results) == 0:
            self.console.error(f"No suitable cover art could be found for {click.style(path, bold=True)}")
            self.failed += 1
            return
        
        cover: ExtCover | None = None

        for result in results:
            if result.ext not in IMAGE_EXTENSIONS:
                self.console.warn(f"Cover image format not allowed {result.ext}. Skipping.")
                continue
            cover = result

        if not cover:
            self.console.error(f"Failed to find suitable cover art for {click.style(path, bold=True)}.")
            self.failed += 1
            return
        
        try:
            dir_path = path if os.path.isdir(path) else os.path.dirname(path)
            cover.download(os.path.join(dir_path, self.options.cover_name + cover.ext))
            click.echo(f"{click.style('Successfully', fg='green')} downloaded cover art for {click.style(path, bold=True)}")
            self.completed += 1
        except HTTPError as e:
            self.console.error(f"Failed to download cover art for {click.style(path, bold=True)}, got error: {e.response.status_code}")
        except Timeout:
            self.console.error(f"Timed out while downloading cover art for {click.style(path, bold=True)}")

