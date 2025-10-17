from typing import cast

from labels.model.file import Location, LocationReadCloser
from labels.model.indexables import IndexedDict, IndexedList, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship, RelationshipType
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.php.package_builder import new_package_from_composer
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection.json import parse_json_with_tree_sitter

EMPTY_LIST: IndexedList[ParsedValue] = IndexedList()


def parse_installed_json(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []
    package_json = parse_json_with_tree_sitter(reader.read_closer.read())

    if not isinstance(package_json, (IndexedDict, IndexedList)):  # pragma: no cover
        return packages, relationships

    packages = _extract_packages(package_json, reader.location)
    relationships = _extract_relationships(packages, package_json)

    return packages, relationships


def _extract_packages(
    package_json: IndexedDict[str, ParsedValue] | IndexedList[ParsedValue],
    location: Location,
) -> list[Package]:
    packages = []
    dev_packages = EMPTY_LIST

    if (
        isinstance(package_json, IndexedDict)
        and "dev-package-names" in package_json
        and isinstance(package_json["dev-package-names"], IndexedList)
    ):
        dev_packages = package_json["dev-package-names"]

    packages_list = (
        package_json["packages"]
        if isinstance(package_json, IndexedDict) and "packages" in package_json
        else package_json
    )

    for package in packages_list if isinstance(packages_list, IndexedList) else EMPTY_LIST:
        if not isinstance(package, IndexedDict):
            continue

        name = cast("str", package.get("name"))
        version = cast("str", package.get("version"))

        if not name:
            continue

        is_dev = _is_dev_package(package, dev_packages)
        new_location = get_enriched_location(
            location,
            line=package.get_key_position("name").start.line,
            is_dev=is_dev,
            is_transitive=False,
        )

        pkg_item = new_package_from_composer(name=name, version=version, location=new_location)
        if pkg_item:
            packages.append(pkg_item)

    return packages


def _extract_relationships(
    packages: list[Package], package_json: IndexedDict[str, ParsedValue] | IndexedList[ParsedValue]
) -> list[Relationship]:
    relationships = []
    packages_list = (
        package_json["packages"]
        if isinstance(package_json, IndexedDict) and "packages" in package_json
        else package_json
    )

    if not isinstance(packages_list, IndexedList):
        return []

    for package in packages_list:
        parsed_package_with_dependencies = _get_parsed_package_and_dependencies(package, packages)
        if not parsed_package_with_dependencies:
            continue

        parsed_package, dependencies = parsed_package_with_dependencies
        if not parsed_package or not dependencies:
            continue

        raw_dependency_names = list(dependencies.keys()) if dependencies else []
        for dep_name in raw_dependency_names:
            dependency_parsed_package = next((x for x in packages if x.name == dep_name), None)
            if dependency_parsed_package:
                relationships.append(
                    Relationship(
                        from_=dependency_parsed_package.id_,
                        to_=parsed_package.id_,
                        type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
                    ),
                )

    return relationships


def _is_dev_package(
    package: IndexedDict[str, ParsedValue], dev_packages: IndexedList[ParsedValue]
) -> bool:
    name_value = package.get("name")
    name = name_value if isinstance(name_value, str) else None

    return name in dev_packages if name else False


def _get_parsed_package_and_dependencies(
    package_data: ParsedValue,
    packages: list[Package],
) -> tuple[Package | None, IndexedDict[str, ParsedValue]] | None:
    if not isinstance(package_data, IndexedDict):
        return None

    package_name = package_data.get("name")
    if not isinstance(package_name, str):
        return None

    parsed_package = next((p for p in packages if p.name == package_name), None)

    raw_dependencies = package_data.get("require")
    if not parsed_package or not isinstance(raw_dependencies, IndexedDict):
        return None

    return parsed_package, raw_dependencies
