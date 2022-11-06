from utils import fnc
from utils import cli


class Environment:
    def __init__(self):
        self._registry: dict[str, str] = {}

    def _register(self, varname: str) -> tuple[str, int]:
        (msg, ok) = cli.check_env(varname)
        if not ok:
            return cli.failure("msg")
        self._registry.update({varname: msg})
        return cli.success(msg)

    def get(self, varname: str) -> tuple[str, int]:
        value = self._registry.get(varname)
        if not value:
            return self._register(varname)
        return cli.success(value)

    def set(self, varname: str, value: str) -> tuple[str, int]:
        prev = self._registry.get(varname)
        if not prev or value != prev:
            self._registry.update({varname: value})
        return cli.success(value)


# env = Environment()

# fnc.Maybe.unit("OBSIDIAN_VAULT").bind(env.get).
# (msg, ok) = env.get("OBSIDIAN_VAULT")
# if not ok:
#    return cli.failure(msg)
#
# (msg, ok) = env.get("OBSIDIAN_DIR")
# if not ok:
#    return cli.failure(msg)
