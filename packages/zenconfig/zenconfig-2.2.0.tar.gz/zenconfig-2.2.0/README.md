# zen-config

[![tests](https://github.com/gpajot/zen-config/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/gpajot/zen-config/actions/workflows/test.yml?query=branch%3Amain+event%3Apush)
[![PyPi](https://img.shields.io/pypi/v/zenconfig?label=stable)](https://pypi.org/project/zenconfig/)
[![python](https://img.shields.io/pypi/pyversions/zenconfig)](https://pypi.org/project/zenconfig/)

Simple configuration loader for python.

Compared to other solutions, the goal is to bring:
- simple usage for simple use cases
- multiple format support
- use objects rather than plain dict to interact with the config
- optionally use the power of pydantic for validation

## Simple usage
If you don't want to configure much, pass the config path through the env variable `CONFIG`, and simply use:
```python
from dataclasses import dataclass
from zenconfig import Config

@dataclass
class MyConfig(Config):
    some_key: str
    some_optional_key: bool = False


cfg = MyConfig(some_key="hello")
cfg.save()
...
cfg = MyConfig.load()
cfg.some_optional_key = True
cfg.save()
...
cfg.clear()
```

## Config file loading
When creating your config, you can specify at least one of those two attributes:
- `ENV_PATH` the environment variable name containing the path to the config file, defaults to `CONFIG`
- `PATH` directly the config path

> [!TIP]
> When supplying both, if the env var is not set, it will use `PATH`.

User constructs will be expanded.
If the file does not exist it will be created.
You can specify the file mode via `Config.FILE_MODE`.

The config can be loaded from multiple files, see [fnmatch](https://docs.python.org/3/library/fnmatch.html) for syntax.
Note that you will not be able to save if not handling exactly one file.

## Read only
If you do not want to be able to modify the config from your code, you can use `ReadOnlyConfig`.

## Supported formats
Currently, those formats are supported:
- JSON
- YAML - requires the `yaml` extra
- TOML - requires the `toml` extra

The format is automatically inferred from the config file extension.
When loading from multiple files, files can be of multiple formats.

Other formats can be added by subclassing `Format`: `Config.register_format(MyFormat(...), ".ext1", ".ext2")`.

> [!TIP]
> You can re-register a format to change dumping options.

## Supported schemas
Currently, those schemas are supported:
- plain dict
- dataclasses
- pydantic models - requires the `pydantic` extra
- attrs - requires the `attrs` extra

The schema is automatically inferred from the config class.

Other schemas can be added by subclassing `Schema`: `Config.register_schema(MySchema(...))`.

You can also force the schema by directly overriding the `SCHEMA` class attribute on your config.
This can be used to disable auto selection, or pass arguments to the schema instance.

> [!WARNING]
> When using pydantic, you have to supply the `ClassVar` type annotations
> to all class variable you override
> otherwise pydantic will treat those as its own fields and complain.

### Conversions
For all schemas and formats, common built in types are handled [when dumping](https://github.com/gpajot/zen-config/blob/main/zenconfig/encoder.py).

> [!IMPORTANT]
> Keep in mind that only `attrs` and `pydantic` support casting when loading the config.

You can add custom encoders with `Config.ENCODERS`.
For `pydantic`, stick with [the standard way of doing it](https://docs.pydantic.dev/latest/usage/serialization/#custom-serializers).


## Contributing
See [contributing guide](https://github.com/gpajot/zen-config/blob/main/CONTRIBUTING.md).
