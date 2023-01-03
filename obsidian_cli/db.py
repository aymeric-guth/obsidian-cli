import os
import os.path
import sqlite3
import re
import pathlib

import lsfiles


conn = sqlite3.connect(":memory:")
# con = sqlite3.connect("db.sqlite")

conn.execute(
    """
DROP TABLE IF EXISTS link;
"""
)

conn.execute(
    """
DROP TABLE IF EXISTS file;
"""
)

conn.execute(
    """
CREATE TABLE file (
    id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
	name NVARCHAR(250)  NULL,
    extension NVARCHAR(250)  NULL,
	path NVARCHAR(250)  NULL
);
"""
)

conn.execute(
    """
CREATE TABLE link (
    parent_id INTEGER  NOT NULL,
    child_id INTEGER  NOT NULL,
    FOREIGN KEY(parent_id) REFERENCES file(id),
	FOREIGN KEY(child_id) REFERENCES file(id)
);
"""
)


def create_notes(conn, data: list[tuple[str, str, str]]) -> None:
    conn.executemany(
        """
    INSERT INTO file (name, extension, path)
    VALUES (?, ?, ?);
    """,
        data,
    )


def read_notes(conn) -> list[tuple[int, str, str, str]]:
    return conn.execute(
        """
    SELECT * FROM file WHERE extension = '.md';
    """
    ).fetchall()


def read_file(conn, name: str, ext: str, path: str) -> list[tuple[int, str, str, str]]:
    return conn.execute(
        """
    SELECT * FROM file WHERE name = ? AND extension = ? AND path = ?;
    """,
        [name, ext, path],
    ).fetchall()


def read_file_name(conn, name: str, ext: str) -> list[tuple[int, str, str, str]]:
    return conn.execute(
        """
    SELECT * FROM file WHERE name = ? AND extension = ?;
    """,
        [name, ext],
    ).fetchall()


def create_link(conn, parent_id: int, child_id: int):
    return conn.execute(
        """
        INSERT INTO link (parent_id, child_id)
        VALUES (?, ?);
        """,
        (parent_id, child_id),
    )


def read_links(conn):
    return conn.execute(
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

files = lsfiles.iterativeDFS(
    filters=lsfiles.filters.dotfiles,
    adapter=pathlib.PurePath,
    root=root,
)

# add all files to db
create_notes(
    conn,
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

dead_links = 0
# process all files
for _id, name, ext, path in read_notes(conn):
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

        rs = read_file_name(conn, lname, ".md")
        if len(rs) == 1:
            # unique file found with minimum info
            create_link(conn, parent_id=_id, child_id=rs[0][0])
            continue

        rs = read_file(conn, lname, ".md", lpath)
        if len(rs) == 1:
            # unique file found with name and relative path
            create_link(conn, parent_id=_id, child_id=rs[0][0])

        elif len(rs) == 0:
            # file not found
            # at this point all md are expected to be found
            f, e = os.path.splitext(lname)
            assert e != ".md", print(lname, lpath)

            rs = read_file_name(conn, f, e)
            if len(rs) == 1:
                # non md file found with minimum info
                create_link(conn, parent_id=_id, child_id=rs[0][0])
                continue

            rs = read_file(conn, f, e, lpath)
            if len(rs) == 1:
                # non md file found with name and relative path
                create_link(conn, parent_id=_id, child_id=rs[0][0])

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

cur = conn.execute(
    """
SELECT f.path, f.name, f.extension
FROM link AS l
FULL JOIN file AS f
ON l.child_id = f.id
WHERE l.child_id IS NULL
AND f.extension = '.md'
AND f.path NOT LIKE '%Archives%';
"""
)
orphaned_md_files = [i for i in cur]

cur = conn.execute(
    """
SELECT f.path, f.name, f.extension
FROM link AS l
FULL JOIN file AS f
ON l.child_id = f.id
WHERE l.child_id IS NULL
AND f.extension != '.md'
AND f.path NOT LIKE '%Archives%';
"""
)
orphaned_non_md_files = [i for i in cur]

total_md_files, *_ = conn.execute(
    """
SELECT count(*)
FROM file
WHERE extension = '.md';
"""
).fetchone()

total_non_md_files, *_ = conn.execute(
    """
SELECT count(*)
FROM file
WHERE extension != '.md';
"""
).fetchone()

rapport = [
    f"Total md files: {total_md_files}",
    f"Total non-md files: {total_non_md_files}",
    f"Dead links: {dead_links}",
    f"Orphaned md files: {len(orphaned_md_files)}",
    f"Orphaned non-md files: {len(orphaned_non_md_files)}",
]

print("\n".join(rapport))

conn.commit()
conn.close()
