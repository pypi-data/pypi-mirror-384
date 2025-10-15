from __future__ import annotations

from pydantic import field_validator
from typing import Any, Optional, List

from metricflow.model.objects.base import HashableBaseModel, ModelWithMetadataParsing
from metricflow.model.objects.common import Metadata
from metricflow.object_utils import ExtendedEnum
from metricflow.references import IdentifierReference, CompositeSubIdentifierReference


class IdentifierType(ExtendedEnum):
    """Defines uniqueness and the extent to which an identifier represents the common entity for a data source"""

    FOREIGN = "foreign"
    NATURAL = "natural"
    PRIMARY = "primary"
    UNIQUE = "unique"


class CompositeSubIdentifier(HashableBaseModel):
    """CompositeSubIdentifiers either describe or reference the identifiers that comprise a composite identifier"""

    name: Optional[str] = None
    expr: Optional[str] = None
    ref: Optional[str] = None

    @property
    def reference(self) -> CompositeSubIdentifierReference:  # noqa: D
        assert self.name, f"The element name should have been set during model transformation. Got {self}"
        return CompositeSubIdentifierReference(element_name=self.name)


class Identifier(HashableBaseModel, ModelWithMetadataParsing):
    """Describes a identifier"""

    name: str
    description: Optional[str] = None
    type: IdentifierType
    role: Optional[str] = None
    entity: Optional[str] = None
    identifiers: List[CompositeSubIdentifier] = []
    expr: Optional[str] = None
    metadata: Optional[Metadata] = None

    @field_validator("entity", mode="before")
    @classmethod
    def default_entity_value(cls, value: Any, info) -> str:  # type: ignore[misc]
        """Defaulting the value of the identifier 'entity' value using pydantic validator

        If an entity value is provided that is a string, that will become the value of
        entity. If the provifed entity value is None, the entity value becomes the
        element_name representation of the identifier's name.
        """

        if value is None:
            if hasattr(info, 'data') and "name" in info.data:
                value = info.data["name"]
            elif hasattr(info, 'context') and info.context and "name" in info.context:
                value = info.context["name"]
            else:
                # If we can't get the name, we'll return None and let the default handle it
                return None

        # guarantee value is string
        if value is not None and not isinstance(value, str):
            raise ValueError(f"Entity value should be a string (str) type, but got {type(value)} with value: {value}")
        return value

    @property
    def is_primary_time(self) -> bool:  # noqa: D
        return False

    @property
    def is_composite(self) -> bool:  # noqa: D
        return self.identifiers is not None and len(self.identifiers) > 0

    @property
    def reference(self) -> IdentifierReference:  # noqa: D
        return IdentifierReference(element_name=self.name)

    @property
    def is_linkable_identifier_type(self) -> bool:
        """Indicates whether or not this identifier can be used as a linkable identifier type for joins

        That is, can you use the identifier as a linkable element in multi-hop dundered syntax. For example,
        the country dimension in the listings data source can be linked via listing__country, because listing
        is the primary key.

        At the moment, you may only request things accessible via primary, unique, or natural keys, with natural
        keys reserved for SCD Type II style data sources.
        """
        return self.type in (IdentifierType.PRIMARY, IdentifierType.UNIQUE, IdentifierType.NATURAL)
