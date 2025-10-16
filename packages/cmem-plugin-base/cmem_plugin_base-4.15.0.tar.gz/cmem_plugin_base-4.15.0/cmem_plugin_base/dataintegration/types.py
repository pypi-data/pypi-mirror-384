"""Parameter types."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from inspect import Parameter
from typing import Any, ClassVar, Generic, TypeVar

from cmem_plugin_base.dataintegration.context import PluginContext


@dataclass(frozen=True, eq=True)
class Autocompletion:
    """A single auto-completion result."""

    value: str
    """The value to which the parameter value should be set."""

    label: str | None
    """An optional label that a human user would see instead."""


T = TypeVar("T")


class ParameterType(Generic[T]):
    """Represent a plugin parameter type.

    Provides string-based serialization and autocompletion.
    """

    name: str
    """The name by which this type can be identified. If available,
    this should be the same as the corresponding DataIntegration type name."""

    allow_only_autocompleted_values: bool = False
    """Hint to the UI that it should only allow to set values for the parameter coming
     from the auto-completion.
    """

    autocomplete_value_with_labels: bool = False
    """Signals that the auto-completed values have labels that must be
    displayed to the user."""

    autocompletion_depends_on_parameters: ClassVar[list[str]] = []
    """The other plugin parameters the auto-completion depends on.
    Without those values given no auto-completion is possible.
    The values of all parameters specified here will be provided
    to the autocomplete function."""

    def get_type(self) -> type:
        """Retrieve the type that is supported by a given instance."""
        return self.__orig_bases__[0].__args__[0]  # type: ignore[attr-defined, no-any-return]

    def from_string(self, value: str, context: PluginContext) -> T:
        """Parse strings into parameter values."""

    def to_string(self, value: T) -> str:
        """Convert parameter values into their string representation."""
        return str(value)

    def autocomplete_query(
        self, query: str, depend_on_parameter_values: list[Any], context: PluginContext
    ) -> list[Autocompletion]:
        """Search for autocompletions based on a query string.

        Splits the query string into separate lower-cased terms and calls `autocomplete`.
        Usually, it is preferred to implement `autocomplete` instead of this method.
        """
        terms = [query.lower() for query in query.split() if query.strip()]
        return self.autocomplete(terms, depend_on_parameter_values, context)

    def autocomplete(
        self,
        query_terms: list[str],
        depend_on_parameter_values: list[Any],
        context: PluginContext,
    ) -> list[Autocompletion]:
        """Autocompletion request - Returns all results that match ALL provided query terms.

        :param query_terms: A list of lower case conjunctive search terms.
        :param depend_on_parameter_values The values of the parameters specified by
        'autocompletion_depends_on_parameters'. The type of each parameter value is the
        same as in the init method, e.g., a password parameter will be typed Password.
        :param context: The context in which the autocompletion is requested.
        """
        return []

    def label(
        self, value: str, depend_on_parameter_values: list[Any], context: PluginContext
    ) -> str | None:
        """Return the label if exists for the given value.

        :param value: The value for which a label should be generated.
        :param depend_on_parameter_values The values of the parameters specified
        by 'autocompletion_depends_on_parameters'.
        :param context: The context in which the label is requested.
        """
        return None

    def autocompletion_enabled(self) -> bool:
        """Enable autocompletion.

        True, if autocompletion should be enabled on this type.
        By default, checks if the type implements its own autocomplete method.
        """
        return (
            type(self).autocomplete != ParameterType.autocomplete
            or type(self).autocomplete_query != ParameterType.autocomplete_query
        )


class StringParameterType(ParameterType[str]):
    """String type"""

    name = "string"

    def from_string(self, value: str, context: PluginContext) -> str:
        """Return the string."""
        return value


class IntParameterType(ParameterType[int]):
    """Int type"""

    name = "Long"

    def from_string(self, value: str, context: PluginContext) -> int:
        """Parse string into int."""
        return int(value)


class FloatParameterType(ParameterType[float]):
    """Float type"""

    name = "double"

    def from_string(self, value: str, context: PluginContext) -> float:
        """Parse string into float."""
        return float(value)


class BoolParameterType(ParameterType[bool]):
    """Boolean type"""

    name = "boolean"

    def from_string(self, value: str, context: PluginContext) -> bool:
        """Get boolean value from string"""
        lower = value.lower()
        if lower in ("true", "1"):
            return True
        if lower in ("false", "0"):
            return False
        raise ValueError("Value must be either 'true' or 'false'")

    def to_string(self, value: bool) -> str:
        """Get string value from boolean"""
        if value:
            return "true"
        return "false"


class PluginContextParameterType(ParameterType[PluginContext]):
    """Used to pass context information into plugins"""

    name = "PluginContext"

    def from_string(self, value: str, context: PluginContext) -> PluginContext:
        """Return the plugin context."""
        return context

    def to_string(self, value: PluginContext) -> str:
        """Return an empty string, since from_string will always return the plugin context."""
        return ""


class EnumParameterType(ParameterType[Enum]):
    """Enumeration type"""

    name = "enumeration"

    allow_only_autocompleted_values = True

    def __init__(self, enum_type: type[Enum]):
        super().__init__()
        self.enum_type = enum_type

    def from_string(self, value: str, context: PluginContext) -> Enum:
        """Parse string into the corresponding enum value."""
        values = self.enum_type.__members__
        if not value:
            raise ValueError("Empty value is not allowed.")
        if value not in values:
            vals = ", ".join(list(values.keys()))
            raise ValueError(f"'{value}' is not a valid value. Valid values: {vals}.")
        return values[value]

    def to_string(self, value: Enum) -> str:
        """Convert an enum into its string value."""
        return str(value.name)

    def autocomplete(
        self,
        query_terms: list[str],
        depend_on_parameter_values: list[str],
        context: PluginContext,
    ) -> list[Autocompletion]:
        """Autocompletion request - Returns all results that match all provided query terms."""
        values = self.enum_type.__members__.keys()
        return list(self.find_matches(query_terms, values))

    @staticmethod
    def find_matches(
        lower_case_terms: list[str], values: Iterable[str]
    ) -> Iterable[Autocompletion]:
        """Find auto completions in a list of values"""
        for value in values:
            if EnumParameterType.matches_search_term(lower_case_terms, value.lower()):
                yield Autocompletion(value, value)

    @staticmethod
    def matches_search_term(lower_case_terms: list[str], search_in: str) -> bool:
        """Test if a string contains a list of (lower case) search terms."""
        lower_case_text = search_in.lower()
        return all(search_term in lower_case_text for search_term in lower_case_terms)


class ParameterTypes:
    """Manages the available parameter types."""

    registered_types: ClassVar[list[ParameterType]] = [
        StringParameterType(),
        BoolParameterType(),
        IntParameterType(),
        FloatParameterType(),
        PluginContextParameterType(),
    ]

    @staticmethod
    def register_type(param_type: ParameterType) -> None:
        """Register a new custom parameter type.

        All registered types will be detected
        in plugin constructors. If a type with an existing name is registered, it will
        overwrite the previous one.
        """
        ParameterTypes.registered_types = [
            t for t in ParameterTypes.registered_types if t.name != param_type.name
        ]
        ParameterTypes.registered_types.append(param_type)

    @staticmethod
    def get_type(param_type: type) -> ParameterType:
        """Retrieve the ParameterType instance for a given type."""
        if issubclass(param_type, Enum):
            return EnumParameterType(param_type)
        found_type = next(
            (t for t in ParameterTypes.registered_types if issubclass(param_type, t.get_type())),
            None,
        )
        if found_type is None:
            mapped = [str(t.get_type().__name__) for t in ParameterTypes.registered_types]
            raise ValueError(
                f"Parameter has an unsupported type {param_type.__name__}. "
                "Supported types are: Enum, "
                f"{', '.join(list(mapped))}."
            )
        return found_type

    @staticmethod
    def get_param_type(param: Parameter) -> ParameterType:
        """Retrieve the ParameterType instance for a given parameter."""
        if param.annotation == Parameter.empty:
            # If there is no type annotation, DI should send the parameter as a string
            return StringParameterType()
        return ParameterTypes.get_type(param.annotation)
