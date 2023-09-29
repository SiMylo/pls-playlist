"""Keep track of information we need about individual tracks."""

from mutagen.mp3 import MP3
import os.path


class TrackLib:
    def __init__(self):
        self.instances = {}

    def get_info(self, filename):
        if filename not in self.instances:
            self.instances[filename] = {
                "title": os.path.basename(filename),
                "length": MP3(filename).info.length,
            }

        return self.instances[filename]
