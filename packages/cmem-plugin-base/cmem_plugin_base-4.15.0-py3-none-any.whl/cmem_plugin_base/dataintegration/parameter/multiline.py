"""DI Multiline String Parameter Type."""

from cmem_plugin_base.dataintegration.types import StringParameterType


class MultilineStringParameterType(StringParameterType):
    """Multiline string parameter type."""

    name = "multiline string"
    """Same type name as MultilineStringParameterType in DataIntegration code base."""
