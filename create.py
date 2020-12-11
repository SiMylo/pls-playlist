#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create a ``.pls`` playlist from music filenames.

Specify a path to be recursively searched for music files.

Requires Python 3.3 and the `pathlib` module, or Python 3.4+.

According to an `unofficial PLS format specification`__, the attribute
``NumberOfEntries`` can be placed *after* all entries.  This allows to
iterate through filenames without keeping details for each entry in
memory.

__ http://forums.winamp.com/showthread.php?threadid=65772

:Copyright: 2007-2016 Jochen Kupperschmidt
:Date: 2016-03-28 (original release: 09-Feb-2007)
:License: MIT
:Website: http://homework.nwsnet.de/releases/1a02/#create-pls-playlists
"""

from argparse import ArgumentParser
import os.path
from pathlib import Path
import yaml
import re
from TrackDatabase import TrackDatabase


PATTERN = re.compile(r'.mp3$', re.I)


def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser()
    parser.add_argument('path', type=Path)
    parser.add_argument('output_file', type=Path)

    return parser.parse_args()


def find_files(path):
    """Return all matching files beneath the path."""
    for root, dirs, files in os.walk(str(path)):
        for fn in filter(PATTERN.search, files):
            filename = os.path.join(root, fn)
            yield Path(filename)

if __name__ == '__main__':
    args = parse_args()
    database = TrackDatabase(str(args.path))
    # paths = find_files(args.path)
    # Playlist(paths).write_file(args.output_file,relpath=args.path)
