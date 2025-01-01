import contextlib
import shutil
import subprocess
from pathlib import Path
from typing import Any


def run(*args, output: bool=False, kwargs: dict|None=None) -> str:
    """run a cli command
    Examples:
        run("git", "--version", 1)
        run(["git", "--version", 1])
        run(["git", "--version", 1], output=True)
    """
    cmdline = [arg if isinstance(arg, (list, tuple)) else [str(arg)] for arg in args]
    cmdline = [str(key) for arg in cmdline for key in arg]
    kwargs = kwargs or {}
    if output:
        kwargs["encoding"] = "utf-8"
        return subprocess.check_output(cmdline, **kwargs)
    return subprocess.check_call(cmdline, **kwargs) or ""


@contextlib.contextmanager
def savefiles():
    pathlist: list[Path | str] = []

    def save(path: Path | str):
        nonlocal pathlist
        original = Path(path).expanduser().absolute()
        backup = original.parent / f"{original.name}.bak"
        if backup.exists():
            raise RuntimeError("backup file present", backup)
        shutil.copy(original, backup)
        pathlist.append(backup)
        return original

    try:
        yield save
    finally:
        for backup in pathlist:
            original = backup.with_suffix("")
            original.unlink()
            shutil.move(backup, original)


## GITHUB_DUMP

GITHUB_KEYS = {
    "run_number": int,  # "33"
    "sha": None,        # "f6322c108b976a9e0bdd6fa29c2adfa007e6dc86"
    "ref_name": None,   # "beta/0.1.0"
    "ref_type": None,   # "branch"
}


def github_dump_validate(gdata: dict[str, Any], keys: list[str] | None = None) -> dict[str, Any]:
    """validate the GITHUB json dioctionary

    Eg.
        validate_gdata(json.loads(os.getenv("GITHUB_DUMP")))

        In github workflow:
        env:
            GITHUB_DUMP: ${{ toJson(github) }}
    """
    result = {}
    missing = []
    keys = keys or GITHUB_KEYS
    for key in keys:
        if key not in gdata:
            missing.append(key)
        else:
            try:
                result[key] = GITHUB_KEYS[key](gdata[key]) if GITHUB_KEYS[key] else gdata[key]
            except:
                print("****", key, GITHUB_KEYS)
                raise
    if missing:
        raise RuntimeError(f"missing keys: {', '.join(missing)}")
    return result


def github_dump_from_local(ref_type: str = "branch") -> dict[str, str]:
    return {
        "run_number" : "0",
        "sha": run("git", "rev-parse", "HEAD", output=True).strip(),
        "ref_name": run("git", "branch", "--show-current", output=True).strip(),
        "ref_type": ref_type,
    }
