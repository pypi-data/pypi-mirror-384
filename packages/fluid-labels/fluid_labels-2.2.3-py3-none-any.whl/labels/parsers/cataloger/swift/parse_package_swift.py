from labels.model.file import LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.graph_parser import Graph, NId, adj, node_to_str, parse_ast_graph
from labels.parsers.cataloger.swift.package_builder import new_swift_package_manager_package
from labels.parsers.cataloger.utils import get_enriched_location


def parse_package_swift(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    content = reader.read_closer.read().encode("utf-8")
    dependencies = None
    if not content or not (graph := parse_ast_graph(content, "swift")):
        return ([], [])
    for node in graph.nodes:
        if (
            graph.nodes[node].get("label_type") == "call_expression"
            and (children := adj(graph, node))
            and len(children) == 2
            and graph.nodes[children[0]].get("label_text") == "Package"
        ):
            for child in adj(graph, children[1], depth=2):
                if (
                    graph.nodes[child].get("label_type") == "value_argument"
                    and (name_id := graph.nodes[child].get("label_field_name"))
                    and (name_value_id := adj(graph, name_id)[0])
                    and graph.nodes[name_value_id].get("label_text") == "dependencies"
                ):
                    dependencies = graph.nodes[child]["label_field_value"]
                    break
    if dependencies is None:
        return ([], [])
    return _get_dependencies(dependencies, graph, reader)


def _get_dependencies(
    dep_node: NId,
    graph: Graph,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    for package_node in adj(graph, dep_node, depth=2):
        if _is_valid_package_node(graph, package_node):
            source_url, package_version = _extract_package_details(graph, package_node)

            new_location = get_enriched_location(
                reader.location, line=graph.nodes[package_node]["label_l"]
            )

            package = new_swift_package_manager_package(
                source_url=source_url, version=package_version, location=new_location
            )

            if package:
                packages.append(package)

    return packages, relationships


def _is_valid_package_node(graph: Graph, package_node: NId) -> bool:
    return bool(
        graph.nodes[package_node]["label_type"] == "call_expression"
        and (child_value := adj(graph, package_node)[0])
        and node_to_str(graph, child_value) != ".package(",
    )


def _extract_package_details(
    graph: Graph,
    package_node: NId,
) -> tuple[str | None, str | None]:
    package_version = None
    source_url = None

    for argument_node in adj(graph, package_node, 3):
        if graph.nodes[argument_node].get("label_type") != "value_argument" or not (
            name_id := graph.nodes[argument_node].get("label_field_name")
        ):
            continue

        argument_name = node_to_str(graph, name_id)
        if argument_name == "url":
            source_url = node_to_str(graph, graph.nodes[argument_node]["label_field_value"])
        elif argument_name in {"from", "version"}:
            package_version = (
                node_to_str(graph, graph.nodes[argument_node]["label_field_value"])
                .replace('"', "")
                .replace("'", "")
            )

    return source_url, package_version
