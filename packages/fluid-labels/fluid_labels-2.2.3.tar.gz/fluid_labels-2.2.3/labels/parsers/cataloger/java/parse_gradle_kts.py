import re
from typing import NamedTuple

from labels.model.ecosystem_data.java import JavaArchive, JavaPomProject
from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.java.utils.package_builder import JavaPackageSpec, new_java_package
from labels.parsers.cataloger.utils import get_enriched_location

QUOTE = r'["\']'
NL = r"(\n?\s*)?"
TEXT = r"[a-zA-Z0-9._-]+"

CONFIG_TO_DEV_STATUS = {
    "testRuntimeOnly": True,
    "testCompileOnly": True,
    "testImplementation": True,
    "compileOnly": True,
    "testCompile": True,
    "androidTestImplementation": True,
    "compile": False,
    "runtime": False,
    "implementation": False,
    "api": False,
    "runtimeOnly": False,
}


class GradleKtsDependency(NamedTuple):
    group: str
    name: str
    version: str
    config: str
    line: int | None = None


def parse_gradle_lockfile_kts(
    _resolver: Resolver | None,
    _environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    file_content = reader.read_closer.read()
    if not file_content:
        return packages, relationships

    gradle_dependencies = _parse_dependencies(file_content)

    packages = _collect_packages(gradle_dependencies, reader.location)

    return packages, relationships


def _parse_dependencies(file_content: str) -> list[GradleKtsDependency]:
    dependencies: list[GradleKtsDependency] = []
    is_block_comment = False

    for line_no, raw_line in enumerate(file_content.splitlines(), start=1):
        line = raw_line.strip()
        is_block_comment = _update_block_comment_status(line, is_block_comment=is_block_comment)

        if is_block_comment or _is_comment(line):
            continue

        dependency = _extract_dependency(line, line_no)
        if dependency:
            dependencies.append(dependency)

    return dependencies


def _update_block_comment_status(line: str, *, is_block_comment: bool) -> bool:
    if "/*" in line:
        return True
    if "*/" in line:
        return False
    return is_block_comment


def _is_comment(line: str) -> bool:
    return (
        line.strip().startswith("//")
        or line.strip().startswith("/*")
        or line.strip().endswith("*/")
    )


def _extract_dependency(line: str, line_no: int) -> GradleKtsDependency | None:
    regex = _build_regex_with_configs()

    if match := regex.match(line):
        version = match.group("version")
        config = match.group("config_name")
        if version:
            return GradleKtsDependency(
                group=match.group("group"),
                name=match.group("name"),
                version=version,
                config=config,
                line=line_no,
            )

    return None


def _build_regex_with_configs() -> re.Pattern[str]:
    configs = {
        "runtimeOnly",
        "api",
        "compile",
        "compileOnly",
        "implementation",
        "testRuntimeOnly",
        "testCompileOnly",
        "testImplementation",
        "runtime",
        "androidTestImplementation",
    }

    config_pattern = "|".join(configs)

    return re.compile(
        rf"(?P<config_name>{config_pattern})\({QUOTE}"
        rf"(?P<group>{TEXT}):(?P<name>{TEXT}):"
        rf"(?P<version>{TEXT})"
        rf"(?::(?P<classifier>{TEXT}))?"
        rf"{QUOTE}\)",
    )


def _collect_packages(
    dependencies: list[GradleKtsDependency],
    reader_location: Location,
) -> list[Package]:
    packages: list[Package] = []

    for dependency in dependencies:
        name = dependency.name
        version = dependency.version

        is_dev = CONFIG_TO_DEV_STATUS.get(dependency.config, None)

        new_location = get_enriched_location(reader_location, line=dependency.line, is_dev=is_dev)

        ecosystem_data = JavaArchive(
            pom_project=JavaPomProject(
                group_id=dependency.group,
                name=name,
                artifact_id=name,
                version=version,
            ),
        )

        package_spec = JavaPackageSpec(
            simple_name=name,
            composed_name=f"{dependency.group}:{name}",
            version=version,
            location=new_location,
            ecosystem_data=ecosystem_data,
        )

        package = new_java_package(package_spec)
        if package:
            packages.append(package)

    return packages
