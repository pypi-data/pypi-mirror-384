from collections.abc import Iterable

from labels.model.file import LocationReadCloser
from labels.model.indexables import IndexedDict, IndexedList, ParsedValue
from labels.model.package import Package, PackageType
from labels.model.relationship import Relationship, RelationshipType
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.python.package_builder import new_python_package
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection import toml
from labels.utils.strings import normalize_name


def parse_poetry_lock(
    _resolver: Resolver | None,
    _env: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    _content = reader.read_closer.read()

    toml_content: IndexedDict[str, ParsedValue] = toml.parse_toml_with_tree_sitter(_content)

    packages = _parse_packages(toml_content, reader)
    relationships = _parse_relationships(toml_content, packages)

    return packages, relationships


def _parse_packages(
    toml_content: IndexedDict[str, ParsedValue],
    reader: LocationReadCloser,
) -> list[Package]:
    packages = []
    toml_pkgs = toml_content.get("package")
    if not isinstance(toml_pkgs, IndexedList):
        return []

    for raw_package in toml_pkgs:
        if not isinstance(raw_package, IndexedDict):
            continue
        name = str(raw_package.get("name", ""))
        version = str(raw_package.get("version", ""))

        if not version:
            continue

        new_location = (
            get_enriched_location(
                reader.location,
                line=raw_package.get_key_position("version").start.line,
            )
            if isinstance(raw_package, IndexedDict)
            else reader.location
        )

        package = new_python_package(name=name, version=version, location=new_location)
        if package:
            packages.append(package)

    return packages


def _get_dependencies(
    package: ParsedValue,
    packages: list[Package],
) -> tuple[Package | None, IndexedDict[str, ParsedValue]] | None:
    if not isinstance(package, IndexedDict):
        return None

    package_name = package.get("name")
    if not isinstance(package_name, str):
        return None

    _pkg = _find_package_by_name(packages, package_name)

    deps = package.get("dependencies")
    if not isinstance(deps, IndexedDict):
        return None

    return _pkg, deps


def _find_package_by_name(packages: list[Package], name: str) -> Package | None:
    return next(
        (p for p in packages if p.name == normalize_name(name, PackageType.PythonPkg)), None
    )


def _parse_relationships(
    toml_content: IndexedDict[str, ParsedValue],
    packages: list[Package],
) -> list[Relationship]:
    relationships = []
    toml_pkgs = toml_content.get("package")

    if not isinstance(toml_pkgs, IndexedList):
        return []

    for package in toml_pkgs:
        pkg_with_deps = _get_dependencies(package, packages)

        if not pkg_with_deps:
            continue

        pkg, deps = pkg_with_deps

        if not pkg or not deps:
            continue

        relationships.extend(_create_relationships_for_package(pkg, deps.keys(), packages))

    return relationships


def _create_relationships_for_package(
    pkg: Package, dependency_names: Iterable[str], packages: list[Package]
) -> list[Relationship]:
    relationships = []
    for dep_name in dependency_names:
        dep_pkg = _find_package_by_name(packages, dep_name)
        if dep_pkg:
            relationships.append(
                Relationship(
                    from_=dep_pkg.id_,
                    to_=pkg.id_,
                    type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
                )
            )
    return relationships
