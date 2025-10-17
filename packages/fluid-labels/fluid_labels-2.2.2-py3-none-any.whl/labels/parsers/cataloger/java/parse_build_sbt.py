import re
from typing import NamedTuple

from labels.model.ecosystem_data.java import JavaArchive, JavaPomProject
from labels.model.file import (
    Location,
    LocationReadCloser,
)
from labels.model.package import Package
from labels.model.relationship import (
    Relationship,
)
from labels.model.release import Environment
from labels.model.resolver import (
    Resolver,
)
from labels.parsers.cataloger.java.utils.package_builder import JavaPackageSpec, new_java_package
from labels.parsers.cataloger.utils import get_enriched_location

QUOTE = r'["\']'
NL = r"(\n?\s*)?"
TEXT = r'[^"\']+'
SBT_DEPENDENCY_RE = re.compile(
    r"^[^%]*"
    rf"{NL}{QUOTE}(?P<group>{TEXT}){QUOTE}{NL}%"
    rf"{NL}{QUOTE}(?P<name>{TEXT}){QUOTE}{NL}%"
    rf"{NL}{QUOTE}(?P<version>{TEXT}){QUOTE}{NL}"
    r".*$",
)

VERSION_VAR_RE = re.compile(
    rf"^\s*val\s+(?P<var_name>\w+)(?:\s*:\s*\w+)?\s*=\s*{QUOTE}(?P<value>{TEXT}){QUOTE}\s*$",
)

VERSION_REF_RE = re.compile(
    rf"{QUOTE}(?P<group>{TEXT}){QUOTE}\s*%%?\s*{QUOTE}(?P<name>{TEXT}){QUOTE}\s*%\s*(?P<version_var>\w+)",
)


class SbtDependency(NamedTuple):
    group: str
    name: str
    version: str
    line_no: int


def parse_build_sbt(
    _resolver: Resolver | None,
    _environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    file_content = reader.read_closer.read()
    if not file_content:
        return packages, relationships

    sbt_dependencies = _parse_dependencies(file_content)
    packages = _collect_packages(sbt_dependencies, reader.location)

    return packages, relationships


def _collect_packages(sbt_dependencies: list[SbtDependency], location: Location) -> list[Package]:
    packages: list[Package] = []

    for dependency in sbt_dependencies:
        product = f"{dependency.group}:{dependency.name}"

        new_location = get_enriched_location(location, line=dependency.line_no, is_transitive=False)

        ecosystem_data = JavaArchive(
            pom_project=JavaPomProject(
                name=product,
                group_id=dependency.group,
                artifact_id=dependency.name,
                version=dependency.version,
            )
        )

        package_spec = JavaPackageSpec(
            simple_name=dependency.name,
            version=dependency.version,
            location=new_location,
            ecosystem_data=ecosystem_data,
            composed_name=product,
        )

        package = new_java_package(package_spec)
        if package:
            packages.append(package)

    return packages


def _extract_version_vars(content: list[str]) -> dict[str, str]:
    version_vars = {}

    for line in content:
        if match := VERSION_VAR_RE.match(line):
            version_vars[match.group("var_name")] = match.group("value")

    return version_vars


def _parse_dependencies(content: str) -> list[SbtDependency]:
    dependencies: list[SbtDependency] = []

    content_lines = content.splitlines()
    version_vars = _extract_version_vars(content_lines)

    for line_no, line in enumerate(content_lines, start=1):
        if match := SBT_DEPENDENCY_RE.match(line):
            version = match.group("version")
            dependencies.append(
                SbtDependency(
                    group=match.group("group"),
                    name=match.group("name"),
                    version=version,
                    line_no=line_no,
                )
            )
        elif match := VERSION_REF_RE.search(line):
            version_var = match.group("version_var")
            version = version_vars.get(version_var, "unknown")
            dependencies.append(
                SbtDependency(
                    group=match.group("group"),
                    name=match.group("name"),
                    version=version,
                    line_no=line_no,
                )
            )

    return dependencies
