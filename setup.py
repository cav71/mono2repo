import os
import re
import sys
import json
import pathlib
import collections


from setuptools import setup, find_namespace_packages

import mono2repo


def hubversion(gdata, fallback):
    """returns (version, shasum)
    >>> hubversion({
        'ref': 'refs/heads/beta/0.0.4',
        'sha': '2169f90c22e',
        'run_number': '8',
    }, None)
    ('0.0.4b8', '2169f90c22e')
    >>> hubversion({
        'ref': 'refs/tags/release/0.0.3',
        'sha': '5547365c82',
        'run_number': '3',
    }, None)
    ('0.0.3', '5547365c82')
    >>> hubversion({
        'ref': 'refs/heads/master',
        'sha': '2169f90c',
        'run_number': '20',
    }, '123'))
    ('123', '2169f90c')
"""
    txt = gdata["ref"]
    number = gdata['run_number']
    shasum = gdata["sha"]
    head, _, rest = txt.partition("/")

    cases = [
        ("refs/heads/master", fallback,),
        ("refs/heads/beta/", f"b{number}"),
        ("refs/tags/release/", ""),
    ]
    for pat, out in cases:
        if not txt.startswith(pat):
            continue
        return txt[len(pat):] + out, shasum
    raise RuntimeError("unhandled github ref", txt)


def update_version(data, path, fallback):
    if not data:
        return

    gdata = json.loads(data)
    version, thehash = hubversion(gdata, fallback)

    lines = pathlib.Path(path).read_text().split("\n")

    exp = re.compile(r"__version__\s*=\s*")
    exp1 = re.compile(r"__hash__\s*=\s*")
    assert len([ l for l in lines if exp.search(l)]) == 1
    assert len([ l for l in lines if exp1.search(l)]) == 1

    lines = [
        f"__version__ = \"{version}\"" if exp.search(l) else
        f"__hash__ = \"{thehash}\"" if exp1.search(l) else
        l
        for l in lines
    ]

    pathlib.Path(mono2repo.__file__).write_text("\n".join(lines))
    return version


version = update_version(os.getenv("GITHUB_DUMP"),
    mono2repo.__file__,
    mono2repo.__version__)


setup(
    name="mono2repo",
    version=version,
    url="https://github.com/cav71/mono2repo",
    py_modules=["mono2repo",],
    entry_points = {
        'console_scripts': ['mono2repo=mono2repo:main'],
    },
    description="extract a monorepo subdir",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
