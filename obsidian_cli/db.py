import os
import os.path
import sqlite3
import re
import collections
import pathlib

import lsfiles


# con = sqlite3.connect(":memory:")
con = sqlite3.connect("db.sqlite")

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
ignore_path = re.compile(r"(?:^.*imdone-tasks.*$)|(?:^\.)")
ignore_link = re.compile(r"(?:^400\sArchives.*$)|(?:^.*@Novall.*$)")

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

# add all files to db
create_notes(
    cur,
    [
        (
            f.name[: -(len(f.suffix))],
            f.suffix,
            p if (p := str(f.parent)[vault_prefix:]) else ".",
        )
        for f in files
        if not ignore_path.match(str(f.parent))
    ],
)

count = 0
# process all files
for _id, name, ext, path in read_notes(cur):
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

        rs = read_file_name(cur, lname, ".md")
        if len(rs) == 1:
            # unique file found with minimum info
            create_link(cur, parent_id=_id, child_id=rs[0][0])
            continue

        rs = read_file(cur, lname, ".md", lpath)
        if len(rs) == 1:
            # unique file found with name and relative path
            create_link(cur, parent_id=_id, child_id=rs[0][0])

        elif len(rs) == 0:
            # file not found
            # at this point all md are expected to be found
            f, e = os.path.splitext(lname)
            assert e != ".md", print(lname, lpath)

            rs = read_file_name(cur, f, e)
            if len(rs) == 1:
                # non md file found with minimum info
                create_link(cur, parent_id=_id, child_id=rs[0][0])
                continue

            rs = read_file(cur, f, e, lpath)
            if len(rs) == 1:
                # non md file found with name and relative path
                create_link(cur, parent_id=_id, child_id=rs[0][0])

            elif len(rs) == 0:
                # dead link
                count += 1

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

print(f"Dead links: {count}")
print(len(read_links(cur)))

rows = cur.execute(
    """
SELECT p.path, p.name, p.extension, c.path, c.name, c.extension
FROM link
JOIN file AS p
ON link.parent_id = p.id
JOIN file AS c
ON link.child_id = c.id
ORDER BY p.path, p.name, p.extension;
"""
).fetchall()
for i in rows:
    pp, pn, pe, cp, cn, ce = i
    print(f"{pp}/{pn}{pe} -> {cp}/{cn}{ce}")

con.commit()
cur.close()
con.close()

# feature orphaned file (does not appear in a link)
