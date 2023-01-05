import sqlite3
import pathlib
from typing import Optional, Any

import aiosql

from ._types import Note, Tag, NoteId


class Base:
    def __init__(self, conn):
        self.conn = conn


class NoteRepository(Base):
    def find_by_name(self, name: str) -> list[int]:
        return [id for id, *_ in queries.note.find_by_name(self.conn, name)]

    def read_all(self) -> list[NoteId]:
        rs = queries.note.read_all(self.conn)
        return [NoteId(*r) for r in rs]

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


class TagRepository(Base):
    def find_by_name(self, tagname: str) -> list[Tag]:
        return queries.tag.find_by_name(self.conn, tagname)

    def read_all(self) -> list[Tag]:
        return queries.tag.read_all(self.conn)

    def create_one(self, name: str) -> int:
        rs = self.conn.execute(
            """
            SELECT id FROM tag WHERE name = ?;
                     """,
            (name,),
        ).fetchall()
        if rs:
            return rs[0][0]
        return conn.execute(
            """
            INSERT INTO tag (name) VALUES (?) RETURNING id;
            """,
            (name,),
        ).fetchall()[0][0]


class LinkRepository(Base):
    def create_one(self, parent_id, child_id):
        return queries.link.create_one(self.conn, parent_id, child_id)

    def read_all(self):
        return queries.link.read_all(self.conn)


class FileTagRepository(Base):
    def find_tag_by_filename(self, name: str) -> list[str]:
        return [tag for tag, *_ in queries.file_tag.find_tag_by_filename(conn, name)]

    def create_one(self, file_id: int, tag_id: int) -> None:
        return queries.file_tag.create_one(conn, file_id, tag_id)

    def find_file_by_tag(self, tag: str) -> list[Note]:
        return [Note(tag) for tag, *_ in queries.file_tag.find_file_by_tag(conn, tag)]


queries = aiosql.from_path(pathlib.Path(__file__).parent / "sql", "sqlite3")

conn = sqlite3.connect(":memory:")

queries.link.drop_table(conn)
queries.tag.drop_table(conn)
queries.file_tag.drop_table(conn)
queries.file.drop_table(conn)

queries.file.create_table(conn)
queries.link.create_table(conn)
queries.tag.create_table(conn)
queries.file_tag.create_table(conn)

file_tag_repo = FileTagRepository(conn)
file_repo = FileRepository(conn)
note_repo = NoteRepository(conn)
tag_repo = TagRepository(conn)
link_repo = LinkRepository(conn)
