#!/usr/bin/env python
"""extract from a mono repo a single project

Example:
   ./mono2repo create https://github.com/cav71/pelican.git/pelican/themes/notmyidea outputdir

"""
import os
import re
import contextlib
import logging
import platform
import argparse
import pathlib
import subprocess
import shutil
import tempfile


log = logging.getLogger(__name__)


def which(exe):
    cmd = {
        "unix" : "which",
        "windows" : "where",
    }[platform.uname().system.lower()]
    return subprocess.check_output([cmd, exe], encoding="utf-8").strip()


def run(args, abort=True, silent=False, dryrun=False):
    cmd = [args] if isinstance(args, str) else args
    if dryrun:
        return [str(c) for c in cmd]
    try:
        return subprocess.check_output([str(c) for c in cmd], encoding="utf-8",
            stderr=subprocess.DEVNULL if silent else None).strip()
    except:
        if abort is True:
            raise
        elif abort:
            raise abort


@contextlib.contextmanager
def tempdir(tmpdir=None):
    path = tmpdir or pathlib.Path(tempfile.mkdtemp())
    try:
        path.mkdir(parents=True, exist_ok=True)
        yield path
    finally:
        if not tmpdir:
            log.debug("cleaning up tmpdir %s", path)
            shutil.rmtree(path, ignore_errors=True)
        else:
            log.debug("leaving behind tmpdir %s", tmpdir)


def split_source(path):
    if re.search("^(http|https|git):", str(path)):
        assert ".git" in str(path), f"no .git in path {path}"
        path1 = path[:path.find(".git")] + ".git"
        subdir1 = path[path.find(".git")+4:].lstrip("/")
        return (path1, subdir1)
    else:
        return Git.findroot(path)


class Git:
    @staticmethod
    def findroot(path):
        path = path or pathlib.Path(os.getcwd())
        cpath = pathlib.Path(path)
        while cpath.parent != cpath:
            if (cpath / ".git").exists():
                subpath = pathlib.Path(path).relative_to(cpath)
                return cpath, "" if str(subpath) == "." else str(subpath)
            cpath = cpath.parent
        raise RuntimeError("cannot find git root", path)

    @staticmethod
    def clone(uri, dst):
        if not dst.exists():
            subprocess.check_call(["git", "clone", uri, dst])
        return Git(dst)

    def __init__(self, worktree=None):
        self.worktree = worktree or pathlib.Path(os.getcwd())

    def __repr__(self):
        return f"<{self.__class__.__name__} worktree={self.worktree} at {hex(id(self))}>"

    def run(self, args, **kwargs):
        cmd = [ "git", ]
        if self.worktree:
            cmd += [ "-C", self.worktree, ]
        cmd.extend([args] if isinstance(args, str) else args)
        return run(cmd, **kwargs)

    # commands
    def check(self, args):
        ret = self.run(args, abort=False, silent=True)
        return None if ret is None else ret.strip()

    def st(self):
        return self.run("status")

    def init(self, branch=None):
        if not self.worktree.exists():
            self.worktree.mkdir(parents=True, exist_ok=True)
        self.run("init")
        if branch:
            self.run(["checkout", "-b", branch], silent=True)


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    sbs = parser.add_subparsers()
    subparsers = {
        "create": create,
        "update": update,
    }

    for name, func in subparsers.items():
        p = sbs.add_parser(name)
        p.add_argument("-v", "--verbose", action="store_true")
        p.set_defaults(func=func)
        subparsers[name] = p

    for name in [ "create", "update", ]:
        subparsers[name].add_argument("source")
        subparsers[name].add_argument("output", type=pathlib.Path)

    options = parser.parse_args(args)
    options.error = p.error
    logging.basicConfig(level=logging.DEBUG if getattr(options, "verbose") else logging.INFO)
    return options
    

def create(igit, ogit, subdir):
    # prepping the legacy tree

    # filter existing commits
    igit.run([ "filter-repo", 
               "--path", f"{subdir}/",
               "--path-rename", f"{subdir}/:" ])

    # extract latest mod date 
    txt = igit.run(["log", "--reverse", "--format=\"%t|%cd|%s\""])
    date = txt.split("\n")[0].split("|")[1]
    log.debug("got latest date [%s]", date)

    # Create a new (empty) repository
    log.debug("initializing work tree in %s", ogit.worktree)
    ogit.init("master")
    ogit.run(["commit", "--allow-empty",
                "-m", "Initial commit", "--date", date])

    # Add legacy plugin clone as a remote and
    #  pull contents into new branch
    ogit.run(["remote", "add", "legacy", igit.worktree])
    try:
        ogit.run(["fetch", "legacy", "master",])
        ogit.run(["checkout", "-b", "migrate", "--track", "legacy/master"])
        ogit.run(["rebase", "--committer-date-is-author-date", "master"])
    finally:
        ogit.run(["remote", "remove", "legacy"])


def update(igit, ogit, subdir):
    # prepping the legacy tree

    # filter existing commits
    igit.run([ "filter-repo", 
               "--path", f"{subdir}/",
               "--path-rename", f"{subdir}/:" ])

    # Add legacy plugin clone as a remote and
    #  pull contents into new branch
    ogit.run(["remote", "add", "legacy", igit.worktree])
    try:
        ogit.run(["fetch", "legacy", "master",])
        ogit.run(["checkout", "-B", "migrate", "--track", "legacy/master"])
        ogit.run(["rebase", "--committer-date-is-author-date", "master"])
    finally:
        ogit.run(["remote", "remove", "legacy"])


def main(options):
    func, error = options.func, options.error
    [ delattr(options, m) for m in [ "func", "error", "verbose", ] ]

    log.debug("found system %s", platform.uname().system.lower())
    log.debug("git version [%s]", run(["git", "--version"]))

    filter_repo_version = run(["git", "filter-repo", "--version"], False, True)
    if not filter_repo_version:
        options.error("missing filter-repo git plugin"
                      " (https://github.com/newren/git-filter-repo)")
    log.debug("filter-repo [%s]", filter_repo_version)

    source, subdir = split_source(options.source)
    log.debug("source subdir [%s]", subdir)

    with tempdir() as tmpdir:
        igit = Git.clone(source, tmpdir / "legacy-repo")
        log.debug("input client %s", igit)

        ogit = Git(worktree=options.output.resolve())
        log.debug("output client %s", ogit)

        func(igit, ogit, subdir)


if __name__ == "__main__":
    main(parse_args())
