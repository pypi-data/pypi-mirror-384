# FileTrack

[CHANGELOG](CHANGELOG.md)

[FileTrack](https://github.com/kyan001/PyFileTrack) is a filetracking cli tool that can track file changes in a certain folder.

## Get Started

```sh
pip install filetrack  # Install

filetrack  # Run FileTrack according `filetrack.toml` in current folder.
filetrack -h/--help  # Show help message.
filetrack -v/--version  # Show version.
filetrack -c/--config $config_file  # Run FileTrack according to the config file.
```

## Installation

```sh
# pip
pip install --user filetrack  # install filetrack
pip install --upgrade filetrack # upgrade filetrack
pip uninstall filetrack  # uninstall filetrack

# pipx (recommanded)
pipx install filetrack  # install filetrack through pipx
pipx upgrade filetrack  # upgrade filetrack through pipx
pipx uninstall filetrack  # uninstall filetrack through pipx
```

## Config File

* Config file example: [filetrack.toml]

## Knowledge Base

* Trackings: File hashes to track changes.
* TrackFile: The output file to hold file trackings.
* TrackFile Format: Can choose from `TOML` or `JSON`
* Target File Exts: Files that you wanna track with specific extensions. Leave it empty `[]` to track all files.
* Old TrackFile: Autodetect and parse old TrackFile to compared with.
