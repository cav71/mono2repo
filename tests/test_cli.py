# test to garantee the cli interface is robust
import pathlib
import platform
import sys

import pytest

from mono2repo import mono2repo

pyv = tuple(int(v) for v in platform.python_version_tuple())

PNAME = pathlib.Path(sys.argv[0]).name


def test_parse_no_args(capsys):
    pytest.raises(SystemExit, mono2repo.parse_args, [])
    expected = f"""
usage: {PNAME} [-h] [--version] {{init,update}} ...
{PNAME}: error: the following arguments are required: action
""".lstrip()
    captured = capsys.readouterr()
    assert captured.err == expected


def test_parse_help_args(capsys):
    args = ["--help"]
    pytest.raises(SystemExit, mono2repo.parse_args, args)
    fixes = {
        "optional arguments": "optional arguments",
    }
    if pyv >= (3, 10):
        fixes["optional arguments"] = "options"

    expected = f"""
usage: {PNAME} [-h] [--version] {{init,update}} ...

Create a new git checkout from a git repo.

{fixes['optional arguments']}:
  -h, --help     show this help message and exit
  --version      show program's version number and exit

actions:
  {{init,update}}

Eg.
    mono2repo init summary-extracted \\
        https://github.com/getpelican/pelican-plugins.git/summary

    mono2repo update summary-extracted
""".strip()
    assert capsys.readouterr().out.strip() == expected


def test_parse_invalid_init_args(capsys):
    args = ["init"]
    pytest.raises(SystemExit, mono2repo.parse_args, args)
    expected = f"""
usage: {PNAME} init [-h] [-v] [--tmpdir TMPDIR] [--branch MIGRATE] output uri
{PNAME} init: error: the following arguments are required: output, uri
""".strip()

    assert capsys.readouterr().err.strip() == expected
