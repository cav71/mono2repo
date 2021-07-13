#!/usr/bin/env python
"""extract from a mono repo a single project

Example:
   ./mono2repo init outputdir \\
        https://github.com/cav71/pelican.git/pelican/themes/notmyidea

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


__version__ = "0.0.5"
__hash__ = ""

log = logging.getLogger(__name__)


class Mono2RepoError(Exception):
    pass


class InvalidGitUriError(Mono2RepoError):
    pass


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


def split_source(path):
    if re.search("^(http|https|git):", str(path)) or str(path).startswith("git@github.com:"):
        assert ".git" in str(path), f"no .git in path {path}"
        path1 = path[:path.find(".git")] + ".git"
        subdir1 = path[path.find(".git")+4:].lstrip("/")
        return (path1, subdir1)
    raise ValueError("invalid git uri", path)


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
        self.worktree = pathlib.Path(worktree or os.getcwd())

    def __repr__(self):
        return f"<{self.__class__.__name__} branch={self.branch or 'undef'} worktree={self.worktree} at {hex(id(self))}>"

    def run(self, args, **kwargs):
        cmd = [ "git", ]
        if self.worktree:
            cmd += [ "-C", self.worktree, ]
        cmd.extend([args] if isinstance(args, str) else args)
        return run(cmd, **kwargs)

    # commands
    def good(self):
        with contextlib.suppress(subprocess.CalledProcessError):
            self.run(["status"], silent=True)
            return True

    @property
    def branch(self):
        if self.good():
            return self.run(["branch", "--show-current",]).strip()

    @branch.setter
    def branch(self, value):
        self.run(["checkout", value])
        return self.branch

    def init(self, branch=None):
        if not self.worktree.exists():
            self.worktree.mkdir(parents=True, exist_ok=True)
        self.run("init")
        if branch:
            self.run(["checkout", "-b", branch], silent=True)


def parse_args(args=None):
    if isinstance(args,  (list, tuple, None.__class__)):
        args = None if args is None else [ str(a) for a in args]
    else:
        return args

    class F(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
        pass
    parser = argparse.ArgumentParser(formatter_class=F, description="""
Create a new git checkout from a git repo.
""",  epilog="""
Eg.
    mono2repo init summary-extracted \\
        https://github.com/getpelican/pelican-plugins.git/summary

    mono2repo update summary-extracted

""".rstrip())
    parser.add_argument('--version', action='version', version=f"%(prog)s {__version__}")

    sbs = parser.add_subparsers(dest="action", title="actions")
    sbs.required = True

    def subparser(name, func):
        p = sbs.add_parser(name)
        p.set_defaults(func=func)
        p.add_argument("-v", "--verbose", action="store_true")
        p.add_argument("--tmpdir", type=pathlib.Path)
        return p

    # init
    p = subparser("init", init)
    p.add_argument("output", type=pathlib.Path)
    p.add_argument("uri")

    p = subparser("update", update)
    p.add_argument("output", type=pathlib.Path)
    p.add_argument("uri", nargs="?")

    options = parser.parse_args(args)
    options.error = parser.error

    logging.basicConfig(level=logging.DEBUG if options.verbose else logging.INFO)
    return options


def init(igit, ogit, subdir):
    assert (igit.worktree / subdir).exists()

    # prepping the legacy tree

    # filter existing commits
    log.debug("filtering existing commits")
    igit.run([ "filter-repo",
               "--path", f"{subdir}/",
               "--path-rename", f"{subdir}/:" ])

    # extract latest mod date
    log.debug("get latest modification date")
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
    ogit.run(["remote", "add", "legacy-repo", igit.worktree])
    try:
        ogit.run(["fetch", "legacy-repo", "master",])
        ogit.run(["checkout", "-B", "migrate", "--track", "legacy-repo/master"])
        ogit.run(["rebase", "--committer-date-is-author-date", "master"])
    finally:
        ogit.run(["remote", "remove", "legacy-repo"])


@contextlib.contextmanager
def universe(tmpdir, output, func, error, uri):
    """
        (ogit) output/
        (igit) <tmpdir>/legacy-repo
    """

    ogit = Git(worktree=output.resolve())
    log.debug("output client %s", ogit)

    if func == init and ogit.good():
        error(f"directory already initialized, {ogit}")

    branch = ogit.branch
    if func == update:
        if not ogit.good():
            error(f"directory not ready/present/initialized, {ogit}")
        if ogit.run(["status", "-s", "--porcelain"]).strip():
            error(f"directory not clean (eg. git status has modification) on {ogit}")
        if branch != "migrate":
            ogit.branch = "migrate"
            log.debug("switched from branch %s on %s", branch, ogit)

    if uri:
        source, subdir = split_source(uri)
    else:
        log.debug(f"getting source/subdir info from {ogit}")
        txt = ogit.run(["config", "--local", "--get", "mono2repo.uri"])
        source, subdir = split_source(txt)
    log.debug("git repo source [%s]", source)
    log.debug("repo subdir [%s]", subdir)

    with tempdir(tmpdir) as tmp:
        igit = Git.clone(source, tmp / "legacy-repo")
        log.debug("input client %s", igit)
        if not (igit.worktree / subdir).exists():
            error(f"no subdir {subdir} under {igit}")

        try:
            yield ogit, igit, subdir
        finally:
            if branch == "migrate":
                ogit.branch = branch
                log.debug("restoring to old branch %s, %s", branch, ogit)
        if uri:
            # finally we'll leave the configuration parameters for the update
            log.debug("writing config uri in {ogit}")
            ogit.run(["config", "--local", "mono2repo.uri", uri, ])


def main(options=None):
    options = parse_args(options)
    log.debug("found system %s", platform.uname().system.lower())
    log.debug("git version [%s]", run(["git", "--version"]))

    filter_repo_version = run(["git", "filter-repo", "--version"], False, True)
    if not filter_repo_version:
        options.error("missing filter-repo git plugin"
                      " (https://github.com/newren/git-filter-repo)")
    log.debug("filter-repo [%s]", filter_repo_version)

    kwargs = { n: getattr(options, n) for n in {"tmpdir", "output", "func", "error", "uri" } }
    with universe(**kwargs) as (ogit, igit, subdir):
        options.func(igit, ogit, subdir)


if __name__ == "__main__":
    main(parse_args())
