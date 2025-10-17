from packageurl import PackageURL

from labels.model.ecosystem_data.java import (
    JavaArchive,
    JavaManifest,
    JavaPomProject,
    JavaPomProperties,
)
from labels.parsers.cataloger.java.utils.group_id_pkg_list import group_id_from_known_package_list


def looks_like_group_id(group_id: str) -> bool:
    return "." in group_id


def remove_osgi_directives(group_id: str) -> str:
    return group_id.split(";")[0]


def clean_group_id(group_id: str) -> str:
    return remove_osgi_directives(group_id).strip()


def group_id_from_pom_properties(properties: JavaPomProperties | None) -> str:
    if not properties:
        return ""
    if properties.group_id:
        return clean_group_id(properties.group_id)
    if properties.artifact_id and looks_like_group_id(properties.artifact_id):
        return clean_group_id(properties.artifact_id)
    return ""


def group_id_pom_project(project: JavaPomProject | None) -> str:
    if not project:
        return ""
    if project.group_id:
        return clean_group_id(project.group_id)
    if project.artifact_id and looks_like_group_id(project.artifact_id):
        return clean_group_id(project.artifact_id)
    if project.parent:
        if project.parent.group_id:
            return clean_group_id(project.parent.group_id)
        if looks_like_group_id(project.parent.artifact_id):
            return clean_group_id(project.parent.artifact_id)
    return ""


def _starts_with_top_level_domain(value: str) -> bool:
    domains = ["com", "org", "net", "io", "be"]
    return any(value.startswith(domain + ".") for domain in domains)


def _check_manifest_fields(manifest: JavaManifest, fields: list[str]) -> list[str]:
    group_ids = []
    for field in fields:
        if (value := manifest.main.get(field, "")) and _starts_with_top_level_domain(value):
            group_ids.append(clean_group_id(value))
        if manifest.sections:
            section_values = [
                clean_group_id(value)
                for section in manifest.sections
                if (value := section.get(field, "")) and _starts_with_top_level_domain(value)
            ]
            group_ids.extend(section_values)
    return group_ids


def group_id_from_java_manifest(manifest: JavaManifest | None) -> str:
    if not manifest or not manifest.main:
        return ""

    primary_fields = [
        "Group-Id",
        "Bundle-SymbolicName",
        "Extension-Name",
        "Specification-Vendor",
        "Implementation-Vendor",
        "Implementation-Vendor-Id",
        "Implementation-Title",
        "Bundle-Activator",
    ]

    group_ids = _check_manifest_fields(manifest, primary_fields)
    if group_ids:
        return group_ids[0]

    secondary_fields = ["Automatic-Module-Name", "Main-Class", "Package"]
    group_ids = _check_manifest_fields(manifest, secondary_fields)
    return group_ids[0] if group_ids else ""


def group_id_from_java_metadata(pkg_name: str | None, metadata: JavaArchive | None) -> str | None:
    if not metadata or not pkg_name:
        return None

    # 1. Group ID from POM properties
    if group_id := group_id_from_pom_properties(metadata.pom_properties):
        return group_id

    # 2. Group ID from POM project
    if group_id := group_id_pom_project(metadata.pom_project):
        return group_id

    # 3. Group ID from known package list
    if group_id := group_id_from_known_package_list(pkg_name):
        return group_id

    # 4. Group ID from Java manifest
    if group_id := group_id_from_java_manifest(metadata.manifest):
        return group_id

    return None


def package_url(name: str, version: str, metadata: JavaArchive | None = None) -> str:
    group_id = name
    if (g_id := group_id_from_java_metadata(name, metadata)) and g_id:
        group_id = g_id
    return PackageURL(
        type="maven",
        namespace=group_id,
        name=name,
        version=version,
        qualifiers=None,
        subpath="",
    ).to_string()
