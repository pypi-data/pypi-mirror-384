"""UUT data type for the Data Store Client."""

from __future__ import annotations

from typing import Iterable, Mapping, MutableMapping, MutableSequence

from ni.datastore.metadata._grpc_conversion import (
    populate_extension_value_message_map,
    populate_from_extension_value_message_map,
)
from ni.measurements.metadata.v1.metadata_store_pb2 import (
    Uut as UutProto,
)


class Uut:
    """Information about a Unit Under Test (UUT)."""

    __slots__ = (
        "model_name",
        "family",
        "_manufacturers",
        "part_number",
        "link",
        "_extensions",
        "schema_id",
    )

    @property
    def manufacturers(self) -> MutableSequence[str]:
        """The manufacturers of the UUT."""
        return self._manufacturers

    @property
    def extensions(self) -> MutableMapping[str, str]:
        """The extensions of the UUT."""
        return self._extensions

    def __init__(
        self,
        *,
        model_name: str = "",
        family: str = "",
        manufacturers: Iterable[str] | None = None,
        part_number: str = "",
        link: str = "",
        extensions: Mapping[str, str] | None = None,
        schema_id: str = "",
    ) -> None:
        """Initialize a Uut instance."""
        self.model_name = model_name
        self.family = family
        self._manufacturers: MutableSequence[str] = (
            list(manufacturers) if manufacturers is not None else []
        )
        self.part_number = part_number
        self.link = link
        self._extensions: MutableMapping[str, str] = (
            dict(extensions) if extensions is not None else {}
        )
        self.schema_id = schema_id

    @staticmethod
    def from_protobuf(uut_proto: UutProto) -> "Uut":
        """Create a Uut instance from a protobuf Uut message."""
        uut = Uut(
            model_name=uut_proto.model_name,
            family=uut_proto.family,
            manufacturers=uut_proto.manufacturers,
            part_number=uut_proto.part_number,
            link=uut_proto.link,
            schema_id=uut_proto.schema_id,
        )
        populate_from_extension_value_message_map(uut.extensions, uut_proto.extensions)
        return uut

    def to_protobuf(self) -> UutProto:
        """Convert this Uut to a protobuf Uut message."""
        uut_proto = UutProto(
            model_name=self.model_name,
            family=self.family,
            manufacturers=self.manufacturers,
            part_number=self.part_number,
            link=self.link,
            schema_id=self.schema_id,
        )
        populate_extension_value_message_map(uut_proto.extensions, self.extensions)
        return uut_proto

    def __eq__(self, other: object) -> bool:
        """Determine equality."""
        if not isinstance(other, Uut):
            return NotImplemented
        return (
            self.model_name == other.model_name
            and self.family == other.family
            and self.manufacturers == other.manufacturers
            and self.part_number == other.part_number
            and self.link == other.link
            and self.extensions == other.extensions
            and self.schema_id == other.schema_id
        )

    def __str__(self) -> str:
        """Return a string representation of the Uut."""
        return str(self.to_protobuf())
