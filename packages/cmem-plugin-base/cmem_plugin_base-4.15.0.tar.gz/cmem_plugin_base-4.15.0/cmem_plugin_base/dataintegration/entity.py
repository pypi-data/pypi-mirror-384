"""Instance of any given concept."""

from collections.abc import Iterator, Sequence


class EntityPath:
    """A path in a schema.

    :param is_relation: If true, values for this path must only contain URIs that
    point to a sub entity.
    :param is_single_value If true, a single value is expected and supporting datasets
    will not use arrays etc. For instance, in XML, attributes will be used instead of
    nested elements.
    """

    def __init__(self, path: str, is_relation: bool = False, is_single_value: bool = False) -> None:
        self.path = path
        self.is_relation = is_relation
        self.is_single_value = is_single_value

    def __repr__(self) -> str:
        """Get a string representation"""
        obj = {
            "path": self.path,
            "is_relation": self.is_relation,
            "is_single_value": self.is_single_value,
        }
        return f"EntityPath({obj})"

    def __eq__(self, other: object) -> bool:
        """Compare"""
        return (
            isinstance(other, EntityPath)
            and self.path == other.path
            and self.is_relation == other.is_relation
            and self.is_single_value == other.is_single_value
        )

    def __hash__(self) -> int:
        """Return a hash value based on its path, relation status, and single value status."""
        return hash((self.path, self.is_relation, self.is_single_value))


class EntitySchema:
    """An entity schema.

    :param type_uri: The entity type
    :param paths: Ordered list of paths
    :param path_to_root: Specifies a path which defines where this schema is located
    in the schema tree. Empty by default.
    :param sub_schemata: Nested entity schemata
    """

    def __init__(
        self,
        type_uri: str,
        paths: Sequence[EntityPath],
        path_to_root: EntityPath | None = None,
        sub_schemata: Sequence["EntitySchema"] | None = None,
    ) -> None:
        self.type_uri = type_uri
        self.paths = paths
        if path_to_root is None:
            self.path_to_root = EntityPath("")
        else:
            self.path_to_root = path_to_root
        self.sub_schemata = sub_schemata

    def __repr__(self) -> str:
        """Get a string representation"""
        obj = {"type_uri": self.type_uri, "paths": self.paths, "path_to_root": self.path_to_root}
        return f"EntitySchema({obj})"

    def __eq__(self, other: object) -> bool:
        """Compare"""
        return (
            isinstance(other, EntitySchema)
            and self.type_uri == other.type_uri
            and self.paths == other.paths
            and self.path_to_root == other.path_to_root
            and self.sub_schemata == other.sub_schemata
        )

    def __hash__(self) -> int:
        """Return a hash value based on its attributes."""
        return hash(
            (
                self.type_uri,
                tuple(self.paths),
                self.path_to_root,
                tuple(self.sub_schemata) if self.sub_schemata is not None else None,
            )
        )


class Entity:
    """An Entity can represent an instance of any given concept.

    :param uri: The URI of this entity
    :param values: All values of this entity. Contains a sequence of values for
        each path in the schema.

    TODO: uri generation
    """

    def __init__(self, uri: str, values: Sequence[Sequence[str]]) -> None:
        self.uri = uri
        self.values = values


class Entities:
    """Holds a collection of entities and their schema.

    :param entities: An iterable collection of entities. May be very large, so it
        should be iterated over and not loaded into memory at once.
    :param schema: All entities conform to this entity schema.
    :param sub_entities Additional entity collections.
    """

    def __init__(
        self,
        entities: Iterator[Entity],
        schema: EntitySchema,
        sub_entities: Sequence["Entities"] | None = None,
    ) -> None:
        self.entities = entities
        self.schema = schema
        self.sub_entities = sub_entities
