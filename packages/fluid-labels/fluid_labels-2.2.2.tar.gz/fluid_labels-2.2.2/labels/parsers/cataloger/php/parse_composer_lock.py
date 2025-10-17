from typing import cast

from labels.model.file import LocationReadCloser
from labels.model.indexables import IndexedDict, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship, RelationshipType
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.php.package_builder import new_package_from_composer
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection.json import parse_json_with_tree_sitter

EMPTY_DICT: IndexedDict[str, ParsedValue] = IndexedDict()


def parse_composer_lock(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    package_json: IndexedDict[str, ParsedValue] = cast(
        "IndexedDict[str, ParsedValue]",
        parse_json_with_tree_sitter(reader.read_closer.read()),
    )

    packages = _extract_packages(package_json, reader)
    relationships = _extract_relationships(package_json, packages)

    return packages, relationships


def _extract_packages(
    package_json: IndexedDict[str, ParsedValue], reader: LocationReadCloser
) -> list[Package]:
    packages: list[Package] = []

    for is_dev, raw_package in _get_all_packages_with_dev_flag(package_json):
        name = str(raw_package.get("name", "")) or None
        version = str(raw_package.get("version", "")) or None

        if not name:
            continue

        new_location = get_enriched_location(
            reader.location,
            line=raw_package.get_key_position("name").start.line,
            is_dev=is_dev,
            is_transitive=False,
        )

        package = new_package_from_composer(name=name, version=version, location=new_location)
        if package:
            packages.append(package)

    return packages


def _extract_relationships(
    package_json: IndexedDict[str, ParsedValue], packages: list[Package]
) -> list[Relationship]:
    relationships: list[Relationship] = []

    all_packages = [package for _, package in _get_all_packages_with_dev_flag(package_json)]

    for raw_package in all_packages:
        name = str(raw_package.get("name", "")) or None
        if not name:
            continue

        parsed_package = next((x for x in packages if x.name == name), None)
        if not parsed_package:
            continue

        if isinstance(raw_package.get("require"), IndexedDict):
            require = cast("dict[str, str]", raw_package.get("require"))
            deps = list(require.keys())

            for dep_name in deps:
                package_dep = next((x for x in packages if x.name == dep_name), None)
                if package_dep:
                    relationships.append(
                        Relationship(
                            from_=parsed_package.id_,
                            to_=package_dep.id_,
                            type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
                        ),
                    )

    return relationships


def _get_all_packages_with_dev_flag(
    package_json: IndexedDict[str, ParsedValue],
) -> list[tuple[bool, IndexedDict[str, ParsedValue]]]:
    production_packages = _get_packages_dict(package_json, "packages")
    development_packages = _get_packages_dict(package_json, "packages-dev")

    return [
        *[(False, package) for package in production_packages if isinstance(package, IndexedDict)],
        *[(True, package) for package in development_packages if isinstance(package, IndexedDict)],
    ]


def _get_packages_dict(
    package_json: IndexedDict[str, ParsedValue], key: str
) -> IndexedDict[str, ParsedValue]:
    return cast(
        "IndexedDict[str, ParsedValue]",
        package_json.get(key, EMPTY_DICT),
    )
