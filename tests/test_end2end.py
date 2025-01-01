# PYTHONPATH=$(pwd) S=git@github.com:cav71/pelican-plugins.git/summary py.tests -vvs tests/test_end2end.py -m manual  # noqa: E501

import os
import shutil
import subprocess
import sys
import uuid

import pytest

from mono2repo import mono2repo

pytestmark = pytest.mark.manual


@pytest.fixture(scope="module", autouse=True)
def setup():
    # S points to a git writeable report
    #  (eg. git@github.com:<username>/pelican-plugins.git/summary)
    assert os.getenv("S"), "unset environment variable S"


def get_commits(git, subdir=None, astype=set):
    subdir = (
        [
            subdir,
        ]
        if subdir
        else []
    )
    result = [
        " ".join(loglines.split(" ")[1:])
        for loglines in git.run(["log", "--pretty=oneline", *subdir]).split("\n")
    ]
    return astype(result) if astype else result


@pytest.mark.parametrize("climode", [True, False])
def test_end2end(tmpdir, climode):
    tag = str(uuid.uuid1())

    # layout under tmpdir
    # ├── converted
    # ├── legacy-repo
    # └── source

    # clone the repo (source)
    uri, subdir = mono2repo.split_source(os.getenv("S"))
    source = mono2repo.Git.clone(uri, tmpdir / "source")
    source.run(["log", "--pretty=oneline", subdir])
    source_commits = get_commits(source, subdir)

    # do the extract (converted and legacy-repo)
    cmd = [
        sys.executable,
        mono2repo.__file__,
    ]
    cmd += [
        "init",
    ]
    cmd += ["--tmpdir", tmpdir]
    cmd += [
        tmpdir / "converted",
        os.getenv("S"),
    ]

    if climode:
        subprocess.check_call([str(c) for c in cmd])
    else:
        mono2repo.main(cmd[2:])

    converted = mono2repo.Git(tmpdir / "converted")
    assert converted.branch == "master"
    converted.branch = "migrate"
    converted_commits = get_commits(converted)

    # verify the conversion
    left = set(p.name for p in (source.worktree / subdir).glob("*"))
    right = set(p.name for p in converted.worktree.glob("*"))
    assert left == (right - {".git"})

    assert (converted_commits - source_commits) == {"Initial commit"}

    # remove the legacy-repo
    shutil.rmtree((tmpdir / "legacy-repo"), ignore_errors=True)

    # end2end
    source_commits = get_commits(source, subdir)

    # adds a new file
    # modify the source dir and push the changes
    path = source.worktree / subdir / tag
    with path.open("w") as fp:
        print("Some random text", file=fp)
    source.run(["add", path])
    source.run(["commit", "-m", f"added {tag}", path])
    source.run(
        [
            "push",
        ]
    )

    # update the converted repo
    cmd = [
        sys.executable,
        mono2repo.__file__,
    ]
    cmd += [
        "update",
    ]
    cmd += ["--tmpdir", tmpdir]
    cmd += [
        converted.worktree,
    ]

    if climode:
        subprocess.check_call([str(c) for c in cmd])
    else:
        mono2repo.main(cmd[2:])
    converted_commits = get_commits(converted)

    assert (converted_commits - source_commits) == {"Initial commit", f"added {tag}"}

    left = set(p.name for p in (source.worktree / subdir).glob("*"))
    right = set(p.name for p in converted.worktree.glob("*"))
    assert left == (right - {".git"})
