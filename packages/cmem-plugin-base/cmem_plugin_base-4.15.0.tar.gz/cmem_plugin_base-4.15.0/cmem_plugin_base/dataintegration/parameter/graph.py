"""Knowledge Graph Parameter Type."""

from typing import Any

from cmem.cmempy.dp.proxy.graph import get_graphs_list

from cmem_plugin_base.dataintegration.context import PluginContext
from cmem_plugin_base.dataintegration.types import Autocompletion, StringParameterType
from cmem_plugin_base.dataintegration.utils import setup_cmempy_user_access


class GraphParameterType(StringParameterType):
    """Knowledge Graph parameter type."""

    allow_only_autocompleted_values: bool = False

    autocomplete_value_with_labels: bool = True

    classes: set[str] | None = None

    def __init__(
        self,
        show_di_graphs: bool = False,
        show_system_graphs: bool = False,
        show_graphs_without_class: bool = False,
        classes: list[str] | None = None,
        allow_only_autocompleted_values: bool = True,
    ):
        """Knowledge Graph parameter type.

        :param show_di_graphs: show DI project graphs
        :param show_system_graphs: show system graphs such as shape and query catalogs
        :param classes: allowed classes of the shown graphs
            - if None -> defaults to di:Dataset, void:Dataset and shui:QueryCatalog
        :param allow_only_autocompleted_values: allow entering new graph URLs
        """
        self.show_di_graphs = show_di_graphs
        self.show_system_graphs = show_system_graphs
        self.show_graphs_without_class = show_graphs_without_class
        self.allow_only_autocompleted_values = allow_only_autocompleted_values
        if classes:
            self.classes = set(classes)
        else:
            self.classes = {
                "https://vocab.eccenca.com/di/Dataset",
                "http://rdfs.org/ns/void#Dataset",
                "https://vocab.eccenca.com/shui/QueryCatalog",
            }

    def autocomplete(
        self,
        query_terms: list[str],
        depend_on_parameter_values: list[Any],
        context: PluginContext,
    ) -> list[Autocompletion]:
        """Autocompletion request - Returns all results that match ALL provided query terms"""
        setup_cmempy_user_access(context=context.user)
        graphs = get_graphs_list()
        result = []
        for _ in graphs:
            iri = _["iri"]
            title = _["label"]["title"]
            label = f"{title} ({iri})"
            assigned_classes = set(_["assignedClasses"])
            # ignore DI project graphs
            if self.show_di_graphs is False and _["diProjectGraph"] is True:
                continue
            # ignore system resource graphs
            if self.show_system_graphs is False and _["systemResource"] is True:
                continue
            # show graphs without assigned classes only if explicitly wanted
            if len(assigned_classes) == 0:
                if self.show_graphs_without_class is True:
                    result.append(Autocompletion(value=iri, label=label))
                continue
            # ignore graphs which do not match the requested classes
            if (
                self.classes is not None
                and len(assigned_classes) > 0
                and len(self.classes.intersection(assigned_classes)) == 0
            ):
                continue
            # if no search terms are given: add all remaining graphs to list
            if len(query_terms) == 0:
                result.append(Autocompletion(value=iri, label=label))
                continue
            # show only graphs which match the given terms
            for term in query_terms:
                if term.lower() in label.lower():
                    result.append(Autocompletion(value=iri, label=label))
                    continue
        result.sort(key=lambda x: x.label)  # type: ignore[return-value, arg-type]
        return list(set(result))
