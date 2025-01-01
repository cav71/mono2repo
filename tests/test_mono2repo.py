import pathlib

import pytest

from mono2repo import mono2repo


@pytest.fixture(scope="function")
def myfs(tmp_path):
    (tmp_path / "a/b/root/d/e/f").mkdir(parents=True)
    (tmp_path / "a/b/root/.git").mkdir(parents=True)
    (tmp_path / "a/b/root/.git/testme").touch()
    yield tmp_path


def test_platform(platform):
    assert platform in {"windows", "darwin", "linux"}


def test_which(platform):
    if platform == "windows":
        assert mono2repo.which("CMD.EXE") == r"C:\Windows\System32\cmd.exe"
    else:
        assert mono2repo.which("ls") in {"/bin/ls", "/usr/bin/ls"}


@pytest.mark.parametrize(
    "uri, expected",
    [
        ("ow", ValueError()),
        (
            "https://a.domain.org/some/repo.git/adir/asubdir",
            (
                "https://a.domain.org/some/repo.git",
                "adir/asubdir",
            ),
        ),
    ],
)
def test_split_source(uri, expected):
    if isinstance(expected, Exception):
        pytest.raises(expected.__class__, mono2repo.split_source, uri)
    else:
        found = mono2repo.split_source(uri)
        assert expected == found


def test_findroot(myfs):
    import os

    assert (myfs / "a/b/root/.git/testme").exists()
    expected = myfs / "a/b/root"
    pytest.raises(mono2repo.InvalidGitDir, mono2repo.Git.findroot, myfs / "a/b")
    assert (expected, "") == mono2repo.Git.findroot(myfs / "a/b/root")
    assert (expected, str(pathlib.Path("d/e"))) == mono2repo.Git.findroot(
        myfs / "a/b/root/d/e"
    )
    try:
        cdir = os.getcwd()
        os.chdir(myfs / "a/b/root")
        assert (expected, "") == mono2repo.Git.findroot(".")
    finally:
        os.chdir(cdir)
