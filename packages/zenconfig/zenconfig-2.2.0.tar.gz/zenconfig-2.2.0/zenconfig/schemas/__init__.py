import contextlib

from zenconfig.schemas.dataclass import DataclassSchema
from zenconfig.schemas.dict import DictSchema

with contextlib.suppress(ImportError):
    from zenconfig.schemas.pydantic import PydanticSchema
with contextlib.suppress(ImportError):
    from zenconfig.schemas.attrs import AttrsSchema
