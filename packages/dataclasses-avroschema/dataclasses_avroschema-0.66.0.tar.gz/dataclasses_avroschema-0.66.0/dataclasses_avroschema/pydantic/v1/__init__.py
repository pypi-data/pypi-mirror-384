from .main import AvroBaseModel  # noqa: F401 I001
from .mapper import (
    PYDANTIC_INMUTABLE_FIELDS_CLASSES,
    PYDANTIC_LOGICAL_TYPES_FIELDS_CLASSES,
)
from dataclasses_avroschema.fields import mapper

mapper.IMMUTABLE_FIELDS_CLASSES.update(PYDANTIC_INMUTABLE_FIELDS_CLASSES)
mapper.LOGICAL_TYPES_FIELDS_CLASSES.update(PYDANTIC_LOGICAL_TYPES_FIELDS_CLASSES)  # type: ignore
