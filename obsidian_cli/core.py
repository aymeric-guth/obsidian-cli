from typing import Any, Callable
import re

import yaml
import utils


def tag_parser(loader: Callable[[], str]) -> dict[Any, Any]:
    return (
        utils.default_exc(yaml.load, {})(m.group(1), yaml.CLoader)  # type: ignore
        if (
            m := re.compile(r"^[-]{3}([a-zA-Z0-9-_#:\s\n/]{1,})[-]{3}").search(loader())
        )
        else {}
    )
