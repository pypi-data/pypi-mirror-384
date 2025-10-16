"""Quad entities"""

import uuid
from typing import ClassVar, cast

from pydantic import BaseModel

from cmem_plugin_base.dataintegration.entity import Entity, EntityPath
from cmem_plugin_base.dataintegration.typed_entities import path_uri, type_uri
from cmem_plugin_base.dataintegration.typed_entities.typed_entities import (
    TypedEntitySchema,
)

# --- RDF Node Types ---


class RdfNode(BaseModel):
    """Abstract base class for an RDF node."""

    type: ClassVar[str]
    """The type code that identifies this RDF node type. Must be defined in subclasses."""

    value: str
    """The value of the RDF node. This is typically a URI, a blank node identifier, or a literal."""


class ConcreteNode(RdfNode):
    """Abstract base class for an RdfNode which is either a Resource or a BlankNode."""


class Resource(ConcreteNode):
    """Represents an RDF resource (typically a URI)."""

    type: ClassVar[str] = "URI"

    value: str  # The URI of the resource


class BlankNode(ConcreteNode):
    """Represents an RDF blank node."""

    type: ClassVar[str] = "BlankNode"

    value: str  # Usually the identifier without the '_:' prefix internally


class Literal(RdfNode):
    """Abstract base class for an RDF literal."""


class PlainLiteral(Literal):
    """Represents a plain literal without a language tag or datatype."""

    type: ClassVar[str] = "Literal"

    value: str


class LanguageLiteral(Literal):
    """Represents a literal with a language tag."""

    type: ClassVar[str] = "LangLiteral"

    value: str
    language: str


class DataTypeLiteral(Literal):
    """Represents a literal with a specific datatype."""

    type: ClassVar[str] = "TypedLiteral"

    value: str
    data_type: str = "http://www.w3.org/2001/XMLSchema#string"  # Default datatype IRI for literals


class Quad(BaseModel):
    """Represents an RDF Quad."""

    subject: ConcreteNode
    predicate: Resource
    object: RdfNode
    graph: Resource | None = None


def create_node(
    type_name: str, value: str, language: str | None = None, data_type: str | None = None
) -> RdfNode:
    """Create an RDF node for a given type name."""
    match type_name:
        case Resource.type:
            return Resource(value=value)
        case BlankNode.type:
            return BlankNode(value=value)
        case PlainLiteral.type:
            return PlainLiteral(value=value)
        case LanguageLiteral.type:
            if language is None:
                raise ValueError("Language must be provided for LanguageLiteral.")
            return LanguageLiteral(value=value, language=language)
        case DataTypeLiteral.type:
            if data_type is None:
                raise ValueError("Data type must be provided for DataTypeLiteral.")
            return DataTypeLiteral(value=value, data_type=data_type)
        case _:
            raise ValueError(f"Unknown type: {type_name}")


# --- RDF Quad Schema ---


class QuadEntitySchema(TypedEntitySchema[Quad]):
    """Entity schema that holds a collection of RDF quads."""

    def __init__(self):
        # The parent class TypedEntitySchema implements a singleton pattern
        if not hasattr(self, "_initialized"):
            super().__init__(
                type_uri=type_uri("Quad"),
                paths=[
                    EntityPath(path_uri("quad/subject")),
                    EntityPath(path_uri("quad/subjectType")),
                    EntityPath(path_uri("quad/predicate")),
                    EntityPath(path_uri("quad/object")),
                    EntityPath(path_uri("quad/objectType")),
                    EntityPath(path_uri("quad/objectLanguage")),
                    EntityPath(path_uri("quad/objectDataType")),
                    EntityPath(path_uri("quad/graph")),
                ],
            )

    def to_entity(self, quad: Quad) -> Entity:
        """Create a generic entity from an RDF quad."""
        # Extract object language
        match quad.object:
            case LanguageLiteral(language=lang):
                object_language = [lang]
            case _:
                object_language = []

        # Extract object data type
        match quad.object:
            case DataTypeLiteral(data_type=dt):
                object_data_type = [dt]
            case _:
                object_data_type = []

        # Generate a UUID-based URI
        uri_components = "".join(
            [
                quad.subject.value,
                quad.predicate.value,
                quad.object.value,
                object_language[0] if object_language else "",
                object_data_type[0] if object_data_type else "",
                quad.graph.value if quad.graph else "",
            ]
        )
        uri = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, uri_components)}"

        # Build entity
        return Entity(
            uri=uri,
            values=[
                [quad.subject.value],
                [quad.subject.type],
                [quad.predicate.value],
                [quad.object.value],
                [quad.object.type],
                object_language,
                object_data_type,
                [quad.graph.value] if quad.graph else [],
            ],
        )

    def from_entity(self, entity: Entity) -> Quad:
        """Create an RDF quad entity from a generic entity."""
        # Indices for the values in the entity
        subject_index = 0
        subject_type_index = 1
        predicate_index = 2
        object_index = 3
        object_type_index = 4
        object_language_index = 5
        object_data_type_index = 6
        graph_index = 7

        # Get entity values
        values = entity.values

        # Subject
        subject_type_list = values[subject_type_index]
        if len(subject_type_list) == 1:
            subject = create_node(subject_type_list[0], values[subject_index][0])
        else:
            raise ValueError(f"Invalid subject type: {subject_type_list}. Expected a single value.")

        # Predicate
        predicate = Resource(value=values[predicate_index][0])

        # Object
        object_type_list = values[object_type_index]
        if len(object_type_list) == 1:
            lang_list = values[object_language_index]
            lang = lang_list[0] if lang_list else None
            type_list = values[object_data_type_index]
            type_id = type_list[0] if type_list else None
            object_value = create_node(object_type_list[0], values[object_index][0], lang, type_id)
        else:
            raise ValueError(f"Invalid object type: {object_type_list}. Expected a single element.")

        # Graph
        graph_list = values[graph_index]
        graph: Resource | None = None
        if graph_list:
            graph = Resource(value=graph_list[0])

        # Build the Quad
        return Quad(
            subject=cast("ConcreteNode", subject),
            predicate=predicate,
            object=object_value,
            graph=graph,
        )
