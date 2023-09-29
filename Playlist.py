"""Writes a PSL-formatted playlist from the given filelist, in order.

Specify a path to be recursively searched for music files.

Requires Python 3.3 and the `pathlib` module, or Python 3.4+.

According to an `unofficial PLS format specification`__, the attribute
``NumberOfEntries`` can be placed *after* all entries.  This allows to
iterate through filenames without keeping details for each entry in
memory.

__ http://forums.winamp.com/showthread.php?threadid=65772

Based on Jochen Kupperschmidt's work

:Copyright: 2007-2016 Jochen Kupperschmidt
:Date: 2016-03-28 (original release: 09-Feb-2007)
:License: MIT
:Website: http://homework.nwsnet.de/releases/1a02/#create-pls-playlists
"""

import os
from itertools import count
from TrackLib import TrackLib


class Playlist:
    tracks = TrackLib()

    def __init__(self, files=[]):
        self.filelist = files

    @staticmethod
    def create_track_entry(number, path, *, relpath=None):
        """Create a track entry."""
        track = Playlist.tracks.get_info(path)
        if relpath:
            path = os.path.relpath(path, relpath)

        return {
            "number": number,
            "file": path,
            "title": track["title"],
            "length": track["length"],
        }

    def write_file(self, filename, *, relpath=None):
        with open(filename, "w+") as outfile:
            for content in self.generate_contents(relpath):
                try:
                    outfile.write(content)
                except UnicodeEncodeError:
                    print(f"Filename: {filename}\nContents: {content}")
                    raise

    def generate_contents(self, relpath=None):
        """Generate a PLS playlist from file list."""
        yield "[playlist]\n\n"

        total = 0

        entry_template = (
            "File{number:d}={file}\n"
            "Title{number:d}={title}\n"
            "Length{number:d}={length}\n\n"
        )

        for track_entry in self.get_track_entries(relpath):
            total += 1
            yield entry_template.format(**track_entry)

        yield ("NumberOfEntries={:d}\n" "Version=2\n").format(total)

    def get_track_entries(self, relpath=None):
        """Generate track entries."""
        numbers = count(1)
        for number, filename in zip(numbers, self.filelist):
            yield Playlist.create_track_entry(number, filename, relpath=relpath)
