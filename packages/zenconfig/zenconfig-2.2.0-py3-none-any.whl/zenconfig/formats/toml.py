from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import tomlkit

from zenconfig.base import BaseConfig, Format


@dataclass
class TOMLFormat(Format):
    sort_keys: bool = False

    def load(self, path: Path) -> Dict[str, Any]:
        return tomlkit.loads(path.read_text())

    def dump(
        self,
        path: Path,
        config: Dict[str, Any],
    ) -> None:
        path.write_text(tomlkit.dumps(config, sort_keys=self.sort_keys))


BaseConfig.register_format(TOMLFormat(), ".toml")
