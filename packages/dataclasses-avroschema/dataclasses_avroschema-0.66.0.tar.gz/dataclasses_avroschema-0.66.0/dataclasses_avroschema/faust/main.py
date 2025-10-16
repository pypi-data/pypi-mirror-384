import typing

from fastavro.validation import validate

from dataclasses_avroschema import AvroModel, serialization
from dataclasses_avroschema.types import JsonDict
from dataclasses_avroschema.utils import standardize_custom_type

from .parser import FaustParser

try:
    from faust import Record  # pragma: no cover
except ImportError as ex:  # pragma: no cover
    raise Exception("faust-streaming must be installed in order to use AvroRecord") from ex  # pragma: no cover


class AvroRecord(Record, AvroModel):  # type: ignore
    def validate_avro(self) -> bool:
        """
        Validate that instance matches the avro schema
        """
        schema = self.avro_schema_to_python()
        return validate(self.asdict(), schema)

    def standardize_type(self, include_type: bool = True) -> typing.Any:
        """
        Standardization factory that converts data according to the
        user-defined pydantic json_encoders prior to passing values
        to the standard type conversion factory
        """
        return {
            field_name: standardize_custom_type(
                field_name=field_name, value=value, model=self, base_class=AvroRecord, include_type=include_type
            )
            for field_name, value in self.asdict().items()
        }

    def serialize(self, serialization_type: serialization.SerializationType = "avro") -> bytes:
        """
        Overrides the base AvroModel's serialize method to inject this
        class's standardization factory method
        """
        schema = self.avro_schema_to_python()
        data = self.standardize_type()

        return serialization.serialize(
            data,
            schema,
            serialization_type=serialization_type,
        )

    def to_dict(self) -> JsonDict:
        return self.standardize_type(include_type=False)

    @classmethod
    def _generate_parser(cls: typing.Type["AvroRecord"]) -> FaustParser:
        return FaustParser(type=cls, parent=cls._parent or cls)
