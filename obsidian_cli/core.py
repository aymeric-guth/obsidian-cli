import pathlib
from typing import Any, Callable
import re
import os
import collections

import yaml
import utils
import lsfiles


class Vault:
    def __init__(self, root: str) -> None:
        wikilink = re.compile(r"(?:[\[]{2}(.*)[\]]{2})")
        mdlink = re.compile(r"(?:\[(.*)\])\((.*)\)")
        modifiers = re.compile(r"[\#\|\^]{1,}")
        pathlink = re.compile(r"/{1,}")

        self.root = pathlib.Path(root)
        self.vault_prefix = len(root) + 1
        if not self.root.exists():
            # basic sanity check, might not be necessary
            raise Exception()
        self._registry: dict[str, list[str]] = collections.defaultdict(list)
        self.files = lsfiles.iterativeDFS(
            filters=lsfiles.filters.ext(
                {
                    ".md",
                }
            ),
            adapter=pathlib.PurePath,
            root=self.root,
        )

        for f in self.files:
            self._registry[f.name[: -len(f.suffix)]].append(
                str(f.parent)[self.vault_prefix :]
            )


def tag_parser(loader: Callable[[], str]) -> dict[Any, Any]:
    return (
        utils.default_exc(yaml.load, {})(m.group(1), yaml.CLoader)  # type: ignore
        if (
            m := re.compile(r"^[-]{3}([a-zA-Z0-9-_#:\s\n/]{1,})[-]{3}").search(loader())
        )
        else {}
    )


if __name__ == "__main__":
    Vault(os.getenv("OBSIDIAN_VAULT"))
    # link_parser()
