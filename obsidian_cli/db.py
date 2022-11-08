import os
import sqlite3
import re
import collections
import pathlib

import lsfiles


con = sqlite3.connect(":memory:")
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


def create_links(cur, data: list[tuple[int, int]]) -> None:
    ...


wikilink = re.compile(r"(?:[\[]{2}(.*)[\]]{2})")
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
        (f.name[: -(len(f.suffix))], f.suffix, str(f.parent)[vault_prefix:])
        for f in files
    ],
)


for i in read_notes(cur):
    print(i)
# links: dict[str, list[str]] = collections.defaultdict(list)
# for _id, name, path in read_notes(cur):
#    md = root / path / f"{name}.md"
#    raw = (lambda f: open(f).read())(md)
#    matches = wikilink.findall(raw)
#    links = [modifiers.split(m)[0] for m in matches]
#    for l in links:
#        if "." in l:
#            # peu etre un fichier md contenant un point, peut etre un fichier non-md
#            # test d'appartenance aux notes dans la db
#            ...
#        if pathlink.search(l):
#            # resolution immediate en cherchant path et name dans read_notes
#            # possibilité que ce soit un fichier non-md référencé par un path complet
#            ...
