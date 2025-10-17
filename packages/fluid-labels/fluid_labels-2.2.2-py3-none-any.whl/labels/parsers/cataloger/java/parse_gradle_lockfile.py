from pydantic import BaseModel

from labels.model.ecosystem_data.java import JavaArchive, JavaPomProject
from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.java.utils.package_builder import JavaPackageSpec, new_java_package
from labels.parsers.cataloger.utils import get_enriched_location


class LockFileDependency(BaseModel):
    group: str
    name: str
    version: str
    line: int | None = None


def parse_gradle_lockfile(
    _resolver: Resolver | None,
    _environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    file_content = reader.read_closer.read()
    if not file_content:
        return packages, relationships

    lockfile_dependencies = _parse_dependencies(file_content)
    packages = _collect_packages(lockfile_dependencies, reader.location)

    return packages, relationships


def _parse_dependencies(file_content: str) -> list[LockFileDependency]:
    dependencies: list[LockFileDependency] = []

    content_lines = file_content.splitlines()

    for line_number, line in enumerate(content_lines, 1):
        if _is_dependency_line(line):
            dependency_part = line.split("=")[0]
            group, name, version = dependency_part.split(":")
            dependencies.append(
                LockFileDependency(group=group, name=name, version=version, line=line_number),
            )

    return dependencies


def _collect_packages(
    lockfile_dependencies: list[LockFileDependency], location: Location
) -> list[Package]:
    packages: list[Package] = []

    for dependency in lockfile_dependencies:
        name = dependency.name
        composed_name = f"{dependency.group}:{name}"

        version = dependency.version

        new_location = get_enriched_location(location, line=dependency.line)

        archive = JavaArchive(
            pom_project=JavaPomProject(
                group_id=dependency.group,
                name=name,
                artifact_id=name,
                version=version,
            ),
        )

        package_spec = JavaPackageSpec(
            simple_name=name,
            version=version,
            location=new_location,
            ecosystem_data=archive,
            composed_name=composed_name,
        )

        package = new_java_package(package_spec)
        if package:
            packages.append(package)

    return packages


def _is_dependency_line(line: str) -> bool:
    return "=" in line and ":" in line
