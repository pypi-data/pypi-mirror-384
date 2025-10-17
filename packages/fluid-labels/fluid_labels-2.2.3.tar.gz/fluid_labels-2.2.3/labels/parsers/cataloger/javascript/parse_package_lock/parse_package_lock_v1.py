from labels.model.file import Location
from labels.model.indexables import IndexedDict, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship, RelationshipType
from labels.parsers.cataloger.javascript.package_builder import new_package_lock
from labels.parsers.cataloger.utils import get_enriched_location


def parse_package_lock_v1(
    location: Location,
    package_json: IndexedDict[str, ParsedValue],
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    dependencies = package_json.get("dependencies")
    if not isinstance(dependencies, IndexedDict):
        return packages, relationships

    direct_dependencies = _get_direct_dependencies(dependencies)
    packages = _collect_packages(location, dependencies, direct_dependencies)
    relationships = _build_relationships(dependencies, packages)

    return packages, relationships


def _get_direct_dependencies(dependencies: IndexedDict[str, ParsedValue]) -> list[str]:
    transitives: set[str] = set()
    for details in dependencies.values():
        if not isinstance(details, IndexedDict):
            continue

        requires = details.get("requires")
        if not isinstance(requires, IndexedDict):
            continue

        transitives.update(requires.keys())

    return [dependency for dependency in dependencies if dependency not in transitives]


def _collect_packages(
    location: Location,
    dependencies: IndexedDict[str, ParsedValue],
    direct_dependencies: list[str],
) -> list[Package]:
    packages: list[Package] = []
    for dependency_key, dependency_value in dependencies.items():
        if not isinstance(dependency_value, IndexedDict):
            continue

        is_transitive = dependency_key not in direct_dependencies
        is_dev = dependency_value.get("dev") is True
        new_location = get_enriched_location(
            location,
            line=dependency_value.position.start.line,
            is_dev=is_dev,
            is_transitive=is_transitive,
        )

        package = new_package_lock(
            location=new_location, name=dependency_key, value=dependency_value, lockfile_version=1
        )
        if package:
            packages.append(package)

        sub_dependencies = dependency_value.get("dependencies")
        if isinstance(sub_dependencies, IndexedDict):
            packages.extend(_collect_packages(location, sub_dependencies, direct_dependencies))

    return packages


def _build_relationships(
    dependencies: IndexedDict[str, ParsedValue], packages: list[Package]
) -> list[Relationship]:
    relationships: list[Relationship] = []

    for dependency_key, dependency_value in dependencies.items():
        if not isinstance(dependency_value, IndexedDict):
            continue

        requires_dict = dependency_value.get("requires")
        requires_names = (
            list(requires_dict.keys()) if isinstance(requires_dict, IndexedDict) else []
        )

        current_package = next(
            (package for package in packages if package.name == dependency_key), None
        )
        if not current_package:
            continue

        required_parsed_packages = [
            package for package in packages if package.name in requires_names
        ]
        relationships.extend(
            Relationship(
                from_=required_parsed_package.id_,
                to_=current_package.id_,
                type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
            )
            for required_parsed_package in required_parsed_packages
        )

    return relationships
