from dataclasses import dataclass


@dataclass
class Note:
    name: str
    path: str
    ext: str
