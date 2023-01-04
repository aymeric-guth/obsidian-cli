import dataclasses
import os
import os.path
import sqlite3
import re
import pathlib
import yaml

import lsfiles
import utils

from dataclasses import dataclass


@dataclass
class Note:
    name: str
    path: str
    ext: str


conn = sqlite3.connect(":memory:")
# conn = sqlite3.connect("db.sqlite")

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
CREATE TABLE tag (
    id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
	value NVARCHAR(250)  NULL
);
"""
)

conn.execute(
    """
CREATE VIRTUAL TABLE filesearch USING fts5(
    id,
    name,
    extension,
	path
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

conn.execute(
    """
CREATE TABLE file_tag (
    file_id INTEGER  NOT NULL,
    tag_id INTEGER  NOT NULL,
    PRIMARY KEY (file_id, tag_id),
    FOREIGN KEY(file_id) REFERENCES file(id),
	FOREIGN KEY(tag_id) REFERENCES tag(id)
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


def get_file_by_filename(conn, filename: str):
    return conn.execute(
        """
    SELECT path, name, extension FROM file WHERE name LIKE ? AND extension = '.md';
    """,
        [
            filename,
        ],
    ).fetchone()


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


def create_tag(conn, value: str) -> int:
    rs = conn.execute(
        """
        SELECT id FROM tag WHERE value = ?;
                 """,
        (value,),
    ).fetchall()
    if rs:
        return rs[0][0]
    return conn.execute(
        """
        INSERT INTO tag (value) VALUES (?) RETURNING id;
        """,
        (value,),
    ).fetchall()[0][0]


def read_tag(conn, value: str) -> int:
    rs = conn.execute(
        """
        SELECT id FROM tag WHERE value = ?;
                 """,
        (value,),
    ).fetchall()
    if rs:
        return rs[0][0]
    raise RuntimeError(f"Tag({value}) not found")


def create_file_tag(conn, file_id: int, tag_id: int) -> None:
    conn.execute(
        """
        INSERT INTO file_tag (file_id, tag_id) VALUES (?, ?);
    """,
        (file_id, tag_id),
    )


def find_tags_from_filename(conn, filename: str) -> list[str]:
    rs = conn.execute(
        """
        SELECT t.value
        FROM tag AS t
        JOIN file_tag AS ft
        ON t.id = ft.tag_id
        JOIN file AS f
        ON ft.file_id = f.id
        WHERE f.name LIKE ?
        ORDER BY t.value;
    """,
        (filename,),
    ).fetchall()
    return [tag for tag, *_ in rs]


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


# select all files containing tags and their relative tags
cur = conn.execute(
    """
SELECT f.name, t.value
FROM tag AS t
JOIN file_tag AS ft
ON t.id = ft.tag_id
JOIN file AS f
ON ft.file_id = f.id
ORDER BY f.name;
"""
)


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
        create_file_tag(conn, _id, tag_id)


# select all files containing tags and their relative tags
cur = conn.execute(
    """
SELECT f.name, t.value
FROM tag AS t
JOIN file_tag AS ft
ON t.id = ft.tag_id
JOIN file AS f
ON ft.file_id = f.id
ORDER BY f.name;
"""
)

# select all MD files without a reference to them
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

# select all non-MD files without a reference to them
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

total_tags, *_ = conn.execute(
    """
SELECT count(*)
FROM tag;
"""
).fetchone()

# select all files without tags
md_files_without_tag, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
FULL JOIN file_tag AS ft
ON f.id = ft.file_id
WHERE ft.tag_id IS NULL
AND f.extension = '.md'
AND f.path NOT LIKE '%Archives%';
"""
).fetchone()

# select all files at zettelkasten root
md_files_zk_root, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension = '.md'
AND f.path = '001 Zettelkasten';
"""
).fetchone()
non_md_files_zk_root, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension != '.md'
AND f.path = '001 Zettelkasten';
"""
).fetchone()
md_files_in_zk, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension = '.md'
AND f.path LIKE '001 Zettelkasten%';
"""
).fetchone()
non_md_files_in_zk, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension != '.md'
AND f.path LIKE '001 Zettelkasten%';
"""
).fetchone()

# select all files at attachment root
non_md_files_attachment_root, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension != '.md'
AND f.path = '000 Attachments';
"""
).fetchone()
md_files_attachment_root, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension = '.md'
AND f.path = '000 Attachments';
"""
).fetchone()
non_md_files_in_attachment, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension != '.md'
AND f.path LIKE '000 Attachments%';
"""
).fetchone()
md_files_in_attachment, *_ = conn.execute(
    """
SELECT COUNT(*)
FROM file AS f
WHERE f.extension = '.md'
AND f.path LIKE '000 Attachments%';
"""
).fetchone()


rapport = [
    f"Total MD files: {total_md_files}",
    f"Total non-MD files: {total_non_md_files}",
    f"Dead links: {dead_links}",
    f"Orphaned MD files: {len(orphaned_md_files)}",
    f"Orphaned non-MD files: {len(orphaned_non_md_files)}",
    f"Total tags: {total_tags}",
    f"MD files without tag: {md_files_without_tag}",
    f"MD files at Zettelkasten root: {md_files_zk_root}",
    f"non-MD files at Zettelkasten root: {non_md_files_zk_root}",
    f"MD files at Attachments root: {md_files_attachment_root}",
    f"Non-MD files at Attachments root: {non_md_files_attachment_root}",
    f"MD files in Attachments: {md_files_in_attachment}",
    f"Non-MD files in Attachments: {non_md_files_in_attachment}",
    f"MD files in Zettelkasten: {md_files_in_zk}",
    f"Non-MD files in Zettelkasten: {non_md_files_in_zk}",
]


def list_tags(conn) -> list[str]:
    rs = conn.execute(
        """
    SELECT t.value
    FROM tag AS t
    ORDER BY t.value DESC;
    """
    ).fetchall()
    res = []
    for tag, *_ in rs:
        res.append(tag)
    return res


def list_files_containing_tag(conn, tag: str):
    return conn.execute(
        """
    SELECT f.path, f.name, f.extension
    FROM file AS f
    JOIN file_tag AS ft
    ON f.id = ft.file_id
    JOIN tag AS t
    ON ft.tag_id = t.id
    WHERE t.value = ?
    ORDER BY t.value DESC;
    """,
        (tag,),
    ).fetchall()


# print("\n".join(rapport))
