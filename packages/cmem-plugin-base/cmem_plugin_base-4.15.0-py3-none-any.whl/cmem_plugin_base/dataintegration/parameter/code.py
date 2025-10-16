"""DI Code Parameter Type."""

import typing
from typing import Generic, TypeVar

from cmem_plugin_base.dataintegration.context import PluginContext
from cmem_plugin_base.dataintegration.types import ParameterType, ParameterTypes


class Code:
    """Base class of all code types.

    Don't use directly, instead use one of the subclasses.
    """

    code: str
    """The code string"""

    def __str__(self) -> str:
        """Return the code string representation."""
        return self.code


class JinjaCode(Code):
    """Jinja 2 code"""

    def __init__(self, code: str):
        self.code = code


class JsonCode(Code):
    """JSON code"""

    def __init__(self, code: str):
        self.code = code


class SparqlCode(Code):
    """SPARQL code"""

    def __init__(self, code: str):
        self.code = code


class SqlCode(Code):
    """SQL code"""

    def __init__(self, code: str):
        self.code = code


class XmlCode(Code):
    """XML code"""

    def __init__(self, code: str):
        self.code = code


class YamlCode(Code):
    """YAML code"""

    def __init__(self, code: str):
        self.code = code


class TurtleCode(Code):
    """RDF Turtle code"""

    def __init__(self, code: str):
        self.code = code


class PythonCode(Code):
    """Python code"""

    def __init__(self, code: str):
        self.code = code


LANG = TypeVar("LANG", bound=Code)


class CodeParameterType(ParameterType[LANG], Generic[LANG]):
    """Code parameter type."""

    def __init__(self, code_mode: str):
        """Code parameter type."""
        self.name = "code-" + code_mode

    # pylint: disable=no-member
    def get_type(self) -> type:
        """Retrieve the concrete code type."""
        return typing.get_args(self.__orig_class__)[0]  # type: ignore[attr-defined, no-any-return]

    def from_string(self, value: str, context: PluginContext) -> LANG:
        """Parse strings into code instances."""
        code: LANG = self.get_type()(value)
        return code

    def to_string(self, value: LANG) -> str:
        """Convert code values into their string representation."""
        return value.code


ParameterTypes.register_type(CodeParameterType[JinjaCode]("jinja2"))
ParameterTypes.register_type(CodeParameterType[JsonCode]("json"))
ParameterTypes.register_type(CodeParameterType[SparqlCode]("sparql"))
ParameterTypes.register_type(CodeParameterType[SqlCode]("sql"))
ParameterTypes.register_type(CodeParameterType[XmlCode]("xml"))
ParameterTypes.register_type(CodeParameterType[YamlCode]("yaml"))
ParameterTypes.register_type(CodeParameterType[TurtleCode]("turtle"))
ParameterTypes.register_type(CodeParameterType[PythonCode]("python"))
