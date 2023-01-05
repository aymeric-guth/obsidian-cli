from dataclasses import dataclass


@dataclass
class Note:
    path: str
    name: str
    ext: str
