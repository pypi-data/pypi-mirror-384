from pathlib import Path
from typing import NamedTuple

from bs4 import BeautifulSoup, Tag

from labels.model.ecosystem_data.java import JavaPomParent, JavaPomProject
from labels.model.file import Location
from labels.parsers.cataloger.java.utils.maven_repo_utils import get_next_text
from labels.utils.zip import contents_from_zip


class ParsedPomProject(NamedTuple):
    java_pom_project: JavaPomProject
    licenses: list[str]


def parse_pom_xml_project(
    reader: str,
    _location: Location,
) -> ParsedPomProject | None:
    project = BeautifulSoup(reader, features="xml").project
    if not project:
        return None
    return new_pom_project(project, _location)


def _find_direct_child(parent: Tag, tag: str) -> Tag | None:
    return next(
        (child for child in parent.find_all(tag, recursive=False) if child.parent == parent),
        None,
    )


def new_pom_project(
    project: Tag,
    _location: Location,
) -> ParsedPomProject:
    artifact_id = _safe_string(_find_direct_child(project, "artifactId"))
    name = _safe_string(_find_direct_child(project, "name"))

    licenses: list[str] = []
    if project.licenses:
        for license_ in project.licenses.find_all("license"):
            license_name: str | None = None
            license_url: str | None = None
            if name_node := license_.find_next("name"):
                license_name = name_node.get_text()
            elif url_node := license_.find_next("url"):
                license_url = url_node.get_text()

            if not license_name and not license_url:
                continue

            license_value = license_name or license_url

            if license_value is not None:
                licenses.append(license_value)

    return ParsedPomProject(
        java_pom_project=JavaPomProject(
            parent=pom_parent(_find_direct_child(project, "parent")),
            group_id=_safe_string(_find_direct_child(project, "groupId")),
            artifact_id=artifact_id,
            version=_safe_string(_find_direct_child(project, "version")),
            name=name,
        ),
        licenses=licenses,
    )


def _safe_string(value: Tag | None) -> str:
    if not value:
        return ""
    return value.get_text()


def pom_parent(parent: Tag | None) -> JavaPomParent | None:
    if not parent:
        return None

    group_id = get_next_text(parent, "groupId")
    artifact_id = get_next_text(parent, "artifactId")
    version = get_next_text(parent, "version")

    if (
        not group_id
        or not artifact_id
        or not version
        or not group_id.strip()
        or not artifact_id.strip()
        or not version.strip()
    ):
        return None

    return JavaPomParent(
        group_id=group_id,
        artifact_id=artifact_id,
        version=version,
    )


def pom_project_by_parent(
    archive_path: str,
    location: Location,
    extract_paths: list[str],
) -> dict[str, ParsedPomProject]:
    contents_of_maven_project = contents_from_zip(archive_path, *extract_paths)

    project_by_parent = {}

    for file_path, file_contents in contents_of_maven_project.items():
        pom_project = parse_pom_xml_project(file_contents, location)
        if not pom_project:
            continue
        if (
            not pom_project.java_pom_project.parent and not pom_project.java_pom_project.version
        ) or not pom_project.java_pom_project.artifact_id:
            continue

        project_by_parent[str(Path(file_path).parent)] = pom_project

    return project_by_parent
