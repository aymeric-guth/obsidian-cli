import os
import os.path
import sqlite3
import re
import pathlib
import yaml

import aiosql
import lsfiles
import utils

from ._types import Note


class Base:
    def __init__(self, conn):
        self.conn = conn


class Note(Base):
    def find_by_name(self, name: str) -> Note:
        return queries.note.find_by_name(self.conn, name)

    def read_all(self):
        return queries.note.read_all(self.conn)

    def find_by_name_path(self, name: str, path: str) -> Note:
        return queries.note.find_by_name_path(self.conn, name, path)


class File(Base):
    def find_by_name_extension(self, name: str, extension: str) -> list[Note]:
        return queries.file.find_by_name_extension(self.conn, name, extension)

    def create_many(self, files: list[Note]) -> None:
        return queries.file.create_many(self.conn, files)

    def find_by_name_extension_path(self, name: str, extension: str, path: str) -> Note:
        return queries.file.find_by_name_extension_path(
            self.conn, name, extension, path
        )


class Tag(Base):
    def find_by_name(self, tagname: str) -> list[tuple[int, str]]:
        return queries.tag.find_by_name(self.conn, tagname)

    def read_all(self):
        return queries.tag.read_all(self.conn)


class Link(Base):
    def create_one(self, parent_id, child_id):
        return queries.link.create_one(self.conn, parent_id, child_id)

    def read_all(self):
        return queries.link.read_all(self.conn)


class FileTag(Base):
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

file_tag = FileTag(conn)
file = File(conn)
note = Note(conn)
tag = Tag(conn)
link = Link(conn)
