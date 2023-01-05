from dataclasses import dataclass
import pathlib
import urllib.parse

from utils import cli


# file, every non-md file
# path, name, ext
# note, md file
# path, name

# link
# relation note -> file | note

# tag
# name

# tag_file
# note -> tag


@dataclass(frozen=True)
class Note:
    path: str
    name: str
    extension: str


@dataclass(frozen=True)
class NoteId:
    id: int
    path: str
    name: str
    extension: str

    def to_md(self) -> pathlib.Path:
        return (
            pathlib.Path(cli.env.get("OBSIDIAN_VAULT"))
            / self.path
            / f"{self.name}{self.extension}"
        )

    def to_obsidian(self) -> str:
        return urllib.parse.quote(self.__str__())

    def __str__(self) -> str:
        return f"{self.path}/{self.name}{self.extension}"


@dataclass(frozen=True)
class Tag:
    id: int
    name: str
