# psl-playlist
Writes PSL playlists based on a music library and configuration files.
See playlist-template.yml for an example of how to create that database.

For now, the usage is to create that database and then run

`./create.py </path/to/your/music/folder>`

It will generate the configured playlists with relative paths at
`output/relative` and with absolute paths at `output/absolute`.
