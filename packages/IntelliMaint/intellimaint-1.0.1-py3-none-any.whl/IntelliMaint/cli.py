import argparse

from __version__ import __version__


def main():
    """
    IntelliMaint command-line interface.
    """
    parser = argparse.ArgumentParser(description="IntelliMaint CLI")
    parser.add_argument(
        "-v", "--version", action="version", version=f"IntelliMaint version {__version__}"
    )
    parser.parse_args()

