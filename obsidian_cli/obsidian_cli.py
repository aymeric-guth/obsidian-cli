import os
import os.path
import sys
import pathlib
import os
import json
import subprocess
import time
import re
import pathlib
import yaml
import ipdb

from utils import cli, default_exc
import lsfiles

from . import repo


# URI_OPEN = "obsidian://open?vault={vault_id}&file={filename}"
URI_OPEN = "obsidian://advanced-uri?vault={vault_id}&filename={filename}&openmode=tab"
URI_SEARCH = "obsidian://search?vault={vault_id}&query={query}"
USER_HOME = os.getenv("HOME")
if not USER_HOME:
    raise RuntimeError("can you kindly fuck off, sir")
OBSIDIAN_DIR_DARWIN = f"{USER_HOME}/Library/Application Support/obsidian"
OBSIDIAN_DIR_LINUX = f"{USER_HOME}/snap/obsidian/current/.config/obsidian"
open_cmd = [
    "open",
]


def check_env() -> tuple[str, int]:
    (msg, defined) = cli.env.query("OBSIDIAN_DIR")
    if sys.platform == "darwin" and not defined:
        cli.env.set("OBSIDIAN_DIR", OBSIDIAN_DIR_DARWIN)
        open_cmd.append("--background")
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

        case ["open" | "o", file] if file is not None and "/" in file:
            import urllib.parse

            uri = URI_OPEN.format(
                vault_id=cli.env.get("VAULT_ID"), filename=urllib.parse.quote(file)
            )

            subprocess.run([*open_cmd, uri])
            return cli.success()

        case ["open" | "o", file]:
            rs = repo.note.find_by_name(file)
            if not rs:
                return cli.failure(f"{file=} not found")
            uri = URI_OPEN.format(
                vault_id=cli.env.get("VAULT_ID"),
                filename=rs[0].to_obsidian(),
            )
            subprocess.run([*open_cmd, uri])
            return cli.success()

        case ["match" | "m", "file" | "f", name]:
            # find file matching filename -> list[Note]
            for note in repo.note.find_by_name(name):
                sys.stdout.write(f"{note!s}\n")
            return cli.success()

        case ["list" | "l", "tags" | "t"]:
            # find all tags
            for tag in repo.tag.read_all():
                sys.stdout.write(tag + "\n")
            return cli.success()

        case ["list" | "l", "links" | "l", target]:
            # resolve links in target file
            raise NotImplementedError

        case ["list", "dirs"]:
            # list directory tree structure ~lsd --tree
            for path in repo.file.read_all_path():
                p = path.split("/")
                print("    " * (len(p) - 1) + p[-1])
            return cli.success()

        case ["find" | "f", "files" | "f", tag]:
            # find file containing {tag}
            for note in repo.file_tag.find_file_by_tag(tag):
                sys.stdout.write(f"{note!s}\n")
            return cli.success()

        case ["find" | "f", "tags" | "t", file]:
            # find tags in {file}
            notes = repo.note.find_by_name(file)
            if not notes:
                return cli.failure(f"{file=} not found")
            elif len(notes) > 1:
                return cli.failure(f"found multiple matching files, use FQDN")
            note = notes[0]
            tags = repo.file_tag.find_tag_by_filename(note.name)
            if not tags:
                cli.failure(f"{file=} has no tags")
            for tag in tags:
                sys.stdout.write(tag + "\n")
            return cli.success()

        case ["find" | "f", "links" | "l", file]:
            # find file(s) containing link pattern -> list[Note]
            notes = repo.link.find_file_by_link(file)
            if not notes:
                return cli.failure(f"{file=} not found")
            for note in notes:
                sys.stdout.write(f"{note!s}\n")
            return cli.success()

        case ["find" | "f", "orphaned" | "o", dir]:
            # find orphaned files (files that are not linked)
            if not dir:
                notes = repo.link.find_orphaned()
            else:
                notes = repo.link.find_orphaned_dir(dir)
            if not notes:
                return cli.failure("No orphaned files found")
            for note in notes:
                sys.stdout.write(f"{note!s}\n")
            return cli.success()

        case ["init"]:
            init_db()
            return cli.success()

        case _:
            return cli.failure(f"unrecognised command: {cmd}")


