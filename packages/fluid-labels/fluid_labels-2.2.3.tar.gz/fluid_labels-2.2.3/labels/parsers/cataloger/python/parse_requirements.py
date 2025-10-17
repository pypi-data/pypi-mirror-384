from collections.abc import Generator
from contextlib import suppress
from typing import NamedTuple

import requirements

from labels.model.file import LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.python.package_builder import new_python_package
from labels.parsers.cataloger.utils import get_enriched_location

OPERATOR_ORDER = {"==": 1, "===": 1, "~=": 1, ">=": 2, ">": 2, "<": 3, "<=": 3}


class PythonRequirementsData(NamedTuple):
    name: str
    version: str
    is_dev: bool


def parse_requirements_txt(
    _resolver: Resolver | None,
    _env: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []
    deps_found = False

    try:
        content = reader.read_closer.read()
    except UnicodeDecodeError:
        return packages, relationships

    for line_number, line in _split_lines_requirements(content):
        parsed_dependency_data = _get_parsed_dependency(line)

        if not parsed_dependency_data:
            if not deps_found and line_number > 3:
                return packages, relationships
            continue

        deps_found = True
        new_location = get_enriched_location(
            reader.location,
            line=line_number,
            is_dev=parsed_dependency_data.is_dev,
            is_transitive=False,
        )

        package = new_python_package(
            name=parsed_dependency_data.name,
            version=parsed_dependency_data.version,
            location=new_location,
        )
        if package:  # pragma: no cover
            packages.append(package)

    return packages, relationships


def _split_lines_requirements(
    content: str,
) -> Generator[tuple[int, str], None, None]:
    last_line = ""
    line_number = 1
    for index, raw_line in enumerate(content.splitlines(), 1):
        if not last_line:
            line_number = index
        line = _trim_requirements_txt_line(raw_line)
        if last_line != "":
            line = last_line + line
            last_line = ""
        if line.endswith("\\"):
            last_line += line.rstrip("\\")
            continue
        if not line:
            continue

        if any(
            (
                line.startswith("-e"),
                line.startswith("-r"),
                line.startswith("--requirements"),
            ),
        ):
            continue

        yield line_number, line


def _trim_requirements_txt_line(line: str) -> str:
    line = line.strip()

    return _remove_trailing_comment(line)


def _remove_trailing_comment(line: str) -> str:
    parts = line.split("#", 1)
    if len(parts) < 2:
        # there aren't any comments
        return line
    return parts[0]


def _get_parsed_dependency(line: str) -> PythonRequirementsData | None:
    with suppress(Exception):
        parsed_dep = next(iter(requirements.parse(line)))
        if not parsed_dep.specs or not (version := _get_dep_version_range(parsed_dep.specs)):
            return None
        is_dev: bool = False
        if parsed_dep.extras and any("dev" in extra.lower() for extra in parsed_dep.extras):
            is_dev = True
        return PythonRequirementsData(name=str(parsed_dep.name), version=version, is_dev=is_dev)
    return None


def _get_dep_version_range(dep_specs: list[tuple[str, str]]) -> str | None:
    version_range = ""
    ordered_specs = sorted(dep_specs, key=lambda x: OPERATOR_ORDER.get(x[0], 1))
    for operator, version in ordered_specs:
        if operator not in OPERATOR_ORDER:
            return None

        if operator in {"==", "~="}:
            version_range = version
            break
        version_range += f"{operator}{version} "
    return version_range.rstrip()
