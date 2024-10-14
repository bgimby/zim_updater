# zim_updater

A CLI tool for updating zims via kiwix.org.

This tool allows checking for updated versions of zims from kiwix.org,
downloading new zims, and removing old versions of zims. It assumes you have
your zim files in a directory using the same naming conventions that are used
on https://library.kiwix.org.

## Installation

Download `zim_updater.py`, install the pre-requisites, and run the script with
```
python zim_updater.py
```

## CLI reference

### CLI Help

```
Usage: cli [OPTIONS] COMMAND [ARGS]...

  CLI tool for updating zims via kiwix.org

  This tool allows checking for updated versions of zims from kiwix.org,
  downloading new zims, and removing old versions of zims.

Options:
  --help  Show this message and exit.

Commands:
  clean   Delete old duplicate zims in a directory
  update  Download torrentfiles for zims in path with newer versions available
```

## Cleaning up old versions of zims

Reads through the given directory for any zim files, and removes old zims that
have the same name as newer ones.

### Usage

```
Usage: cli clean [OPTIONS]
```

### CLI Help

```
Usage: cli clean [OPTIONS]

  Delete old duplicate zims in a directory

  Reads through the given directory for any zim files, and removes any that
  have the same name, but different dates.

  This assumes zims end with `_YYYY-MM.zim`, which is the standard for the
  kiwix library.

Options:
  -y, --assume-yes  Assume yes to all questions
  --path TEXT       Path containing zim files to clean
  --help            Show this message and exit.
```


# Update zims

Reads through the given directory for any zim files, downloads the current
library list from kiwix.org, and checks for any new zims that match
those in the directory. If there are any, it downloads torrentfiles for
them to the provided path.

### Usage

```
Usage: cli update [OPTIONS]
```

### CLI Help

```
Usage: cli update [OPTIONS]

  Download torrentfiles for zims in path with newer versions available

  Reads through the given directory for any zim files, downloads the current
  library list from kiwix.org, and checks for any new zims that match those
  in the directory. If there are any, it downloads torrentfiles for them to
  the provided path.

  This assumes zims end with `_YYYY-MM.zim`, which is the standard for the
  kiwix library.

Options:
  -y, --assume-yes     Assume yes to all questions
  --zim-path TEXT      Path containing zim files to update  [default: .]
  --torrent-path TEXT  Path to download new torrentfiles to  [default: ./torrent]
  --help               Show this message and exit.
```

