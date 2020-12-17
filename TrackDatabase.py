"""Gathers information about tracks and make configured playlists"""

from argparse import ArgumentParser
import os
import shutil
from pathlib import Path
from hsaudiotag import auto
import yaml
import re
import copy
import random
from Playlist import Playlist

class TrackDatabase():
    MUSIC_FILES = re.compile(r'.mp3$', re.I)

    def __init__(self, basepath):
        self.groupings = {}
        self.basepath = basepath
        self.parse_config('playlists.yml')
        self.gather_database()
        self.build_playsets()

    def parse_config(self, path):
        self.categories = {}
        self.group_config = {}
        self.playlists = {}
        if os.path.isfile(path):
            with open(path,'r') as configfile:
                raw_config = yaml.load(configfile, Loader=yaml.FullLoader)
        if 'categories' not in raw_config:
            raw_config['categories'] = {}
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
        folder = os.path.dirname(relpath)
        for entry in self.group_config[style]:
            if 'folder' not in entry or entry['folder'] in relpath:
                if 'folder' in entry:
                    folder = entry['folder']
                for regex in entry['regex']:
                    matches = re.search(regex,relpath)
                    if matches:
                        try:
                            self.add_to_grouping(relpath,style,f"{entry['name']}_{folder}_{matches.group(1).strip()}")
                        except IndexError:
                            self.add_to_grouping(relpath,style,f"{entry['name']}_{folder}")
                        return
        # If it was otherwise unmatched, store it as itself.
        self.add_to_grouping(relpath,style,relpath)

    def add_to_groupings(self,relpath):
        for style in self.group_config:
            self.categorize_for_style(relpath,style)

    def gather_database(self):
        """Return all matching files beneath the path."""
        for root, dirs, files in os.walk(self.basepath):
            relpath = os.path.relpath(root,self.basepath)
            for fn in filter(TrackDatabase.MUSIC_FILES.search, sorted(files)):
                filename = os.path.join(root, fn)
                playpath = os.path.join(relpath, fn)
                self.add_to_groupings(playpath)

    def song_matches_category(self,song,category):
        for expression in self.categories[category]:
            if not 'regex' in expression:
                folder = '^' + re.escape(expression['folder'])
                if re.search(folder,song):
                    return True
            else:
                for regex in expression['regex']:
                    if 'folder' in expression:
                        fullexpression = f"^{re.escape(expression['folder'])}/{regex}"
                    else:
                        fullexpression = regex
                    # if 'Christmas' in song:
                    if re.search(fullexpression,song):
                        return True
        return False


    def get_playset_includes(self,*,inclusions,style):
        if len(inclusions) == 0:
            return copy.deepcopy(self.groupings[style])
        songset = {}
        for inclusion in inclusions:
            for key in self.groupings[style]:
                for song in self.groupings[style][key]:
                    if self.song_matches_category(song,inclusion):
                        if key not in songset:
                            songset[key] = []
                        songset[key].append(song)
        return songset

    def remove_playset_excludes(self,*,playset,exclusions,style):
        for exclusion in exclusions:
            for key in playset:
                for song in copy.deepcopy(playset[key]):
                    if self.song_matches_category(song,exclusion):
                        playset[key].remove(song)

    def build_playsets(self):
        for playlist in self.playlists:
            self.playlists[playlist]['grouplist'] = self.get_playset_includes(
                inclusions=self.playlists[playlist]['include'],
                style=self.playlists[playlist]['grouping'])
            self.remove_playset_excludes(playset=self.playlists[playlist]['grouplist'],
                exclusions=self.playlists[playlist]['exclude'],
                style=self.playlists[playlist]['grouping'])

    def make_playlists(self,folder):
        shutil.rmtree(folder,ignore_errors=True)
        os.makedirs(f'{folder}/relative')
        os.makedirs(f'{folder}/absolute')
        for playlist in self.playlists:
            groups = [*self.playlists[playlist]['grouplist']]
            random.shuffle(groups)
            self.playlists[playlist]['tracklist'] = []
            for group in groups:
                self.playlists[playlist]['tracklist'].extend(self.playlists[playlist]['grouplist'][group])
            abslist = Playlist([os.path.join(self.basepath,path) for path in self.playlists[playlist]['tracklist']])
            abslist.write_file(f'{folder}/relative/{playlist}.pls',relpath=self.basepath)
            abslist.write_file(f'{folder}/absolute/{playlist}.pls')
