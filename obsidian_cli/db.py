import os
import os.path
import sqlite3
import re
import collections
import pathlib

import lsfiles


# con = sqlite3.connect(":memory:")
con = sqlite3.connect("db.db")
cur = con.cursor()

cur.execute(
    """
CREATE TABLE file (
    id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
	name NVARCHAR(250)  NULL,
    extension NVARCHAR(250)  NULL,
	path NVARCHAR(250)  NULL
);
"""
)

cur.execute(
    """
CREATE TABLE link (
    parent_id INTEGER  NOT NULL,
    child_id INTEGER  NOT NULL,
    FOREIGN KEY(parent_id) REFERENCES file(id),
	FOREIGN KEY(child_id) REFERENCES file(id)
);
"""
)


def create_note(cur, data: tuple[str, str, str]) -> None:
    cur.execute(
        """
    INSERT INTO file (name, extension, path)
    VALUES (?, ?, ?);
    """,
        data,
    )


def create_notes(cur, data: list[tuple[str, str, str]]) -> None:
    cur.executemany(
        """
    INSERT INTO file (name, extension, path)
    VALUES (?, ?, ?);
    """,
        data,
    )


def read_notes(cur) -> list[tuple[int, str, str, str]]:
    return cur.execute(
        """
    SELECT * FROM file WHERE extension = '.md';
    """
    ).fetchall()


def read_file(cur, name: str, ext: str, path: str) -> list[tuple[int, str, str, str]]:
    return cur.execute(
        """
    SELECT * FROM file WHERE name = ? AND extension = ? AND path = ?;
    """,
        [name, ext, path],
    ).fetchall()


def read_file_name(cur, name: str, ext: str) -> list[tuple[int, str, str, str]]:
    return cur.execute(
        """
    SELECT * FROM file WHERE name = ? AND extension = ?;
    """,
        [name, ext],
    ).fetchall()


def create_link(cur, parent_id: int, child_id: int):
    return cur.execute(
        """
        INSERT INTO link (parent_id, child_id)
        VALUES (?, ?);
        """,
        (parent_id, child_id),
    )


def read_links(cur):
    return cur.execute(
        """
        SELECT * FROM link;
        """
    ).fetchall()


wikilink = re.compile(r"(?:[\[]{2}([^\[]+)[\]]{2})")
# wikilink = re.compile(r"(?:[\[]{2}((?!\[).*)[\]]{2})")
mdlink = re.compile(r"(?:\[(.*)\])\((.*)\)")
modifiers = re.compile(r"[\#\|\^]{1,}")
pathlink = re.compile(r"/{1,}")

root = pathlib.Path(os.getenv("OBSIDIAN_VAULT"))
vault_prefix = len(str(root)) + 1

if not root.exists():
    # basic sanity check, might not be necessary
    raise Exception()

_registry: dict[str, list[str]] = collections.defaultdict(list)
files = lsfiles.iterativeDFS(
    filters=lsfiles.filters.dotfiles,
    adapter=pathlib.PurePath,
    root=root,
)

create_notes(
    cur,
    [
        (
            f.name[: -(len(f.suffix))],
            f.suffix,
            p if (p := str(f.parent)[vault_prefix:]) else ".",
        )
        for f in files
    ],
)

count = 0
for _id, name, ext, path in read_notes(cur):
    md = root / path / f"{name}{ext}"
    raw = (lambda f: open(f).read())(md)
    matches = wikilink.findall(raw)
    links = [modifiers.split(m)[0] for m in matches]

    for l in links:
        components = pathlib.Path(l)
        lname = components.name
        lpath = str(components.parent)

        rs = read_file(cur, lname, ".md", lpath)
        if len(rs) == 1:
            create_link(cur, parent_id=_id, child_id=rs[0][0])
            continue
        rs = read_file_name(cur, lname, ".md")
        if len(rs) == 1:
            create_link(cur, parent_id=_id, child_id=rs[0][0])
        elif len(rs) > 1:
            ...
        #            raise RuntimeError(
        #                f"Unhandled case for: {_id=} {name=} {ext=} {path=} {lname=} {lpath=}"
        #            )
        else:
            f, e = os.path.splitext(lname)
            rs = read_file(cur, f, e, lpath)
            if len(rs) == 1:
                create_link(cur, parent_id=_id, child_id=rs[0][0])
            rs = read_file_name(cur, f, e)
            if len(rs) == 1:
                create_link(cur, parent_id=_id, child_id=rs[0][0])
            elif len(rs) > 1:
                ...
            #                raise RuntimeError(
            #                    f"Unhandled case for: {_id=} {name=} {ext=} {path=} {lname=} {lpath=}"
            #                )
            else:
                print(f"{lname=} {lpath=}")
                count += 1
                # log point for dead link
                ...

# for i in read_notes(cur):
#     print(i)
for i in read_links(cur):
    print(i)
con.commit()
cur.close()
con.close()

# for i in result[State.NON_MD_FILE_NOT_FOUND]:
#     print(i)
