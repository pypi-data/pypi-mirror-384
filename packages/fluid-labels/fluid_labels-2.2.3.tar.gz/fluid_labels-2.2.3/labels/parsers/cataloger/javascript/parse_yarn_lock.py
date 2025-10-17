import re
from typing import NamedTuple, NotRequired, TypedDict

from labels.model.file import LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship, RelationshipType
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.javascript.package_builder import new_simple_npm_package
from labels.parsers.cataloger.utils import get_enriched_location


class YarnPackage(TypedDict):
    line: int
    version: str
    checksum: NotRequired[str]
    dependencies: NotRequired[list[tuple[str, str]]]
    integrity: NotRequired[str]
    resolution: NotRequired[str]
    resolved: NotRequired[str]


class PackageKey(NamedTuple):
    name: str
    version: str


class ParserState(NamedTuple):
    parsed_yarn_lock: dict[PackageKey, YarnPackage]
    current_package: str | None = None
    current_package_line: int | None = None
    current_package_version: str | None = None
    current_indentation: int | None = None
    current_key: str | None = None
    package_key: PackageKey | None = None


def parse_yarn_lock(
    _resolver: Resolver | None,
    _environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    parsed_yarn_lock = _parse_yarn_file(reader.read_closer.read())
    packages = _extract_packages(parsed_yarn_lock, reader)
    relationships = _extract_relationships(parsed_yarn_lock, packages)
    return packages, relationships


def _parse_yarn_file(yarn_lock_content: str) -> dict[PackageKey, YarnPackage]:
    yarn_lock_lines = yarn_lock_content.strip().split("\n")
    initial_state = ParserState(parsed_yarn_lock={})

    final_state = _process_lines(yarn_lock_lines, initial_state)
    return final_state.parsed_yarn_lock


def _process_lines(lines: list[str], state: ParserState) -> ParserState:
    for index, line in enumerate(lines, 1):
        state = _process_line(line, index, state)
    return state


def _process_line(line: str, index: int, state: ParserState) -> ParserState:
    if not line:
        return state._replace(current_indentation=None)

    if line.startswith("#"):
        return state

    if not line.startswith(" "):
        return _handle_package_header(line, index, state)

    return _process_indented_line(line, state)


def _process_indented_line(line: str, state: ParserState) -> ParserState:
    if state.current_package and state.current_package_line and line.strip().startswith("version"):
        return _handle_version_line(line, state)

    if _is_start_of_list_line(state, line):
        return _handle_list_start(line, state)

    if _is_list_item_line(state, line):
        return _handle_list_item(line, state)

    if state.package_key:
        return _handle_property(line, state)

    return state


def _handle_package_header(line: str, index: int, state: ParserState) -> ParserState:
    current_package, current_package_line = _parse_current_package(line, index)
    return state._replace(
        current_package=current_package,
        current_package_line=current_package_line,
        current_package_version=None,
        package_key=None,
    )


def _handle_version_line(line: str, state: ParserState) -> ParserState:
    if not state.current_package or not state.current_package_line:
        return state

    _, raw_version = _resolve_pair(line)
    version = raw_version.strip('"')
    package_key = PackageKey(name=state.current_package, version=version)

    new_package: YarnPackage = {"line": state.current_package_line, "version": version}
    new_parsed_lock = {**state.parsed_yarn_lock, package_key: new_package}

    return state._replace(
        parsed_yarn_lock=new_parsed_lock,
        current_package_version=version,
        package_key=package_key,
    )


def _handle_list_start(line: str, state: ParserState) -> ParserState:
    if not state.package_key:
        return state

    indentation = _count_indentation(line)
    key = line.strip().split(":")[0]

    if key != "dependencies":
        return state._replace(current_indentation=None, current_key=None)

    updated_package: YarnPackage = {
        **state.parsed_yarn_lock[state.package_key],
        "dependencies": [],
    }
    new_parsed_lock = {**state.parsed_yarn_lock, state.package_key: updated_package}

    return state._replace(
        parsed_yarn_lock=new_parsed_lock,
        current_indentation=indentation,
        current_key=key,
    )


def _handle_list_item(line: str, state: ParserState) -> ParserState:
    if not state.package_key:
        return state

    current_deps = state.parsed_yarn_lock[state.package_key].get("dependencies", [])
    new_deps = [*current_deps, _resolve_pair(line)]

    updated_package: YarnPackage = {
        **state.parsed_yarn_lock[state.package_key],
        "dependencies": new_deps,
    }
    new_parsed_lock = {**state.parsed_yarn_lock, state.package_key: updated_package}

    return state._replace(parsed_yarn_lock=new_parsed_lock)


def _handle_property(line: str, state: ParserState) -> ParserState:
    if not state.package_key:
        return state

    key, value = _resolve_pair(line)
    if key not in ("checksum", "integrity", "resolution", "resolved"):
        return state._replace(current_indentation=None)

    existing_package = state.parsed_yarn_lock[state.package_key]
    updated_package: YarnPackage = {**existing_package, key: value.strip('"')}  # type: ignore[misc]
    new_parsed_lock = {**state.parsed_yarn_lock, state.package_key: updated_package}

    return state._replace(parsed_yarn_lock=new_parsed_lock, current_indentation=None)


def _extract_packages(
    parsed_yarn_lock: dict[PackageKey, YarnPackage],
    reader: LocationReadCloser,
) -> list[Package]:
    packages = []
    for pkg_info, item in parsed_yarn_lock.items():
        name = _get_name(pkg_info, item)
        version = item.get("version")

        new_location = get_enriched_location(reader.location, line=item["line"])

        package = new_simple_npm_package(new_location, name, version)
        if package:
            packages.append(package)

    return packages


def _extract_relationships(
    parsed_yarn_lock: dict[PackageKey, YarnPackage],
    packages: list[Package],
) -> list[Relationship]:
    relationships = []
    for pkg_info, item in parsed_yarn_lock.items():
        current_pkg = next(
            (package for package in packages if package.name == _get_name(pkg_info, item)),
            None,
        )

        if current_pkg is None:
            continue

        if "dependencies" in item:
            for raw_dep_name, _ in item["dependencies"]:
                dep_name = raw_dep_name.strip('"')
                # TO-DO: check if the version matches
                if dep := next(
                    (package for package in packages if package.name == dep_name),
                    None,
                ):
                    relationships.append(
                        Relationship(
                            from_=dep.id_,
                            to_=current_pkg.id_,
                            type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
                        ),
                    )
    return relationships


def _get_name(pkg_info: PackageKey, item: YarnPackage) -> str:
    if resolution := item.get("resolution"):
        is_scoped_package = resolution.startswith("@")
        if is_scoped_package:
            return f"@{resolution.split('@')[1]}"
        return resolution.split("@")[0]

    return pkg_info.name


def _parse_current_package(line: str, index: int) -> tuple[str | None, int | None]:
    line = line.strip()
    if match_ := re.match(r'^"?((?:@\w[\w\-\.]*/)?\w[\w\-\.]*)@', line):
        current_package = match_.groups()[0]
        current_package_line = index
    else:
        current_package = None
        current_package_line = None

    return current_package, current_package_line


def _resolve_pair(line: str) -> tuple[str, str]:
    line = line.strip()
    if ": " in line:
        key, value = line.split(": ")
        return key.strip(), value.strip()

    key, value = line.split(" ", maxsplit=1)
    return key.strip(), value.strip()


def _count_indentation(line: str) -> int:
    # Stripping the leading spaces and comparing the length difference
    return len(line) - len(line.lstrip(" "))


def _is_start_of_list_line(state: ParserState, line: str) -> bool:
    return bool(
        state.current_package and state.current_package_version and line.strip().endswith(":"),
    )


def _is_list_item_line(state: ParserState, line: str) -> bool:
    return bool(
        state.current_package
        and state.current_package_version
        and state.current_key
        and state.current_indentation
        and _count_indentation(line) > state.current_indentation,
    )
