from dataclasses import dataclass
import pathlib

from utils import cli


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


@dataclass(frozen=True)
class Tag:
    id: int
    name: str
