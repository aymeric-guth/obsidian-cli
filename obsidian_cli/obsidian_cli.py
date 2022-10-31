import sys
from typing import Optional
import pathlib
import os
import json
import pdb
import subprocess
import urllib.parse
import lsfiles
import time
import re


SUCCESS = 1
FAILURE = 0
URI_OPEN = "obsidian://open?vault={vault_id}&file={filename}"
URI_SEARCH = "obsidian://search?vault={vault_id}&query={query}"
USER_HOME = os.getenv("HOME")
if not USER_HOME:
    raise RuntimeError("can you please fuck off")
OBSIDIAN_DIR_DARWIN = f"{USER_HOME}/Library/Application Support/obsidian"
OBSIDIAN_DIR_LINUX = f"{USER_HOME}/.config/obsidian"

env: dict[str, pathlib.Path | str] = {}


def obsidian_encode(param: str, meta: str = "") -> str:
    return urllib.parse.quote(f"{meta}{param}")


def to_obsidian_root(path: pathlib.PurePath | pathlib.Path) -> str:
    global env

    return str(path)[len(str(env.get("OBSIDIAN_VAULT"))) :]  # type: ignore


def failure(msg: Optional[str] = None) -> int:
    if msg:
        sys.stdout.write(f"{msg}\n")
    return FAILURE


def success(msg: Optional[str] = None) -> int:
    if msg:
        sys.stdout.write(f"{msg}\n")
    return SUCCESS


def check_env_var(var: str) -> bool:
    global env

    env_var = s if (s := os.getenv(var)) else ""
    if not env_var:
        return False
    path = pathlib.Path(env_var)
    if not path.exists():
        return False
    env.update({var: path})
    return True


def check_env() -> int:
    # pdb.set_trace()
    global env

    if not check_env_var("OBSIDIAN_VAULT"):
        return failure("obsidian_vault not found")

    if not check_env_var("OBSIDIAN_DIR"):
        return failure("obsidian_vault not found")

    obsidian_dir: pathlib.Path = env.get("OBSIDIAN_DIR")  # type: ignore
    obsidian_cfg = obsidian_dir / "obsidian.json"
    if not obsidian_cfg.exists():
        return failure("obsidian_cfg not found")

    obsidian_cfg = json.loads(obsidian_cfg.read_text())
    vaults = obsidian_cfg.get("vaults")
    if vaults is None:
        return failure("no vaults are registred")

    for k, v in vaults.items():
        if v.get("path", "") == str(env.get("OBSIDIAN_VAULT")):
            env.update({"VAULT_ID": k})
            if not check_env_var("STACK_FILE"):
                env.update({"STACK_FILE": "3) Resources/Stack.md"})
            return success()

    return failure("vault is not active")


def parse_args(cmd: list[str]) -> int:
    global env

    files: list[pathlib.PurePath] = lsfiles.iterativeDFS(
        lambda x: (
            lsfiles.Maybe.unit(x)
            .bind(lsfiles.filters.dotfiles)
            .bind(
                lsfiles.filters.ext(
                    {
                        ".md",
                    }
                )
            )
        ),
        lsfiles.adapters.pathlib_purepath,
        env.get("OBSIDIAN_VAULT"),  # type: ignore
    )

    match cmd:
        case ["open" | "o"]:
            resource = env.get("OBSIDIAN_VAULT") / env.get("STACK_FILE")  # type: ignore
            if not resource.exists():
                return failure("resource could not be found on disk")
            uri = URI_OPEN.format(vault_id=env.get("VAULT_ID"), filename=obsidian_encode(env.get("STACK_FILE")))  # type: ignore
            subprocess.run(["open", uri])
            return success("open | o")

        case ["open" | "o", file]:
            pat = re.compile(file, re.IGNORECASE)
            files = [i for i in files if pat.search(i.name)]
            if not files:
                return failure(f"no match for: {file=}")
            uri = URI_OPEN.format(
                vault_id=env.get("VAULT_ID"),
                filename=obsidian_encode(to_obsidian_root(files[0])),
            )
            subprocess.run(["open", uri])
            return success(f"match for {file=} : {files=}")

        case ["find" | "f", query]:
            if "#" in query:
                uri = URI_SEARCH.format(
                    vault_id=env.get("VAULT_ID"),
                    query=obsidian_encode(meta="tag:", param=query),
                )
                subprocess.run(["open", uri])
                return success()

            else:
                return parse_args(["o", *cmd[1:]])

        case ["find" | "f"]:
            return failure("usage: find | f tag[/sub-tag] | filename")

        case _:
            return failure(f"unrecognised command: {cmd}")


def _main():
    global env

    if sys.platform == "darwin":
        os.environ["OBSIDIAN_DIR"] = OBSIDIAN_DIR_DARWIN
    elif sys.platform == "linux":
        os.environ["OBSIDIAN_DIR"] = OBSIDIAN_DIR_LINUX
    else:
        return failure("i've got bad news for you bud")

    if not check_env():
        return failure()

    res = subprocess.run(["pgrep", "Obsidian"], capture_output=True)
    if res.returncode:
        subprocess.run(
            [
                "open",
                "obsidian://open?vault={vault_id}".format(vault_id=env.get("VAULT_ID")),
            ]
        )
        c = 0
        while 1:
            print("polling obsidian process...")
            res = subprocess.run(["pgrep", "Obsidian"], capture_output=True)
            if res.returncode == 0:
                success(f"opened obsidian after {c} tries")
                break
            time.sleep(0.1)
            c += 1
            if c >= 10:
                return failure(f"could not open obsidian, tried {c} times")

    return parse_args(sys.argv[1:])


def main() -> int:
    return not _main()


if __name__ == "__main__":
    main()
