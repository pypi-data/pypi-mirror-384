"""DI Resource Parameter Type."""

from typing import Any

from cmem.cmempy.workspace.projects.resources import get_resources

from cmem_plugin_base.dataintegration.context import PluginContext
from cmem_plugin_base.dataintegration.types import Autocompletion, StringParameterType
from cmem_plugin_base.dataintegration.utils import setup_cmempy_user_access


class ResourceParameterType(StringParameterType):
    """Resource parameter type."""

    allow_only_autocompleted_values: bool = True

    autocomplete_value_with_labels: bool = True

    def autocomplete(
        self,
        query_terms: list[str],
        depend_on_parameter_values: list[Any],
        context: PluginContext,
    ) -> list[Autocompletion]:
        """Autocompletion request - Returns all results that match ALL provided query terms."""
        setup_cmempy_user_access(context.user)
        resources = get_resources(context.project_id)
        result = [
            Autocompletion(
                value=f"{_['fullPath']}",
                label=f"{_['name']}",
            )
            for _ in resources
        ]
        if query_terms:
            result = [_ for _ in result if _.value.find(query_terms[0]) > -1]

        if not result and query_terms:
            result = [
                Autocompletion(value=f"{query_terms[0]}", label=f"{query_terms[0]} (New resource)")
            ]

        return result
