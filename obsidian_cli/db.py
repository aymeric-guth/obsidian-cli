import os
import os.path
import sqlite3
import re
import pathlib
import yaml

import aiosql
import lsfiles
import utils

from dataclasses import dataclass


@dataclass
class Note:
    name: str
    path: str
    ext: str


# queries = aiosql.from_path(pathlib.Path(__file__).parent / "sql", "aiosqlite")
queries = aiosql.from_path(pathlib.Path(__file__).parent / "sql", "sqlite3")
print(pathlib.Path(__file__).parent)
conn = sqlite3.connect(":memory:")
# conn = sqlite3.connect("db.sqlite")

queries.link.drop_table(conn)
queries.tag.drop_table(conn)
queries.file_tag.drop_table(conn)
queries.file.drop_table(conn)

queries.file.create_table(conn)
queries.link.create_table(conn)
queries.tag.create_table(conn)
queries.file_tag.create_table(conn)


def create_tag(conn, value: str) -> int:
    rs = conn.execute(
        """
        SELECT id FROM tag WHERE name = ?;
                 """,
        (value,),
    ).fetchall()
    if rs:
        return rs[0][0]
    return conn.execute(
        """
        INSERT INTO tag (name) VALUES (?) RETURNING id;
        """,
        (value,),
    ).fetchall()[0][0]


def find_note_by_name(conn, name: str) -> list[Note]:
    rs = conn.execute(
        """
        SELECT name, path, extension
        FROM file
        WHERE name LIKE ?;
    """,
        (name,),
    ).fetchall()
    return [Note(*note) for note in rs]


wikilink = re.compile(r"(?:[\[]{2}([^\[]+)[\]]{2})")
# wikilink = re.compile(r"(?:[\[]{2}((?!\[).*)[\]]{2})")
mdlink = re.compile(r"(?:\[(.*)\])\((.*)\)")
modifiers = re.compile(r"[\#\|\^]{1,}")
pathlink = re.compile(r"/{1,}")
ignore_path = re.compile(r"(?:^.*imdone-tasks.*$)|(?:^\.)")
ignore_link = re.compile(r"(?:^400\sArchives.*$)|(?:^.*@Novall.*$)")

root = pathlib.Path(os.getenv("OBSIDIAN_VAULT"))
vault_prefix = len(str(root)) + 1

if not root.exists():
    # basic sanity check, might not be necessary
    raise Exception()

files = lsfiles.iterativeDFS(
    filters=lsfiles.filters.dotfiles,
    adapter=pathlib.PurePath,
    root=root,
)

# add all files to db
queries.file.create_many(
    conn,
    [
        {
            "name": f.name[: -(len(f.suffix))],
            "extension": f.suffix,
            "path": p if (p := str(f.parent)[vault_prefix:]) else ".",
        }
        for f in files
        if not ignore_path.match(str(f.parent))
    ],
)

dead_links = 0
# process all files
for _id, name, ext, path in queries.note.read_many(conn):
    # ignore files located at 400 Archives
    if ignore_link.match(path):
        continue
    # ignore non markdown files
    elif ext != ".md":
        continue
    # file loader
    md = root / path / f"{name}{ext}"
    raw = (lambda f: open(f).read())(md)
    # link parser
    matches = wikilink.findall(raw)
    links = [modifiers.split(m)[0] for m in matches]

    # link -> file resolver
    for link in links:
        components = pathlib.Path(link)
        lname = components.name
        lpath = str(components.parent)

        rs = queries.file.find_by_name_extension_path(
            conn, name=name, extension=ext, path=path
        )
        if len(rs) == 1:
            # unique file found with minimum info
            queries.link.create(conn, parent_id=_id, child_id=rs[0][0])
            continue

        rs = queries.note.find_by_name_path(conn, lname, lpath)
        if len(rs) == 1:
            # unique file found with name and relative path
            queries.link.create(conn, parent_id=_id, child_id=rs[0][0])

        elif len(rs) == 0:
            # file not found
            # at this point all md are expected to be found
            f, e = os.path.splitext(lname)
            assert e != ".md", print(lname, lpath)

            rs = queries.file.find_by_name_extension(conn, f, e)
            if len(rs) == 1:
                # non md file found with minimum info
                queries.link.create(conn, parent_id=_id, child_id=rs[0][0])
                continue

            queries.file.find_by_name_extension_path(
                conn, path=path, name=f, extension=e
            )
            if len(rs) == 1:
                # non md file found with name and relative path
                queries.link.create(conn, parent_id=_id, child_id=rs[0][0])

            elif len(rs) == 0:
                # dead link
                dead_links += 1

            elif len(rs) > 1:
                # multiple files found with name and relative path
                raise RuntimeError(
                    f"Unhandled case for: {_id=} {name=} {ext=} {path=} {lname=} {lpath=}"
                )
        else:
            # multiple files found with name and relative path
            raise RuntimeError(
                f"Unhandled case for: {_id=} {name=} {ext=} {path=} {lname=} {lpath=}"
            )

    # YAML tag parser
    tags = (
        lambda data: (
            utils.default_exc(yaml.load, {})(m.group(1), yaml.CLoader)  # type: ignore
            if (
                m := re.compile(r"^[-]{3}([a-zA-Z0-9-_#:\s\n/]{1,})[-]{3}").search(data)
            )
            else {}
        )
    )(raw)

    for tag in tags.get("tags", []):
        tag_id = create_tag(conn, tag)
        queries.file_tag.create(conn, file_id=_id, tag_id=tag_id)
