import sqlite3
import pathlib
from typing import Optional
import os

import aiosql

from ._types import Tag, Note


class Base:
    def __init__(self, conn):
        self.conn = conn


class Init(Base):
    def __call__(self):
        queries.link.drop_table(self.conn)
        queries.tag.drop_table(self.conn)
        queries.file_tag.drop_table(self.conn)
        queries.file.drop_table(self.conn)

        queries.file.create_table(self.conn)
        queries.link.create_table(self.conn)
        queries.tag.create_table(self.conn)
        queries.file_tag.create_table(self.conn)


class NoteRepository(Base):
    def find_by_id(self, id: int) -> Optional[Note]:
        note = queries.note.find_by_id(self.conn, id=id)
        if note is not None:
            return Note(*note)

    def find_by_name(self, name: str) -> list[Note]:
        return [Note(*note) for note in queries.note.find_by_name(self.conn, name)]

    def read_all(self) -> list[Note]:
        rs = queries.note.read_all(self.conn)
        return [Note(*r) for r in rs]

    def find_by_name_path(self, name: str, path: str) -> Optional[int]:
        return queries.note.find_by_name_path(self.conn, name, path)


class FileRepository(Base):
    def find_by_name_extension(self, name: str, extension: str) -> list[int]:
        return [
            id
            for id, *_ in queries.file.find_by_name_extension(
                self.conn, name, extension
            )
        ]

    def create_many(self, files: list[tuple[str, str, str]]) -> None:
        return queries.file.create_many(self.conn, files)

    def find_by_name_extension_path(
        self, name: str, extension: str, path: str
    ) -> Optional[int]:
        return queries.file.find_by_name_extension_path(
            self.conn, name, extension, path
        )

    def read_all_path(self) -> list[str]:
        interpolated = set()
        for path, *_ in queries.file.read_all_path(self.conn):
            p = path.split("/")
            for i in range(len(p)):
                interpolated.add("/".join(p[: i + 1]))

        res = list(interpolated)
        res.sort()
        return res


class TagRepository(Base):
    def find_by_name(self, tagname: str) -> list[Tag]:
        return queries.tag.find_by_name(self.conn, tagname)

    def read_all(self) -> list[str]:
        return [tag for tag, *_ in queries.tag.read_all(self.conn)]

    def create_one(self, name: str) -> int:
        rs = queries.tag.read_one(self.conn, name)
        if rs:
            return rs
        return queries.tag.create_one(self.conn, name)


class LinkRepository(Base):
    def create_one(self, parent_id, child_id):
        return queries.link.create_one(self.conn, parent_id, child_id)

    def read_all(self):
        return queries.link.read_all(self.conn)

    def find_file_by_link(self, name: str) -> list[Note]:
        return [Note(*note) for note in queries.link.find_file_by_link(self.conn, name)]

    def find_orphaned(self) -> list[Note]:
        return [Note(*note) for note in queries.link.find_orphaned(self.conn)]

    def find_orphaned_dir(self, dir: str) -> list[Note]:
        return [
            Note(*note)
            for note in queries.link.find_orphaned_dir(self.conn, f"%{dir}%")
        ]


class FileTagRepository(Base):
    def find_tag_by_filename(self, name: str) -> list[str]:
        return [tag for tag, *_ in queries.file_tag.find_tag_by_filename(conn, name)]

    def create_one(self, file_id: int, tag_id: int) -> None:
        try:
            return queries.file_tag.create_one(conn, file_id, tag_id)
        except sqlite3.IntegrityError as err:
            ...
            # suposed note using the same tag twice or more
            # print(f"{tag_id=} note={NoteRepository(conn).find_by_id(file_id)}")
            # raise

    def create_many(self, tag_repo: list[tuple[int, int]]) -> None:
        return queries.file_tag.create_many(conn, tag_repo)

    def find_file_by_tag(self, tag: str) -> list[Note]:
        return [Note(*note) for note in queries.file_tag.find_file_by_tag(conn, tag)]


queries = aiosql.from_path(pathlib.Path(__file__).parent / "sql", "sqlite3")
workspace = os.getenv("WORKSPACE")
if not workspace:
    raise RuntimeError("WORKSPACE is not defined")
conn = sqlite3.connect(f"{workspace}/db.sqlite")
# conn = sqlite3.connect(":memory:")


file_tag = FileTagRepository(conn)
file = FileRepository(conn)
note = NoteRepository(conn)
tag = TagRepository(conn)
link = LinkRepository(conn)
init = Init(conn)