def init_db():
    wikilink = re.compile(r"(?:[\[]{2}([^\[]+)[\]]{2})")
    mdlink = re.compile(r"(?:\[(.*)\])\((.*)\)")
    modifiers = re.compile(r"[\#\|\^]{1,}")
    pathlink = re.compile(r"/{1,}")
    ignore_path = re.compile(r"(?:^.*imdone-tasks.*$)|(?:^\.)")
    ignore_link = re.compile(r"(?:^400\sArchives.*$)|(?:^.*@Novall.*$)")
    yaml_tag = re.compile(r"^[-]{3}([a-zA-Z0-9-_#:\s\n/]{1,})[-]{3}")
    root = cli.env.get("OBSIDIAN_VAULT")
    vault_prefix = len(str(root)) + 1

    files = lsfiles.iterativeDFS(
        filters=lsfiles.filters.dotfiles,
        adapter=pathlib.PurePath,
        root=root,  # type: ignore
    )

    repo.init()
    # add all files to db
    repo.file.create_many(
        [
            (
                p if (p := str(f.parent)[vault_prefix:]) else ".",
                f.name[: -(len(f.suffix))],
                f.suffix,
            )
            for f in files
            if not ignore_path.match(str(f.parent))
        ],
    )

    dead_links = 0
    # process all files
    for note in repo.note.read_all():
        # ignore files located at 400 Archives
        if ignore_link.match(note.path):
            continue
        # file loader
        raw = (lambda f: open(f).read())(note.to_md())
        # link parser
        matches = wikilink.findall(raw)
        links = [modifiers.split(m)[0] for m in matches]

        # link -> file resolver
        for l in links:
            components = pathlib.Path(l)
            lname = components.name
            lpath = str(components.parent)

            note_id = repo.note.find_by_name_path(name=lname, path=lpath)
            if note_id is not None:
                # unique file found with minimum info
                repo.link.create_one(parent_id=note.id, child_id=note_id)
                continue

            rs = repo.note.find_by_name(name=lname)
            if len(rs) == 1:
                # unique file found with name and relative path
                repo.link.create_one(parent_id=note.id, child_id=rs[0].id)

            elif len(rs) == 0:
                # file not found
                # at this point all md are expected to be found
                f, e = os.path.splitext(lname)
                assert e != ".md", print(lname, lpath)

                rs = repo.file.find_by_name_extension(name=f, extension=e)
                if len(rs) == 1:
                    # non md file found with minimum info
                    repo.link.create_one(parent_id=note.id, child_id=rs[0])
                    continue

                rs = repo.file.find_by_name_extension_path(
                    name=f, extension=e, path=lpath
                )
                if rs is not None:
                    # non md file found with name and relative path
                    repo.link.create_one(parent_id=note.id, child_id=rs)
                else:
                    # dead link
                    dead_links += 1
            else:
                # multiple files found with name and relative path
                raise RuntimeError(f"Unhandled case for: {note=} {lname=} {lpath=}")

        # YAML tag parser
        tags = (
            lambda data: (
                default_exc(yaml.load, {})(m.group(1), yaml.CLoader)  # type: ignore
                if (m := yaml_tag.search(data))
                else {}
            )
        )(raw)

        for tag in tags.get("tags", []):
            if not tag:
                continue
            repo.file_tag.create_one(note.id, repo.tag.create_one(tag))


def _main(*args) -> tuple[str, int]:
    """
    main function
    """
    (msg, ok) = check_env()
    if not ok:
        print("check_env failed")
        return cli.failure(msg)

    # init_db()
    _env = os.environ.copy()
    if sys.platform == "darwin":
        process = "Obsidian"
    elif sys.platform == "linux":
        _env.update({"LD_PRELOAD": _env["TOOLDIR"] + "/lib/h4ckz/libwlhack.so"})
        process = "obsidian"

    cmd = [
        *open_cmd,
        "obsidian://open?vault={vault_id}".format(vault_id=cli.env.get("VAULT_ID")),
    ]
    res = subprocess.run(["pgrep", process], capture_output=True)

    if res.returncode == 0:
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

    return parse_args(*args)


def main() -> int:
    rv = cli.py_fnc(_main)(sys.argv[1:])
    repo.conn.commit()
    repo.conn.close()
    return rv
