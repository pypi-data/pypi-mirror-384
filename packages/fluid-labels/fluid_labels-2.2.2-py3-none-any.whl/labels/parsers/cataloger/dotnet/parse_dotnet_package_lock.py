from more_itertools import flatten

from labels.model.file import Location, LocationReadCloser
from labels.model.indexables import IndexedDict, ParsedValue
from labels.model.package import Package, PackageType
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.dotnet.package_builder import new_dotnet_package
from labels.parsers.cataloger.dotnet.utils import build_relationships_from_json_dependencies
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection.json import parse_json_with_tree_sitter
from labels.utils.strings import normalize_name


def parse_dotnet_package_lock(
    _resolver: Resolver | None,
    _env: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    package_json = parse_json_with_tree_sitter(reader.read_closer.read())
    if not isinstance(package_json, IndexedDict):
        return packages, relationships

    targets = _collect_targets(package_json)
    if not targets:
        return packages, relationships

    packages = _collect_packages(targets, reader.location)
    relationships = _collect_relationships(targets, packages)

    return packages, relationships


def _collect_targets(package_json: IndexedDict) -> list[tuple[str, ParsedValue]] | None:
    targets: ParsedValue = package_json.get("dependencies")
    if not isinstance(targets, IndexedDict):
        return None

    return list(
        flatten(target.items() for target in targets.values() if isinstance(target, IndexedDict))
    )


def _collect_packages(targets: list[tuple[str, ParsedValue]], location: Location) -> list[Package]:
    packages: list[Package] = []

    for package_name, package_value in targets:
        if not isinstance(package_value, IndexedDict):
            continue

        version = package_value.get("resolved")
        if not isinstance(version, str):
            continue

        is_transitive = package_value.get("type", "") == "Transitive"
        new_location = get_enriched_location(
            location, line=package_value.position.start.line, is_transitive=is_transitive
        )

        new_package = new_dotnet_package(package_name, version, new_location)
        if new_package:
            packages.append(new_package)

    return packages


def _collect_relationships(
    targets: list[tuple[str, ParsedValue]],
    packages: list[Package],
) -> list[Relationship]:
    relationships: list[Relationship] = []

    packages_by_key = {(pkg.name, pkg.version): pkg for pkg in packages}

    for package_key, package_value in targets:
        relationships.extend(
            _build_relationships_for_package(package_key, package_value, packages_by_key)
        )

    return relationships


def _build_relationships_for_package(
    package_key: str,
    package_value: ParsedValue,
    packages_by_key: dict[tuple[str, str], Package],
) -> list[Relationship]:
    relationships: list[Relationship] = []

    if not isinstance(package_value, IndexedDict):
        return relationships

    normalized_name = normalize_name(package_key, PackageType.DotnetPkg)
    version = package_value.get("resolved")
    if not isinstance(version, str):
        return relationships

    current_package = packages_by_key.get((normalized_name, version))
    if not isinstance(current_package, Package):
        return relationships

    dependencies = package_value.get("dependencies")
    if not isinstance(dependencies, IndexedDict):
        return relationships

    return build_relationships_from_json_dependencies(
        dependencies, current_package, packages_by_key
    )
