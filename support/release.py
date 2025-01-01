#!/usr/bin/env python
from __future__ import annotations

import argparse
import contextlib
import dataclasses as dc
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).parent))
import common


@dc.dataclass
class File:
    path: Path
    lines: list[str] = dc.field(default_factory=list)

    def __post_init__(self):
        self.lines = self.path.read_text().split("\n")

    def save(self):
        self.path.write_text("\n".join(self.lines))

    def find(self, call):
        result = []
        for lineno, line in enumerate(self.lines):
            if ret := call(line):
                result.append((lineno, line, ret))
        if len(result) > 1:
            raise RuntimeError(f"too many matches: {result}")
        return result[0] if result else (None, None, None)

    def find_var(self, key):
        expr = re.compile(
            r"\s*" + key + r"\s*[=]\s*(?P<quote>['\"])(?P<value>(\d+([.]\d)*)?)\1"
        )
        return self.find(lambda line: expr.search(line))

    def replace_or_append(self, txt, lineno):
        if lineno is None:
            self.lines.append(txt)
        else:
            self.lines[lineno] = txt


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("versionfile", type=Path)
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--local", action="store_true")
    parser.add_argument(
        "-n", "--dry-run", dest="dryrun", action="store_true", help="dry run"
    )
    options = parser.parse_args(args)
    options.error = parser.error
    return options


def main(args):
    github_dump = common.github_dump_from_local() if args.local else os.getenv("GITHUB_DUMP")
    if not github_dump:
        args.error("missing GITHUB_DUMP variable")
    gdata = common.github_dump_validate(github_dump)

    with common.savefiles() as save:
        # update pyproject.toml
        pyproject = File(save("pyproject.toml"))

        lineno, line, ret = pyproject.find_var("version")
        current = ret.group("value")
        version = current if args.release else f"{current}b{gdata['run_number']}"
        if current != version:
            pyproject.lines[lineno] = f'version = "{version}"'
            pyproject.save()

        # update versionfile
        versionfile = File(save(args.versionfile))

        lineno, line, ret = versionfile.find_var("__version__")
        versionfile.replace_or_append(f'__version__ = "{version}"', lineno)

        lineno, line, ret = versionfile.find_var("__hash__")
        versionfile.replace_or_append(f"__hash__ = \"{gdata['sha']}\"", lineno)

        versionfile.save()

        if not args.dryrun:
            subprocess.check_call([sys.executable, "-m", "build"])  # noqa: S603


if __name__ == "__main__":
    main(parse_args())
