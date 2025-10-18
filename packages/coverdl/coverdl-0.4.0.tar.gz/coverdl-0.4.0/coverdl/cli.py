import os
import sys
import click
from coverdl import __version__
from coverdl.providers import providers
from coverdl.providers.source import Source
from coverdl.upgrade import UpgradeService
from coverdl.download import DownloadService
from coverdl.utils import (
    get_album_paths,
    error
)
from coverdl.options import Options

@click.command(context_settings={'show_default': True})
@click.option('-p', '--provider',
              type=Source, multiple=True, default=[Source.APPLE_MUSIC, Source.DEEZER],
              help='The provider to download cover art from. Multiple providers can be specified by passing this option more than once (by order of preference).')
@click.option('--cover-name',
              default='cover',
              help='The filename for the cover art image.')
@click.option('--cache',
              help='Specify a cache file to prevent repeat upgrades')
@click.option('-t', '--tag',
              multiple=True,
              help='A tag is an attribute unique to your release. e.g: remastered, expanded. Multiple tags can be specified.')
@click.option('-r', '--recursive',
              is_flag=True,
              help='Enables recursive download. This will traverse the path you give it and download cover art for albums that don\'t have them.')
@click.option('-u', '--upgrade',
              is_flag=True,
              help='Upgrades existing cover art to better quality equivalents.')
@click.option('--max-size',
              type=float, default=10,
              help='Already existing cover art that exceeds the max size will not be considered for upgrade (unit must be in MBs).')
@click.option('--max-upgrade-size',
              type=float, default=15,
              help='Upgrade candidates exceeding this size will not be considered (unit must be in MBs).')
@click.option('--strict',
              help='Enables strict mode (for upgrades). Ensures that only near-perfect comparisons will be upgraded.')
@click.option('--replace-non-square',
              is_flag=True,
              help='Replace non-square cover art. Must be used alongside --upgrade')
@click.option('--max-hamming-distance',
            type=int, default=8,
            help='Specifies the maximum hamming distance used for upgrades. Setting this to 0 is the equivalent of using --strict')
@click.option('--silence-warnings',
              is_flag=True)
@click.option('--delete-old-covers',
              is_flag=True)
@click.argument('path', type=click.Path(exists=True), nargs=-1)
@click.version_option(__version__)
def coverdl(path: str,
            provider: list[Source],
            cover_name: str,
            cache: str,
            recursive: bool,
            upgrade: bool,
            tag: list[str],
            max_size: float,
            max_upgrade_size: float,
            strict: bool,
            replace_non_square: bool,
            max_hamming_distance: int,
            silence_warnings: bool,
            delete_old_covers: bool):
    options = Options(
        path=path,
        providers=provider,
        cover_name=cover_name,
        cache=cache,
        tags=tag,
        recursive=recursive,
        upgrade=upgrade,
        max_size=max_size,
        max_upgrade_size=max_upgrade_size,
        strict=strict,
        replace_non_square=replace_non_square,
        max_hamming_distance=max_hamming_distance,
        silence_warnings=silence_warnings,
        delete_old_covers=delete_old_covers
    )
    
    # Get and sort the providers based on user preference
    selected_providers = list(filter(lambda p: p.SOURCE in provider, providers))
    selected_providers.sort(key=lambda p: options.providers.index(p.SOURCE))

    if options.recursive and options.tags:
        error("--recursive and --tag cannot be used together.")
        return

    path_locations: list[str] = []
    if not sys.stdin.isatty():
        stdin_text = click.get_text_stream('stdin')
        path_locations = list(stdin_text.read().rstrip().split('\n'))
    else:
        if options.recursive and len(options.path) != 1:
            error("Please specify (one) path for recursive search.")
            return
        path_locations = get_album_paths(options.path[0], must_have_cover=options.upgrade) if options.recursive else list(options.path)

    if options.upgrade:
        upgrade_service = UpgradeService(path_locations, options, selected_providers)
        upgrade_service.upgrade()
    else:
        download_service = DownloadService(path_locations, options, selected_providers)
        download_service.download()
