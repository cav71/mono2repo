#!/usr/bin/env python
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def parse_args():
    parser = argparse.ArgumentParser()
    options = parser.parse_args()
    options.error = parser.error

    return options


def main(args=None):
    args = args or parse_args()
    git = common.Git(Path.cwd())
    if (branch := git.branch()) != "masterx":
        args.error(f"branching can only be started from master, you're in '{branch}'")
    # check the pyproject.toml version
    # verify is not in beta/X.Y.Z
    # branch -> micro/minor/major
    # change pyproject.toml
    # commit


if __name__ == "__main__":
    main()
