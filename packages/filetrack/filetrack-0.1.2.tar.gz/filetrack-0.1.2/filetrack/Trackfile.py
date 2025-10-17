import os
import socket
import datetime
import platform

import consoleiotools as cit
import consolecmdtools as cct


class Trackfile:
    def __init__(self, trackfile_dir: str = os.getcwd(), prefix: str = "FileTrack-", format: str = "json", group_by: str = ""):
        """Initialize Trackfile object.

        Args:
            trackfile_dir (str): The directory path of the trackfile.
            prefix (str): The prefix of the trackfile.
            format (str): The output format. Options: "json", "toml".
            group_by (str): Group by. Default is "" meaning no group. Options: "host", "os", "".
        """
        self.prefix = prefix
        self.trackfile_dir = trackfile_dir
        self.format = format
        if self.format.upper() == "TOML":
            import tomlkit  # lazyload
            self.suffix = ".toml"
            self.formatter = tomlkit
        elif self.format.upper() == "JSON":
            import json  # lazyload
            self.suffix = ".json"
            self.formatter = json
        else:
            raise Exception(f"Output format `{self.format}` does not support")
        self.group_by = group_by
        self.trackings = {}

    def __str__(self) -> str:
        return self.path

    @property
    def files(self) -> list:
        def filename_filter(path: str) -> bool:
            filename = cct.get_path(path).basename
            if filename.startswith(self.prefix) and filename.endswith(self.suffix):
                if self.group_by and (self.group not in filename):
                    return False
                return True
            return False

        trackfile_list = cct.get_paths(self.trackfile_dir, filter=filename_filter)
        return sorted(trackfile_list)

    @property
    def latest(self) -> str:
        if not self.files:
            return ""
        return self.files[-1]

    @property
    def group(self) -> str:
        if self.group_by == "host":
            return self.hostname
        elif self.group_by == "os":
            return platform.system()
        elif self.group_by == "":
            return ""
        cit.err(f"Unsupported group_by: {self.group_by}")
        exit(1)

    @property
    def filename(self):
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.prefix}{now}{'-' if self.group else ''}{self.group}{self.suffix}"

    @property
    def path(self):
        return cct.get_path(os.path.join(self.trackfile_dir, self.filename))

    def compare_with(self, trackfile: "Trackfile") -> tuple[list, list]:
        trackings_1 = set(self.trackings.items())
        trackings_2 = set(trackfile.trackings.items())
        return [filename for filename, filehash in trackings_1 - trackings_2], [filename for filename, filehash in trackings_2 - trackings_1]

    @property
    def hostname(self) -> str:
        """Get hostname and check if hostname is new."""
        host = socket.gethostname().replace("-", "").replace(".", "")  # default hostname
        return host

    @cit.as_session("Cleanup Outdated TrackFiles")
    def cleanup_outdated_trackfiles(self):
        if len(self.files) > 1:
            old_trackfiles = self.files[:-1]  # exclude the latest one
            cit.ask(f"Cleanup {len(old_trackfiles)} old TrackFiles?")
            for trackfile in old_trackfiles:
                cit.echo(cct.get_path(trackfile).basename, pre="*")
            if cit.get_choice(["Yes", "No"]) == "Yes":
                for filepath in old_trackfiles:
                    os.remove(filepath)
                cit.info("Cleanup done")
            else:
                cit.warn("Cleanup canceled")

    @cit.as_session("Saving TrackFile")
    def to_file(self):
        with open(self.path, "w", encoding="UTF8") as f:
            options = {}
            if self.format == "JSON":
                options = {"indent": 4, "ensure_ascii": False}
            f.write(self.formatter.dumps(self.trackings, **options))
            cit.info(f"New TrackFile created: [u]{self.path.basename}[/]")

    @cit.as_session("Loading Old TrackFile")
    def from_file(self, path: str) -> bool:
        """Parse a TrackFile and load trackings into instance.

        Args:
            path (str): Path to the TrackFile.

        Returns:
            bool: True if successful.
        """
        if not path:
            return False
        path = cct.get_path(path)
        if not path.is_file:
            cit.warn("No TrackFile loaded.")
            return False
        cit.info(f"Parsing TrackFile `{path.basename}`")
        with open(path, encoding="UTF8") as fl:
            trackings = self.formatter.loads(fl.read())
            cit.info(f"{len(trackings)} entries loaded")
        self.trackings = trackings
        return True

    def target_files(self, target_dir: str = os.getcwd(), exts: list = []) -> list:
        """Get target files in the target directory.

        Args:
            target_dir (str): Target directory to scan.
            exts (list[str]): Accepted file extensions. Ex. ["mp3", "m4a"]. Default is [] meaning all files.

        Returns:
            list: List of target file paths.
        """
        paths = []
        if not exts:
            paths += cct.get_paths(target_dir, filter=os.path.isfile)
        else:
            for ext in exts:
                target_file_pattern = f".{ext}"
                cit.info(f"Target file pattern: {target_file_pattern}")
                paths += cct.get_paths(target_dir, filter=lambda path: path.name.endswith(target_file_pattern))
        return paths

    @cit.as_session("Generating New TrackFile")
    def generate(self, target_dir: str = os.getcwd(), exts: list = [], hash_mode: str = "CRC32"):
        """Generate file tracking information.

        Args:
            target_dir (str): Target directory to scan.
            exts (list[str]): Accepted file extensions. Ex. ["mp3", "m4a"]. Default is [] meaning all files.
            hash_mode (str): "XXHASH", "CRC32", "MD5", "NAME", "PATH", "MTIME".

        Returns:
            dict: {filename: filehash}
        """
        def find_duplicates(paths: list) -> list:
            """Find duplicate filename files in the list of paths.

            Returns:
                list: List of duplicate filepaths.
            """
            duplicate_files = set()
            files = {}
            for filepath in paths:
                filepath = cct.get_path(filepath)
                if path := files.get(filepath.basename):
                    duplicate_files.add(path)
                    duplicate_files.add(filepath)
                else:
                    files[filepath.basename] = filepath
            return list(duplicate_files)

        paths = self.target_files(target_dir, exts)
        cit.info(f"Target files: {len(paths)}")
        if paths:
            duplicate_files = find_duplicates(paths)
            cit.info(f"Duplicate files: {len(duplicate_files)}")
            for filepath in cit.track(paths, "Hashing...", unit="files"):
                filepath = cct.get_path(filepath)
                match hash_mode.lower():  # >=3.10
                    case "xxhash":
                        import xxhash  # lazyload

                        with open(filepath, 'rb') as f:
                            filehash = xxhash.xxh3_64_hexdigest(f.read())
                    case "crc32":
                        filehash = cct.crc32(filepath)
                    case "md5":
                        filehash = cct.md5(filepath)
                    case "mtime":
                        filehash = int(os.path.getmtime(filepath))
                    case "name":
                        filehash = filepath.basename
                    case "path":
                        filehash = filepath.abs
                    case _:
                        cit.err(f"Unsupported hash mode: {hash_mode}")
                        exit(1)
                filehash = str(filehash)
                if oldhash := self.trackings.get(filepath.basename):
                    self.trackings[filepath.basename] = ",".join([oldhash, filehash])
                else:
                    self.trackings[filepath.basename] = filehash
