import os
import tomllib

import fuzzyfinder
import consolecmdtools as cct
import consoleiotools as cit

from . import Trackfile


__version__ = '0.1.1'


def load_configs(config_path: str, target_dir: str, target_exts: list[str], trackfile_dir: str, trackfile_format: str, hash_mode: str, group_by: str) -> dict:
    """Get configurations from the config file.

    Args:
        config_path (str, optional): The path or the file name of the config file. Defaults to "filetrack.toml".

    Returns:
        dict: The configurations. If the file does not exist, return an empty dict.
    """
    configs = {}
    if config_path:
        if os.path.isfile(config_path):
            with open(config_path, "rb") as fl:
                configs = tomllib.load(fl)
        else:
            cit.warn(f"Config file not found: [u]{config_path}[/]")
    # [target] defaults
    if not configs.get("target"):
        configs['target'] = {}
    if not configs["target"].get("dir"):
        configs['target']['dir'] = target_dir
    if not os.path.isabs(configs['target']['dir']):
        configs['target']['dir'] = os.path.join(cct.get_path(config_path).parent, configs['target']['dir'])
    configs['target']['dir'] = cct.get_path(configs['target']['dir'])
    if not configs['target'].get("exts"):
        configs['target']['exts'] = target_exts
    # [trackfile] defaults
    if not configs.get("trackfile"):
        configs['trackfile'] = {}
    configs['trackfile']['dir'] = configs['trackfile'].get("dir") or trackfile_dir
    if not os.path.isabs(configs['trackfile']['dir']):
        configs['trackfile']['dir'] = os.path.join(cct.get_path(config_path).parent, configs['trackfile']['dir'])
    configs['trackfile']['dir'] = cct.get_path(configs['trackfile']['dir'])
    if not configs['trackfile'].get("format"):
        configs['trackfile']['format'] = trackfile_format
    if not configs['trackfile'].get("hash_mode"):
        configs['trackfile']['hash_mode'] = hash_mode
    if not configs['trackfile'].get("group_by"):
        configs['trackfile']['group_by'] = group_by
    if not configs['trackfile'].get("prefix"):
        configs['trackfile']['prefix'] = "FileTrack-"
    return configs


def diffs(old_ft: Trackfile.Trackfile, new_ft: Trackfile.Trackfile) -> bool:
    """Check if there are any differences between the old and new trackfiles.

    Args:
        old_ft (Filetrack.Trackfile): The old trackfile.
        new_ft (Filetrack.Trackfile): The new trackfile.

    Returns:
        bool: True if there are differences, False otherwise.
    """
    pres = {
        "delete": "[red]-[/]",
        "add": "[green]+[/]",
        "move_from": "[blue]-[/]",
        "move_to": "[blue]+[/]",
    }
    if not old_ft.trackings and not new_ft.trackings:
        return False
    entries_deleted, entries_added = old_ft.compare_with(new_ft)
    if not entries_deleted and not entries_added:
        cit.info("No changes")
        return False
    cit.info("Changes since last time: ✍️")
    for filename in entries_deleted:
        if entries_added:
            fuzzy = list(fuzzyfinder.fuzzyfinder(filename, entries_added))
            if len(fuzzy) > 0:
                cit.echo(f"{pres['move_from']} {filename}")
                cit.echo(f"{pres['move_to']} {fuzzy[0]}")
                entries_added.remove(fuzzy[0])
            else:
                cit.echo(f"{pres['delete']} {filename}")
    for filename in entries_added:
        cit.echo(f"{pres['add']} {filename}")
    return True


def run_filetrack(config_path: str = "filetrack.toml", target_dir: str = ".", target_exts: list[str] = [], trackfile_dir: str = ".", trackfile_format: str = "json", hash_mode: str = "CRC32", group_by: str = ""):
    """Run filetrack

    Args:
        config_path (str, optional): The path or the file name of the config file. Defaults to "filetrack.toml".
        target_dir (str): The directory path of the files to be tracked. Default is config file's parent directory.
        target_exts (list[str], optional): The target extensions. Defaults to TARGET_EXTS.
        trackfile_dir (str): The directory path of the trackfile. Default is config file's parent directory.
        trackfile_format (str, optional): The output format. Defaults to "json". Options: "json", "toml".
        hash_mode (str, optional): The hash mode. Defaults to "CRC32". Options: "XXHASH", "CRC32", "MD5", "NAME", "PATH", "MTIME".
        group_by (str, optional): Group by. Defaults to "". Options: "host", "os", "".
    """
    cit.rule("▶ [yellow]Run Filetrack[/]")
    configs = load_configs(config_path, target_dir, target_exts, trackfile_dir, trackfile_format, hash_mode, group_by)
    old_ft = Trackfile.Trackfile(trackfile_dir=configs['trackfile']['dir'], prefix=configs['trackfile']['prefix'], format=configs['trackfile']['format'], group_by=configs['trackfile']['group_by'])
    new_ft = Trackfile.Trackfile(trackfile_dir=configs['trackfile']['dir'], prefix=configs['trackfile']['prefix'], format=configs['trackfile']['format'], group_by=configs['trackfile']['group_by'])
    cit.info(f"Version: {__version__}")
    cit.info(f"Config File: [u]{config_path}[/]")
    cit.info(f"Target Dir: 📂 [u]{configs['target']['dir']}[/]")
    cit.info(f"Target Extensions: {configs['target']['exts']}")
    cit.info(f"Trackfile Format: {configs['trackfile']['format']}")
    cit.info(f"Trackfile Dir: 📂 [u]{configs['trackfile']['dir']}[/]")
    cit.info(f"Trackfile Prefix: `{configs['trackfile']['prefix']}`")
    cit.info(f"Hash Mode: {configs['trackfile']['hash_mode']}")
    if configs['trackfile']['group_by']:
        cit.info(f"Group by {configs['trackfile']['group_by']}: `{new_ft.group}`")
    # fill trackings
    old_ft.from_file(old_ft.latest)
    new_ft.generate(configs['target']['dir'], configs['target']['exts'], configs['trackfile']['hash_mode'])
    if not old_ft.trackings or diffs(old_ft, new_ft):
        cit.info("[Done]")
        new_ft.to_file()
        new_ft.cleanup_outdated_trackfiles()
