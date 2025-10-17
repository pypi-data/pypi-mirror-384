import re

from bs4 import Tag

from labels.model.ecosystem_data.java import JavaArchive
from labels.parsers.cataloger.java.utils.maven_repo_utils import (
    recursively_find_versions_from_parent_pom,
)
from labels.parsers.cataloger.java.utils.model import PomContext


def resolve_version(
    dependency: Tag,
    pom_context: PomContext,
    java_archive: JavaArchive,
    full_name: str,
) -> str | None:
    version = dependency.version.get_text() if dependency.version else None

    if version and version.startswith("${"):
        version = _resolve_property_version(
            version, pom_context.project, pom_context.parent_version_properties
        )

    if not version and pom_context.parent_info:
        version = _resolve_parent_version(java_archive, pom_context.parent_info)

    if not version and pom_context.manage_deps and pom_context.parent_version_properties:
        version = _resolve_managed_version(
            pom_context.manage_deps,
            pom_context.parent_version_properties,
            full_name,
        )

    return version


def _resolve_property_version(
    version: str,
    project: Tag,
    parent_version_properties: dict[str, str] | None,
) -> str | None:
    property_name = _extract_bracketed_text(version)

    property_node = project.find_next(property_name)
    if property_node:
        version_text = property_node.get_text()
        if version_text and not version_text.startswith("${"):
            return version_text

    if parent_version_properties:
        return parent_version_properties.get(property_name)

    return None


def _resolve_parent_version(java_archive: JavaArchive, parent_info: dict[str, str]) -> str | None:
    if (
        java_archive.pom_properties
        and java_archive.pom_properties.group_id
        and java_archive.pom_properties.artifact_id
    ):
        return recursively_find_versions_from_parent_pom(
            group_id=java_archive.pom_properties.group_id,
            artifact_id=java_archive.pom_properties.artifact_id,
            parent_group_id=parent_info["group"],
            parent_artifact_id=parent_info["artifact"],
            parent_version=parent_info["version"],
        )

    return None


def _resolve_managed_version(
    manage_deps: dict[str, str],
    parent_version_properties: dict[str, str],
    full_name: str,
) -> str | None:
    managed_version = manage_deps.get(full_name)
    if managed_version:
        if not managed_version.startswith("${"):
            return managed_version

        return parent_version_properties.get(_extract_bracketed_text(managed_version))

    return None


def _extract_bracketed_text(item: str) -> str:
    match = re.search(r"\$\{([^}]+)\}", item)
    if match:
        return match.group(1)

    return ""
