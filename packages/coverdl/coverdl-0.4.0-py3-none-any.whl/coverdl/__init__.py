from importlib import metadata

__title__ = metadata.metadata(__package__)['name']
__version__ = metadata.version(__package__)
__author__ = metadata.metadata(__package__)['author']
