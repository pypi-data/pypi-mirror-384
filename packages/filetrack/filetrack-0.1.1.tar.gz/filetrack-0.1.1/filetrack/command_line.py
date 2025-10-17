import argparse

import consoleiotools as cit

import filetrack


README_URL = "https://github.com/kyan001/PyFileTrack/blob/main/README.md"


def main(assigned_args: list | None = None):
    parser = argparse.ArgumentParser(prog="filetrack", description="Tracking file changes.", epilog=f"Checkout README for more details: {README_URL}")
    parser.add_argument("-v", "--version", action="version", version=filetrack.__version__)
    parser.add_argument("-c", "--config", dest="config", default="filetrack.toml", help="The path or the file name of the config file.")
    args = parser.parse_args(assigned_args)
    filetrack.run_filetrack(args.config)


if __name__ == "__main__":
    main()
    cit.pause()
