#!/usr/bin/env python
"""extract from a mono repo a single project

Example:
   ./mono2repo init https://github.com/cav71/pelican.git/pelican/themes/notmyidea outputdir

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


__version__ = "0.0.0"
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
    raise argparse.ArgumentError("invalid git uri")


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
    def good(self):
        with contextlib.suppress(subprocess.CalledProcessError):
            self.run(["status"])
            return True
        
    # def check(self, args):
    #     ret = self.run(args, abort=False, silent=True)
    #     return None if ret is None else ret.strip()
    # def st(self):
    #    return self.run("status")

    def init(self, branch=None):
        if not self.worktree.exists():
            self.worktree.mkdir(parents=True, exist_ok=True)
        self.run("init")
        if branch:
            self.run(["checkout", "-b", branch], silent=True)


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    sbs = parser.add_subparsers()
    
    # init
    p = sbs.add_parser("init")
    p.set_defaults(func=init)
    p.add_argument("-v", "--verbose", action="store_true")

    p.add_argument("output", type=pathlib.Path)
    p.add_argument("source", type=split_source)

    p = sbs.add_parser("update")
    p.set_defaults(func=update)
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("output", type=pathlib.Path)
    p.add_argument("source", nargs="?", type=split_source, default=(None, None))
    #subparsers = {
    #    "init": init,
    #    "update": update,
    #}

    #for name, func in subparsers.items():
    #    p = sbs.add_parser(name)
    #    p.add_argument("-v", "--verbose", action="store_true")
    #    p.set_defaults(func=func)
    #    subparsers[name] = p

    #for name in [ "init", "update", ]:
    #    subparsers[name].add_argument("source")
    #    subparsers[name].add_argument("output", type=pathlib.Path)

    options = parser.parse_args(args)
    options.error = p.error
    logging.basicConfig(level=logging.DEBUG if getattr(options, "verbose") else logging.INFO)
    return options
    

def init(igit, ogit, subdir, source):
    if not (igit.worktree / subdir).exists():
        raise RuntimeError("no subdir under git repo", subdir, source)
    
    # prepping the legacy tree

    log.debug("filtering repo paths")
    # filter existing commits
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
    ogit.run(["remote", "add", "legacy", igit.worktree])
    try:
        ogit.run(["fetch", "legacy", "master",])
        ogit.run(["checkout", "-B", "migrate", "--track", "legacy/master"])
        ogit.run(["rebase", "--committer-date-is-author-date", "master"])
    finally:
        ogit.run(["remote", "remove", "legacy"])


def main(options):
    log.debug("found system %s", platform.uname().system.lower())
    log.debug("git version [%s]", run(["git", "--version"]))

    filter_repo_version = run(["git", "filter-repo", "--version"], False, True)
    if not filter_repo_version:
        options.error("missing filter-repo git plugin"
                      " (https://github.com/newren/git-filter-repo)")
    log.debug("filter-repo [%s]", filter_repo_version)

    ogit = Git(worktree=options.output.resolve())
    log.debug("output client %s", ogit)
    if options.func == init and ogit.good():
        options.error(f"directory already initialized, {ogit}")

    source, subdir = options.source
    if not any(options.source):
        log.debug(f"getting source info from {ogit}")
        # detect from ogit the source
        txt = ogit.run(["config", "--local", "--get", "mono2repo.uri"])
        source, subdir = split_source(txt)

    log.debug("git repo source [%s]", source)
    log.debug("repo subdir [%s]", subdir)

    with tempdir() as tmpdir:
        igit = Git.clone(source, tmpdir / "legacy-repo")
        log.debug("input client %s", igit)

        if options.func.__name__ == "init":
            init(igit, ogit, subdir, source)
        else:
            update(igit, ogit, subdir)
    # finally we'll leave the configuration parameters for the update
    ogit.run(["config", "--local", "mono2repo.uri", source + "/" + subdir, ]) 
        

if __name__ == "__main__":
    main(parse_args())
