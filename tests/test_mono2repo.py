import sys
import pathlib

import pytest
import mono2repo


PNAME = pathlib.Path(sys.argv[0]).name


def test_parse_no_args(capsys):
    pytest.raises(SystemExit, mono2repo.parse_args, [])
    txt = f"""
usage: {PNAME} [-h] [--version] {{init,update}} ...
py.test: error: the following arguments are required: action
""".lstrip()
    captured = capsys.readouterr()
    assert txt == captured.err


def test_parse_help_args(capsys):
    args = [ "--help" ]
    pytest.raises(SystemExit, mono2repo.parse_args, args)
    txt = f"""
usage: {PNAME} [-h] [--version] {{init,update}} ...

Create a new git checkout from a git repo.

optional arguments:
  -h, --help     show this help message and exit
  --version      show program's version number and exit

actions:
  {{init,update}}

Eg.
    mono2repo init summary-extracted \\
        https://github.com/getpelican/pelican-plugins.git/summary

    mono2repo update summary-extracted
""".strip()
    captured = capsys.readouterr()
    assert txt in captured.out.strip()


def test_parse_invalid_init_args(capsys):
    args = [ "init" ]
    pytest.raises(SystemExit, mono2repo.parse_args, args)
    txt = f"""
usage: {PNAME} init [-h] [-v] [--tmpdir TMPDIR] output uri
{PNAME} init: error: the following arguments are required: output, uri
""".strip()
    captured = capsys.readouterr()
    assert txt == captured.err.strip()


@pytest.mark.parametrize("uri, expected", [
    ("ow", ValueError()),
    ("https://a.domain.org/some/repo.git/adir/asubdir",
        ("https://a.domain.org/some/repo.git", "adir/asubdir",),),
])
def test_split_source(uri, expected):
    if isinstance(expected, Exception):
        pytest.raises(expected.__class__, mono2repo.split_source, uri)
    else:
        found = mono2repo.split_source(uri)
        assert expected == found
