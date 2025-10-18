# coverdl
A command-line tool for downloading high quality album cover art.

# Installation

```
pip install coverdl
```

# Usage

Download cover art from album directory:

```
coverdl /artist/album/
```

Download cover art using track file:
```
coverdl "/artist/album/01 - Track Title.flac"
```

By default, the Apple Music and Deezer providers will be used to find cover art. You can specify a different provider like so:

```
coverdl -p itunes /artist/album
```

You can specify more than one provider by passing the `-p` option more than once:

```
coverdl -p applemusic -p itunes /artist/album
```

The order in which the providers are specified matters, as they will be used for priority ranking.

Click [here](https://github.com/viown/coverdl/blob/main/coverdl/providers/source.py#L3) for a list of providers.

## Upgrading

coverdl will not download cover art for albums that already have them. Instead, you can upgrade them to a better quality version.

The `--upgrade` option allows you to upgrade your existing cover art to a better quality version (if found) by comparing the similarity of both images. This allows you to safely upgrade your existing cover art while being sure that a different version won't be downloaded by mistake:

```
coverdl --upgrade /artist/album/
```

Your old cover art will not be deleted, it will be renamed: e.g `cover.jpg` to `cover.jpg.bk`
To tell coverdl to delete it, pass the `--delete-old-covers` option.

Use the `--max-size` option (in MBs) to prevent coverdl from replacing cover art that exceed a certain size.

Use `--max-upgrade-size` (in MBs) to prevent downloading cover art that exceed a certain size.

Use the `--strict` flag to ensure only perfect comparisons will be upgraded. For example, if your cover art has an explicit advisory label in the cover art while the upgrade candidate doesn't, `--strict` will block the upgrade.

### Replace non-square cover art

Alongside the `--upgrade` option, `--replace-non-square` will replace the cover art for all albums which do not have a perfectly square (1:1) aspect ratio. Replacing non-square cover art will not take into account the similarity of both images.

## Advanced

### Piping

coverdl supports passing multiple paths to it via the pipe operator. This can be useful for advanced use cases, for example:

If your library structure follows `ARTIST/ALBUM`, you could download or upgrade cover art for albums only added within the last day:

```
find music/ -mindepth 2 -maxdepth 2 -mtime -1 -type d | coverdl
```
Which can be useful as a cron job to speed up performance without using `-r`.

## Downloading for an entire music library

If you have a large music library and you wish to download or upgrade cover art for all albums, use the `-r/--recursive` option while passing the path to your media library:

```
coverdl -r /music
```

### When using --upgrade

Using `--upgrade` alongside `-r/--recursive` can be slow, and each run of the command will take the same length of time.

You can tell coverdl to skip already upgraded cover art on the next run by passing a cache file:
```
coverdl -r --upgrade /music --cache /PATH/TO/CACHE/cache.txt
```
