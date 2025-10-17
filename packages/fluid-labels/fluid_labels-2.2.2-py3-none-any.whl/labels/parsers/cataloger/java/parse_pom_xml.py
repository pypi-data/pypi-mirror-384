from pathlib import Path
from typing import NamedTuple, TextIO

from bs4 import BeautifulSoup, Tag

from labels.model.ecosystem_data.java import JavaArchive, JavaPomProperties
from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.java.utils.maven_repo_utils import (
    get_direct_child_text,
    get_next_text,
)
from labels.parsers.cataloger.java.utils.model import PomContext
from labels.parsers.cataloger.java.utils.package_builder import JavaPackageSpec, new_java_package
from labels.parsers.cataloger.java.utils.version_resolver import resolve_version
from labels.parsers.cataloger.utils import get_enriched_location


class PomEvaluationContext(NamedTuple):
    resolver: Resolver
    parent_info: dict[str, str]
    current_project: Tag
    current_pom_path: str


def parse_pom_xml(
    resolver: Resolver | None,
    _environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    pom_tree = _safe_parse_pom_xml(reader)
    if not pom_tree:
        return packages, relationships

    pom_context = _build_pom_context(pom_tree, reader, resolver)
    if not pom_context:
        return packages, relationships

    packages = _collect_packages(pom_context, reader.location)

    return packages, relationships


def _safe_parse_pom_xml(reader: LocationReadCloser) -> BeautifulSoup | None:
    try:
        return BeautifulSoup(reader.read_closer, features="html.parser")
    except (AssertionError, UnicodeError):
        return None


def _build_pom_context(
    pom_tree: BeautifulSoup,
    reader: LocationReadCloser,
    resolver: Resolver | None,
) -> PomContext | None:
    valid_project_and_dependencies = _get_valid_project_and_dependencies(pom_tree)
    if not valid_project_and_dependencies:
        return None

    project, dependencies = valid_project_and_dependencies

    parent_info = _get_parent_info(project)

    if resolver and parent_info:
        evaluation_context = PomEvaluationContext(
            resolver=resolver,
            parent_info=parent_info,
            current_project=project,
            current_pom_path=str(reader.location.access_path),
        )
        parent_version_properties, manage_deps = _evaluate_pom_files_in_project(evaluation_context)
    else:
        parent_version_properties = _get_properties(pom_tree)
        manage_deps = _get_deps_management(pom_tree)

    return PomContext(
        project=project,
        dependencies=dependencies,
        parent_info=parent_info,
        parent_version_properties=parent_version_properties,
        manage_deps=manage_deps,
    )


def _get_valid_project_and_dependencies(pom_tree: BeautifulSoup) -> tuple[Tag, Tag] | None:
    project = getattr(pom_tree, "project", None)
    if not project:
        return None

    if str(project.get("xmlns")) != "http://maven.apache.org/POM/4.0.0":
        return None

    dependencies = project.find("dependencies", recursive=False)
    if not isinstance(dependencies, Tag):
        return None

    return project, dependencies


def _get_parent_info(project: Tag) -> dict[str, str] | None:
    parent = project.find_next("parent")
    if not parent:
        return None

    group_node = get_next_text(parent, "groupid")
    artifact_node = get_next_text(parent, "artifactid")
    version_node = get_next_text(parent, "version")

    if not (group_node and artifact_node and version_node):
        return None

    return {
        "group": group_node,
        "artifact": artifact_node,
        "version": version_node,
    }


def _evaluate_pom_files_in_project(
    context: PomEvaluationContext,
) -> tuple[dict[str, str], dict[str, str]]:
    parent_pom = _find_parent_pom(context)
    properties_vars = _get_properties(parent_pom) if parent_pom else {}
    manage_deps = _get_deps_management(parent_pom) if parent_pom else {}

    manage_deps.update(_get_deps_management(context.current_project))

    return properties_vars, manage_deps


def _find_parent_pom(context: PomEvaluationContext) -> Tag | None:
    for loc in context.resolver.files_by_glob("**/pom.xml", "pom.xml"):
        content = context.resolver.file_contents_by_location(loc)
        if not content:
            continue

        pom_project = get_pom_project(content)
        if not pom_project:
            continue

        if _is_parent_pom(pom_project, context.parent_info) and _is_module_parent(
            pom_project, context.current_pom_path
        ):
            return pom_project

    return None


def get_pom_project(content: TextIO) -> Tag | None:
    root = BeautifulSoup(content, features="html.parser")
    pom_project = getattr(root, "project", None)

    if pom_project and str(pom_project.get("xmlns")) == "http://maven.apache.org/POM/4.0.0":
        return pom_project

    return None


def _is_parent_pom(root_pom_project: Tag, parent_info: dict[str, str]) -> bool:
    group = root_pom_project.find("groupid", recursive=False)
    artifact = root_pom_project.find("artifactid", recursive=False)
    version = root_pom_project.find("version", recursive=False)

    if not (group and artifact and version):
        return False

    return (
        group.get_text() == parent_info["group"]
        and artifact.get_text() == parent_info["artifact"]
        and version.get_text() == parent_info["version"]
    )


def _is_module_parent(parent_pom: Tag, pom_module: str) -> bool:
    base_module_name = Path(pom_module).parent.name

    for modules_section in parent_pom.find_all("modules"):
        for module_tag in modules_section.find_all("module"):
            if module_tag.get_text() == base_module_name:
                return True

    return False


def _get_properties(project_pom: Tag) -> dict[str, str]:
    properties_dict: dict[str, str] = {}

    for properties_section in project_pom.find_all("properties", limit=2):
        for prop in properties_section.children:
            if isinstance(prop, Tag) and prop.name:
                properties_dict[prop.name.lower()] = prop.get_text()

    return properties_dict


def _get_deps_management(pom_tree: Tag) -> dict[str, str]:
    deps_info: dict[str, str] = {}

    for manage in pom_tree.find_all("dependencymanagement"):
        for dependency in manage.find_all("dependency", recursive=True):
            if not (dependency.groupid and dependency.artifactid and dependency.version):
                continue

            group = dependency.groupid.get_text()
            artifact = dependency.artifactid.get_text()
            version = dependency.version.get_text()
            key = f"{group}:{artifact}"
            deps_info[key] = version

    return deps_info


def _collect_packages(pom_context: PomContext, location: Location) -> list[Package]:
    packages: list[Package] = []

    for dependency in pom_context.dependencies.find_all("dependency"):
        package_spec = _build_package_spec(pom_context, dependency, location)
        if not package_spec:
            continue

        package = new_java_package(package_spec)
        if package:
            packages.append(package)

    return packages


def _build_package_spec(
    pom_context: PomContext, dependency: Tag, location: Location
) -> JavaPackageSpec | None:
    name = get_direct_child_text(dependency, "artifactid")
    if not name:
        return None

    group_id = get_direct_child_text(dependency, "groupid")
    full_name = f"{group_id}:{name}" if group_id else name

    java_archive = JavaArchive(
        pom_properties=JavaPomProperties(
            group_id=group_id,
            artifact_id=name,
            version=get_direct_child_text(dependency, "version"),
        ),
    )

    version = resolve_version(dependency, pom_context, java_archive, full_name)
    if not _is_valid_version(version):
        return None

    scope = get_direct_child_text(dependency, "scope")
    is_dev = scope in ["test", "provided"]

    new_location = get_enriched_location(
        location,
        line=dependency.version.sourceline if dependency.version else dependency.sourceline,
        is_transitive=False,
        is_dev=is_dev,
    )

    return JavaPackageSpec(
        composed_name=full_name,
        simple_name=name,
        version=str(version),
        location=new_location,
        ecosystem_data=java_archive,
    )


def _is_valid_version(version: str | None) -> bool:
    return version is not None and not version.startswith("${")
