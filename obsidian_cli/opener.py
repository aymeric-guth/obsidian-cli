import sys
import pathlib
import os
import json
import subprocess
import urllib.parse
import time

from utils import cli, default_exc

from ._types import Note
from .core import note, tag, file_tag, tag, file, link


URI_OPEN = "obsidian://open?vault={vault_id}&file={filename}"
URI_SEARCH = "obsidian://search?vault={vault_id}&query={query}"
USER_HOME = os.getenv("HOME")
if not USER_HOME:
    raise RuntimeError("can you kindly fuck off, sir")
OBSIDIAN_DIR_DARWIN = f"{USER_HOME}/Library/Application Support/obsidian"
# OBSIDIAN_DIR_LINUX = f"{USER_HOME}/.config/obsidian"
OBSIDIAN_DIR_LINUX = f"{USER_HOME}/snap/obsidian/current/.config/obsidian"


def obsidian_encode(param: str, meta: str = "") -> str:
    return urllib.parse.quote(f"{meta}{param}")


def to_obsidian_root(path: pathlib.PurePath | pathlib.Path) -> str:
    return str(path)[len(str(cli.env.get("OBSIDIAN_VAULT"))) :]


def check_env() -> tuple[str, int]:
    (msg, defined) = cli.env.query("OBSIDIAN_DIR")
    if sys.platform == "darwin" and not defined:
        cli.env.set("OBSIDIAN_DIR", OBSIDIAN_DIR_DARWIN)
    elif sys.platform == "linux" and not defined:
        cli.env.set("OBSIDIAN_DIR", OBSIDIAN_DIR_LINUX)
    else:
        return cli.failure("i've got bad news for you bud")

    # var defined ?
    # no -> return error
    # yes -> next step
    (msg, defined) = cli.env.query("OBSIDIAN_VAULT")
    if not defined:
        return cli.failure(msg)

    obsidian_dir = pathlib.Path(cli.env.get("OBSIDIAN_DIR"))
    obsidian_cfg = obsidian_dir / "obsidian.json"
    if not obsidian_cfg.exists():
        return cli.failure(f"{obsidian_cfg=} not found")

    obsidian_cfg = default_exc(json.loads, {})(obsidian_cfg.read_text())
    if not obsidian_cfg:
        return cli.failure(f"{obsidian_cfg=} is invalid")
    vaults = obsidian_cfg.get("vaults", None)
    if vaults is None:
        return cli.failure("no vaults are registred")

    (msg, defined) = cli.env.query("STACK_FILE")
    if not defined:
        cli.env.set("STACK_FILE", "Stack")

    for k, v in vaults.items():
        if v.get("path", "") == cli.env.get("OBSIDIAN_VAULT"):
            cli.env.set("VAULT_ID", k)
            return cli.success()

    return cli.failure("vault is not active")


def parse_args(cmd: list[str]) -> tuple[str, int]:
    match cmd:
        case []:
            return cli.success()

        case ["open" | "o"]:
            return parse_args(["open", cli.env.get("STACK_FILE")])

        case ["open" | "o", file]:
            rs = queries.note.find_by_name(conn, file)
            if not rs:
                return cli.failure(f"{file=} not found")
            elif len(rs) > 1:
                rs = rs[0]
            uri = URI_OPEN.format(
                vault_id=cli.env.get("VAULT_ID"),
                filename=obsidian_encode(f"{rs[0]}/{rs[1]}{rs[2]}"),
            )
            subprocess.run(["open", uri])
            return cli.success()

        case ["match" | "m"]:
            return cli.failure("match | m")
            # [
            #    t
            #    for f in files
            #    if (t := catcher(tag_parser)(lambda f: lambda: open(f).read())(f))
            #    is not None
            # ]

        case ["list" | "l", "tags" | "t"]:
            # find all tags
            for tag, *_ in queries.tag.read_all(conn):
                sys.stdout.write(tag + "\n")
            return cli.success()

        case ["find" | "f", "file" | "f", tag]:
            # find file containing {tag}
            for p, f, e in queries.file_tag.find_file_by_tag(conn, tag):
                sys.stdout.write(f"{p}/{f}{e}\n")
            return cli.failure()

        case ["find" | "f", "tag" | "t", file]:
            # find tags in {file}
            notes = [Note(*note) for note in queries.note.find_by_name(conn, file)]
            if not notes:
                return cli.failure(f"{file=} not found")
            elif len(notes) > 1:
                return cli.failure(f"found multiple matching files, use FQDN")
            note = notes[0]
            tags = queries.file_tag.find_tag_by_filename(conn, note.name)
            if not tags:
                cli.failure(f"{file=} has no tags")
            for tag in tags:
                sys.stdout.write(tag + "\n")
            return cli.success()

        case _:
            return cli.failure(f"unrecognised command: {cmd}")


# find file matching filename -> list[Note]
# find file containing link pattern -> list[Note]
# find orphaned files (files that are not linked)
# find backlink for target file (reference to target file in whole database)

# file, every non-md file
# path, name, ext
# note, md file
# path, name

# link
# relation note -> file | note

# tag
# name

# tag_file
# note -> tag


def main(*args) -> tuple[str, int]:
    """
    main function
    """
    (msg, ok) = check_env()
    if not ok:
        print("check_env failed")
        return cli.failure(msg)

    _env = os.environ.copy()
    if sys.platform == "darwin":
        cmd = [
            "open",
            "obsidian://open?vault={vault_id}".format(vault_id=cli.env.get("VAULT_ID")),
        ]
        process = "Obsidian"
    elif sys.platform == "linux":
        cmd = [
            "open",
            "obsidian://open?vault={vault_id}".format(vault_id=cli.env.get("VAULT_ID")),
        ]
        _env.update({"LD_PRELOAD": _env["TOOLDIR"] + "/lib/h4ckz/libwlhack.so"})
        process = "obsidian"

    res = subprocess.run(["pgrep", process], capture_output=True)
    # possibilite d'alterer le comportement de l'utilitaire
    # dans l'etat ne fait pas passer obsidian au premier plan
    if res.returncode == 0:
        # return cli.success("obsidian process is up")
        return parse_args(*args)
    subprocess.run(
        cmd,
        env=_env,
    )
    c = 0
    delay = 0.2
    while 1:
        print("polling obsidian process...")
        res = subprocess.run(["pgrep", process], capture_output=True)
        if res.returncode == 0:
            break
        time.sleep(delay)
        delay *= 2
        c += 1
        if c >= 10:
            return cli.failure(f"could not open obsidian, tried {c} times")

    # return cli.success()
    return parse_args(*args)
    # return cli.success(f"opened obsidian after {c} tries")


def _main() -> int:
    return cli.py_fnc(main)(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(_main())
