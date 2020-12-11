"""Gathers information about tracks and make configured playlists"""

from argparse import ArgumentParser
import os.path
from pathlib import Path
from hsaudiotag import auto
import yaml
import re
from Playlist import Playlist

class TrackDatabase():
    MUSIC_FILES = re.compile(r'.mp3$', re.I)

    def __init__(self, basepath):
        self.groupings = {}
        self.basepath = basepath
        self.parse_config('playlists.yml')
        self.gather_database()

    def parse_config(self, path):
        self.categories = {}
        self.group_config = {}
        self.playlists = {}
        if os.path.isfile(path):
            with open(path,'r') as configfile:
                raw_config = yaml.load(configfile, Loader=yaml.FullLoader)
        if 'categories' not in raw_config:
            raw_config['categories'] = {'all': ['.']}
        if 'playlists' not in raw_config:
            raw_config['playlists'] = {'name': 'shuffle', 'grouping': 'none', 'include': 'all'}
        for category in raw_config['categories']:
            for playlist in category:
                self.categories[playlist] = []
                for entry in category[playlist]:
                    new_entry = {}
                    if not isinstance(entry, dict):
                        new_entry['folder'] = entry
                    else:
                        new_entry = entry
                        if 'regex' in new_entry:
                            if not isinstance(new_entry['regex'], list):
                                new_entry['regex'] = [new_entry['regex']]
                            for regex in new_entry['regex']:
                                regex = regex.replace('\\\\','\\')
                    self.categories[playlist].append(new_entry)
        for grouping in raw_config['groupings']:
            self.group_config[grouping] = []
            for entry in raw_config['groupings'][grouping]:
                new_entry = entry
                if not isinstance(new_entry['regex'], list):
                    new_entry['regex'] = [new_entry['regex']]
                for regex in new_entry['regex']:
                    regex = regex.replace('\\\\','\\')
                self.group_config[grouping].append(new_entry)
        for playlist in raw_config['playlists']:
            self.playlists[playlist['name']] = {'grouping': playlist['grouping'], 'include': [], 'exclude': []}
            for listtype in ['include','exclude']:
                if listtype in playlist:
                    if isinstance(playlist[listtype], list):
                        self.playlists[playlist['name']][listtype] = playlist[listtype]
                    else:
                        self.playlists[playlist['name']][listtype] = [playlist[listtype]]

    def add_to_categories(self,relpath):
        categories = ['all']
        for category in self.categories:
            for entry in self.categories[category]:
                if entry['folder'] in relpath:
                    if 'regex' not in entry:                          
                        categories.append(category)
                        break
                    for regex in entry['regex']:
                        if re.search(regex, relpath):
                            categories.append(category)
                            break
                    else:
                        continue
        return categories
    
    def add_to_grouping(self,relpath,style,group):
        if style not in self.groupings:
            self.groupings[style] = {}
        if group not in self.groupings[style]:
            self.groupings[style][group] = []
        self.groupings[style][group].append(relpath)

    def categorize_for_style(self,relpath,style):
        for entry in self.group_config[style]:
            if 'folder' not in entry or entry['folder'] in relpath:
                for regex in entry['regex']:
                    matches = re.search(regex,relpath)
                    if matches:
                        try:
                            self.add_to_grouping(relpath,style,matches.group(1))
                        except:
                            self.add_to_grouping(relpath,style,'__nomatch__')
                        return True

    def add_to_groupings(self,relpath):
        for style in self.group_config:
            if not self.categorize_for_style(relpath,style):
                self.add_to_grouping(relpath,style,'__unmatched__')

    def gather_database(self):
        """Return all matching files beneath the path."""
        for root, dirs, files in os.walk(self.basepath):
            relpath = os.path.relpath(root,self.basepath)
            for fn in filter(TrackDatabase.MUSIC_FILES.search, sorted(files)):
                filename = os.path.join(root, fn)
                playpath = os.path.join(relpath, fn)
                self.add_to_groupings(playpath)
                        
        # Seems to be working
        print(self.groupings)

                # print(f'fn:{fn} full:{filename}')
                # Path(filename)
