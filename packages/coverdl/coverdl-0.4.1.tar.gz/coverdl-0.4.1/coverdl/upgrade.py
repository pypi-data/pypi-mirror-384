from coverdl.console import Console
from coverdl.options import Options
from coverdl.providers import Provider
from coverdl.cache import Cache
from coverdl.cover import Cover, ExtCover
from coverdl.utils import get_cover, IMAGE_EXTENSIONS
from coverdl.metadata import get_metadata_from_path
from coverdl.exceptions import MetadataNotFound, MissingMetadata, TriesExceeded, ProviderRequestFailed
from requests.exceptions import Timeout
from mutagen import MutagenError
import click
import os


class UpgradeService:
    def __init__(self, path_locations: list[str], options: Options, providers: list[Provider]) -> None:
        self.console = Console(options.silence_warnings)
        self.cache = Cache(options.cache)
        self.path_locations = path_locations
        self.options = options
        self.providers = providers
        self.current_path = None

    def upgrade(self):
        for path in self.path_locations:
            self.current_path = path
            self._upgrade_cover_art(path)

        self.cache.save()

    def _get_results_from_providers(self, artist: str, album: str) -> list[ExtCover]:
        results: list[ExtCover] = []

        for provider in self.providers:
            try:
                results = results + provider.get_covers(artist, album)
            except ProviderRequestFailed as e:
                self.console.warn(f"Failed to fetch cover art data from provider: {e.args[0].value}. Got error: {e.args[1]}")

        return results

    def _meets_hamming_distance(self, cover: Cover, candidate: ExtCover) -> bool | None:
        if candidate.ext not in IMAGE_EXTENSIONS:
            self.console.warn(f"Image {candidate.ext} not allowed as valid image format.")
            return

        hamming_distance = None
        try:
            hamming_distance = cover.compare(candidate)
        except Timeout:
            self.console.error(f"Timed out while downloading cover art for {click.style(self.current_path, bold=True)}.")
            return

        if not hamming_distance:
            self.console.warn(f"Failed to calculate hamming distance for candidate {candidate.cover_url}. Skipping.")
            return

        similarity_check = hamming_distance == 0 if self.options.strict else hamming_distance <= self.options.max_hamming_distance

        if not similarity_check:
            self.console.warn(f"Cover candidate ({candidate.cover_url}) for {click.style(self.current_path, bold=True)} " \
                        f"does not meet similarity requirements (hamming distance = {hamming_distance}, needs <= {self.options.max_hamming_distance}). Skipping.")
            
        return similarity_check

    def _find_best_candidate(self, cover: Cover, results: list[ExtCover]) -> ExtCover | None:
        cover_size = cover.size / 1000000

        for cover_candidate in results:
            candidate_buffer_size = cover_candidate.get_buffer_size() / 1000000

            if candidate_buffer_size > self.options.max_upgrade_size:
                self.console.warn(f"Cover candidate ({cover_candidate.cover_url}) for {click.style(self.current_path, bold=True)} " \
                    f"exceeds max_upgrade_size ({round(candidate_buffer_size)}M / {self.options.max_upgrade_size}M). Skipping.")
                continue

            if candidate_buffer_size <= cover_size:
                self.console.warn(f"Cover candidate ({cover_candidate.cover_url}) for {click.style(self.current_path, bold=True)} " \
                    f"is less than or equivalent in size ({candidate_buffer_size}M / {cover_size}M). Skipping.")
                continue

            if self._meets_hamming_distance(cover, cover_candidate):
                return cover_candidate

    def _delete_or_backup(self, cover: Cover):
        if self.options.delete_old_covers:
            cover.delete()
            self.console.echo(f"Deleted {cover.path}")
        else:
            old_cover = cover.path
            cover.backup()
            self.console.echo(f"Renamed {old_cover} to {cover.path}")

    def _upgrade_cover_art(self, path: str):
        cover = get_cover(path)

        if self.cache.has(os.path.abspath(path)):
            self.console.warn(f"{click.style(path, bold=True)} exists in cache. It'll be skipped.")
            return

        if not cover:
            self.console.warn(f"{click.style(path, bold=True)} does not have cover. Skipping.")
            return

        cover_size = cover.size / 1000000

        if cover_size > self.options.max_size:
            self.console.warn(f"{click.style(cover, bold=True)} exceeds --max-size ({round(cover_size, 2)}M / {self.options.max_size}M). Skipping.")
            return

        try:
            self.console.echo(f"Fetching metadata from {click.style(path, bold=True)}")
            metadata = get_metadata_from_path(path)
        except (MutagenError, TriesExceeded, MissingMetadata, MetadataNotFound):
            self.console.error(f"Failed to fetch metadata from {path}")
            self.cache.add(os.path.abspath(path))
            return

        results: list[ExtCover] = self._get_results_from_providers(metadata.artist, metadata.album)

        if len(results) == 0:
            self.console.error(f"No suitable upgradable cover art could be found for {click.style(path, bold=True)} (all providers returned no results)")
            self.cache.add(os.path.abspath(path))
            return
        
        candidate: ExtCover | None = None

        if self.options.replace_non_square and cover.shape[0] != cover.shape[1]:
            self.console.echo(f"{cover.path} is non-square. Replacing...")
            candidate = results[0]
        else:
            candidate: ExtCover | None = self._find_best_candidate(cover, results)

        if not candidate:
            self.console.error(f"No suitable cover art could be found for {click.style(path, bold=True)} (exhausted all candidates)")
            self.cache.add(os.path.abspath(path))
            return
        
        self._delete_or_backup(cover)

        target = os.path.join(path, self.options.cover_name + candidate.ext)
        candidate.download(target)

        click.echo(f"{click.style('Successfully', fg='green')} saved new cover art: {target}")
        self.cache.add(os.path.abspath(path))
