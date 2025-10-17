import contextlib

from zenconfig.formats.json import JSONFormat

with contextlib.suppress(ImportError):
    from zenconfig.formats.yaml import YAMLFormat
with contextlib.suppress(ImportError):
    from zenconfig.formats.toml import TOMLFormat
