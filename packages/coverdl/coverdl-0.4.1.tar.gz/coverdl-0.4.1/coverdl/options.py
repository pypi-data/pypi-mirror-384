from dataclasses import dataclass
from coverdl.providers.source import Source

@dataclass
class Options:
    path: list[str]
    providers: list[Source]
    cover_name: str
    cache: str
    tags: list[str]
    recursive: bool
    upgrade: bool
    max_size: float
    max_upgrade_size: float
    strict: bool
    replace_non_square: bool
    max_hamming_distance: int
    silence_warnings: bool
    delete_old_covers: bool
