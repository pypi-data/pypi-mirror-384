from labels.model.file import Location, LocationReadCloser
from labels.model.indexables import IndexedDict, IndexedList, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship, RelationshipType
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.rust.utils import new_rust_package
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection.toml import parse_toml_with_tree_sitter


def parse_cargo_lock(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []

    if not reader.location.coordinates:
        return packages, []

    _content = reader.read_closer.read()
    toml: IndexedDict[str, ParsedValue] = parse_toml_with_tree_sitter(
        _content,
    )

    toml_pkgs: ParsedValue = toml.get("package")
    if not isinstance(toml_pkgs, IndexedList):
        return [], []

    packages.extend(
        package
        for package in (_create_package(pkg, reader.location) for pkg in toml_pkgs)
        if package
    )

    relationships = _create_relationships(packages, toml_pkgs)

    return packages, relationships


def _create_package(pkg: ParsedValue, location: Location) -> Package | None:
    if not isinstance(pkg, IndexedDict):
        return None

    name = str(pkg.get("name", "")) or None
    version = str(pkg.get("version", "")) or None

    if not version:
        return None

    new_location = get_enriched_location(location, line=pkg.get_key_position("version").start.line)

    return new_rust_package(name=name, version=version, location=new_location)


def _create_relationships(
    packages: list[Package], toml_pkgs: IndexedList[ParsedValue]
) -> list[Relationship]:
    relationships: list[Relationship] = []

    package_map = {pkg.name: pkg for pkg in packages}

    for pkg_data in toml_pkgs:
        if not isinstance(pkg_data, IndexedDict):
            continue

        package_name = str(pkg_data.get("name", ""))
        deps = pkg_data.get("dependencies", [])

        if package_name in package_map and isinstance(deps, IndexedList):
            current_package = package_map[package_name]

            for dep_name in deps:
                if isinstance(dep_name, str) and dep_name in package_map:
                    dep = package_map[dep_name]
                    relationships.append(
                        Relationship(
                            from_=dep.id_,
                            to_=current_package.id_,
                            type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
                        )
                    )
    return relationships
