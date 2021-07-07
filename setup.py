import os
import re
import sys
import json
import collections


from setuptools import setup, find_namespace_packages

import mono2repo


def hubversion(gdata):
    txt = gdata["ref"]
    number = gdata['run_number']
    shasum = gdata["sha"]
    head, _, rest = txt.partition("/")

    cases = [
        ("refs/heads/master", mono2repo.__version__),
        ("refs/heads/beta/", f"b{number}"),
        ("refs/tags/release/", ""),
    ]
    for pat, out in cases:
        if not txt.startswith(pat):
            continue
        return txt[len(pat):] + out, shasum
    raise RuntimeError("unhandled github ref", txt)


version = mono2repo.__version__
if os.getenv("GITHUB_DUMP"):
    gdata = json.loads(os.getenv("GITHUB_DUMP"))   
    version, thehash = hubversion(gdata)
    with open(mono2repo.__file__) as fp:
        lines = fp.readlines()

    exp = re.compile(r"__version__\s*=\s*")
    exp1 = re.compile(r"__hash__\s*=\s*")

    assert len([ l for l in lines if exp.search(l)]) == 1
    assert len([ l for l in lines if exp1.search(l)]) == 1

    lines = [
        f"__version__ = \"{version}\"\n" if exp.search(l) else
        f"__hash__ = \"{thehash}\"" if exp1.search(l) else
        l
        for l in lines
    ]        

    with open(mono2repo.__file__ + ".new", "w") as fp:
        fp.write("".join(lines))

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
