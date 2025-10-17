import re
from typing import NamedTuple

from labels.model.file import Location, LocationReadCloser
from labels.model.indexables import IndexedDict, IndexedList, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship, RelationshipType
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.javascript.package_builder import new_simple_npm_package
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection.yaml import parse_yaml_with_tree_sitter

VERSION_PATTERN = re.compile(r"(\d+\.\d+\.\d+(-[0-9A-Za-z\.]+)?)")


class PnpmPackageCreationDetails(NamedTuple):
    package_key: str
    package_spec: IndexedDict[str, ParsedValue]
    package_yaml: IndexedDict[str, ParsedValue]
    direct_dependencies: list[ParsedValue]
    base_location: Location


class PnpmPackageInfo(NamedTuple):
    name: str
    key: str
    is_dev: bool
    dependencies: list[ParsedValue]


def parse_pnpm_lock(
    _: Resolver | None, __: Environment | None, reader: LocationReadCloser
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []
    package_yaml = parse_yaml_with_tree_sitter(reader.read_closer.read())

    if not isinstance(package_yaml, IndexedDict):
        return packages, relationships

    packages = _generate_packages(reader, package_yaml)
    relationships = _generate_relationships(package_yaml, packages)

    return packages, relationships


def _generate_packages(
    reader: LocationReadCloser, package_yaml: IndexedDict[str, ParsedValue]
) -> list[Package]:
    packages: list[Package] = []

    packages_items = package_yaml.get("packages")
    if not isinstance(packages_items, IndexedDict):
        return packages

    dependencies = package_yaml.get("dependencies")
    dev_dependencies = package_yaml.get("devDependencies")

    direct_dependencies: list[ParsedValue] = []
    if isinstance(dependencies, IndexedList) and isinstance(dev_dependencies, IndexedList):
        direct_dependencies = [*dev_dependencies, *dependencies]

    for package_key, pkg_spec in packages_items.items():
        if not isinstance(pkg_spec, IndexedDict):
            continue

        package_creation_details = PnpmPackageCreationDetails(
            package_key=package_key,
            package_spec=pkg_spec,
            package_yaml=package_yaml,
            direct_dependencies=direct_dependencies,
            base_location=reader.location,
        )

        package = _process_package(package_creation_details)
        if package:
            packages.append(package)

    return packages


def _process_package(creation_details: PnpmPackageCreationDetails) -> Package | None:
    name_version = _parse_package_key(creation_details.package_key, creation_details.package_spec)
    if name_version is None:
        return None

    package_name, package_version = name_version
    if not package_name or not package_version:
        return None

    is_dev = creation_details.package_spec.get("dev") is True

    package_info = PnpmPackageInfo(
        name=package_name,
        key=creation_details.package_key,
        dependencies=creation_details.direct_dependencies,
        is_dev=is_dev,
    )

    new_location = _manage_coordinates(
        creation_details.package_yaml, package_info, creation_details.base_location
    )

    return new_simple_npm_package(new_location, package_name, package_version)


def _parse_package_key(package: str, spec: IndexedDict[str, ParsedValue]) -> tuple[str, str] | None:
    if package.startswith("github"):
        pkg_name = spec.get("name")
        pkg_version = spec.get("version")
    else:
        pkg_info: list[str] = VERSION_PATTERN.split(package.strip("\"'"))
        if len(pkg_info) < 2:
            return None

        pkg_name = pkg_info[0].lstrip("/")[0:-1]
        pkg_version = pkg_info[1]

    if not isinstance(pkg_name, str) or not isinstance(pkg_version, str):
        return None

    return pkg_name, pkg_version


def _manage_coordinates(
    package_yaml: IndexedDict[str, ParsedValue],
    package_info: PnpmPackageInfo,
    base_location: Location,
) -> Location:
    packages = package_yaml.get("packages")
    if not isinstance(packages, IndexedDict):
        return base_location

    position = packages.get_key_position(package_info.key)
    is_transitive = package_info.name not in package_info.dependencies

    return get_enriched_location(
        base_location,
        line=position.start.line,
        is_transitive=is_transitive,
        is_dev=package_info.is_dev,
    )


def _generate_relationships(
    package_yaml: IndexedDict[str, ParsedValue],
    packages: list[Package],
) -> list[Relationship]:
    relationships: list[Relationship] = []
    packages_items = package_yaml.get("packages")
    if not isinstance(packages_items, IndexedDict):
        return relationships
    for package_key, package_value in packages_items.items():
        if not isinstance(package_value, IndexedDict):
            continue
        if match_ := re.search(r"/(@?[^@]+)@(\d+\.\d+\.\d+)", package_key):
            package_name = match_.groups()[0]
            package_version = match_.groups()[1]
            current_package = _get_package(
                packages,
                dep_name=package_name,
                dep_version=package_version,
            )
            dependencies = package_value.get("dependencies")
            if dependencies and isinstance(dependencies, IndexedDict):
                relationships.extend(
                    _process_relationships(dependencies, packages, current_package),
                )
    return relationships


def _process_relationships(
    dependencies: IndexedDict[str, ParsedValue],
    packages: list[Package],
    current_package: Package | None,
) -> list[Relationship]:
    relationships: list[Relationship] = []
    for raw_dep_name, raw_dep_version in dependencies.items():
        if not isinstance(raw_dep_version, str):
            continue

        dep_name = _extract_package_name_from_key_dependency(
            raw_dep_name,
        )
        dep_version = _extract_version_from_value_dependency(
            raw_dep_version,
        )

        dependency = _get_package(packages, dep_name, dep_version)
        if dependency and current_package:
            relationships.append(
                Relationship(
                    from_=dependency.id_,
                    to_=current_package.id_,
                    type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
                ),
            )

    return relationships


def _extract_package_name_from_key_dependency(item: str) -> str | None:
    # Regex pattern to extract the package name
    pattern = r"^@?[\w-]+/[\w-]+$"
    match = re.match(pattern, item)
    if match:
        return match.group(0)
    return None


def _extract_version_from_value_dependency(item: str) -> str | None:
    # Regex pattern to extract the version number before any parentheses
    pattern = r"^(\d+\.\d+\.\d+)"
    match = re.match(pattern, item)
    if match:
        return match.group(1)
    return None


def _get_package(
    packages: list[Package],
    dep_name: str | None,
    dep_version: str | None,
) -> Package | None:
    return next(
        (x for x in packages if x.name == dep_name and x.version == dep_version),
        None,
    )
