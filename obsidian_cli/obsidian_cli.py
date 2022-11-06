import sys
from typing import Optional, Any, Callable
import pathlib
import os
import json
import pdb
import subprocess
import urllib.parse
import lsfiles
import time
import re
from collections import defaultdict

import utils
from utils import cli
from rich.console import Console
from rich.table import Table

from .core import tag_parser


URI_OPEN = "obsidian://open?vault={vault_id}&file={filename}"
URI_SEARCH = "obsidian://search?vault={vault_id}&query={query}"
USER_HOME = os.getenv("HOME")
if not USER_HOME:
    raise RuntimeError("can you kindly fuck off, sir")
OBSIDIAN_DIR_DARWIN = f"{USER_HOME}/Library/Application Support/obsidian"
OBSIDIAN_DIR_LINUX = f"{USER_HOME}/.config/obsidian"


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

    # pdb.set_trace()

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

    obsidian_cfg = utils.default_exc(json.loads, {})(obsidian_cfg.read_text())
    if not obsidian_cfg:
        return cli.failure(f"{obsidian_cfg=} is invalid")
    vaults = obsidian_cfg.get("vaults", None)
    if vaults is None:
        return cli.failure("no vaults are registred")

    (msg, defined) = cli.env.query("STACK_FILE")
    if not defined:
        cli.env.set("STACK_FILE", "300 Resources/Stack.md")

    for k, v in vaults.items():
        if v.get("path", "") == cli.env.get("OBSIDIAN_VAULT"):
            cli.env.set("VAULT_ID", k)
            return cli.success()

    return cli.failure("vault is not active")


def obsidian_files() -> list[pathlib.PurePath]:
    return lsfiles.iterativeDFS(
        filters=lsfiles.filters.ext(
            {
                ".md",
            }
        ),
        adapter=pathlib.PurePath,
        root=pathlib.Path(cli.env.get("OBSIDIAN_VAULT")),
    )


def tag_finder(msg: str) -> tuple[str, int]:
    def catcher(fnc):
        def inner(*args, **kwargs):
            try:
                return fnc(*args, **kwargs).get("tags")
            except Exception as err:
                raise RuntimeError(err, *args, **kwargs)

        return inner

    # pdb.set_trace()
    res = (
        t
        for f in obsidian_files()
        if (t := (catcher(tag_parser)((lambda f: lambda: open(f).read())(f))))
        is not None
    )

    d = defaultdict(int)
    table = Table(title="tags and occurrences")
    table.add_column("#", justify="left", style="cyan", no_wrap=True)
    table.add_column("tags", justify="left", style="magenta")

    for y in res:
        for x in y:
            d[x] += 1

    if sys.stdout.isatty():
        [
            table.add_row(str(v), k)
            for k, v in sorted(
                [(k, v) for k, v in d.items()], key=lambda item: item[1], reverse=True
            )
        ]
        console = Console()
        console.print(table)
        return cli.success()
    return cli.success("\n".join([k for k, v in d.items()]))


def parse_args(cmd: list[str]) -> tuple[str, int]:
    files: list[pathlib.PurePath] = lsfiles.iterativeDFS(
        filters=lsfiles.filters.ext(
            {
                ".md",
            }
        ),
        adapter=pathlib.PurePath,
        root=pathlib.Path(cli.env.get("OBSIDIAN_VAULT")),
    )

    match cmd:
        case []:
            return cli.success()

        case ["open" | "o"]:
            resource = pathlib.Path(cli.env.get("OBSIDIAN_VAULT")) / cli.env.get(
                "STACK_FILE"
            )
            if not resource.exists():
                return cli.failure(f"{resource=} could not be found on disk")
            uri = URI_OPEN.format(
                vault_id=cli.env.get("VAULT_ID"),
                filename=obsidian_encode(cli.env.get("STACK_FILE")),
            )
            subprocess.run(["open", uri])
            return cli.success("open | o")

        case ["open" | "o", file]:
            pat = re.compile(file, re.IGNORECASE)
            f = [i for i in files if pat.search(i.name)]
            if not f:
                return cli.failure(f"no match for: {file=}")
            uri = URI_OPEN.format(
                vault_id=cli.env.get("VAULT_ID"),
                filename=obsidian_encode(to_obsidian_root(files[0])),
            )
            subprocess.run(["open", uri])
            return cli.success(f"match for {file=} : {files=}")

        case ["find" | "f", query]:
            if "#" in query:
                uri = URI_SEARCH.format(
                    vault_id=cli.env.get("VAULT_ID"),
                    query=obsidian_encode(meta="tag:", param=query),
                )
                subprocess.run(["open", uri])
                return cli.success()

            else:
                return parse_args(["o", *cmd[1:]])

        case ["match" | "m"]:
            return cli.failure()
            # [
            #    t
            #    for f in files
            #    if (t := catcher(tag_parser)(lambda f: lambda: open(f).read())(f))
            #    is not None
            # ]

        case ["find" | "f"]:
            return cli.failure("usage: find | f tag[/sub-tag] | filename")

        case _:
            return cli.failure(f"unrecognised command: {cmd}")


def main(*args) -> tuple[str, int]:
    """
    main function
    """
    (msg, ok) = check_env()
    if not ok:
        return cli.failure(msg)

    res = subprocess.run(["pgrep", "Obsidian"], capture_output=True)
    if res.returncode:
        subprocess.run(
            [
                "open",
                "obsidian://open?vault={vault_id}".format(
                    vault_id=cli.env.get("VAULT_ID")
                ),
            ]
        )
        c = 0
        while 1:
            print("polling obsidian process...")
            res = subprocess.run(["pgrep", "Obsidian"], capture_output=True)
            if res.returncode == 0:
                cli.success(f"opened obsidian after {c} tries")
                break
            time.sleep(0.2)
            c += 1
            if c >= 10:
                return cli.failure(f"could not open obsidian, tried {c} times")

    return parse_args(*args)


def _main() -> int:
    return cli.sh_fnc(main)(sys.argv[1:])


def _tag_finder() -> int:
    (msg, ok) = check_env()
    if not ok:
        return cli.sh_fnc(cli.failure)(msg)
    return cli.sh_fnc(tag_finder)("")
