from dataclasses import dataclass, field
from typing import Optional

__NAMESPACE__ = "urn:oasis:names:tc:entity:xmlns:xml:catalog"


@dataclass
class Uri:
    class Meta:
        name = "uri"
        namespace = "urn:oasis:names:tc:entity:xmlns:xml:catalog"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    uri: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Catalog:
    class Meta:
        name = "catalog"
        namespace = "urn:oasis:names:tc:entity:xmlns:xml:catalog"

    schema_location: Optional[str] = field(
        default=None,
        metadata={
            "name": "schemaLocation",
            "type": "Attribute",
            "namespace": "http://www.w3.org/2001/XMLSchema-instance",
            "required": True,
        },
    )
    prefer: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    uri: list[Uri] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )
