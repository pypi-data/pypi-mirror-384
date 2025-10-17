from labels.model.file import Location
from labels.model.indexables import IndexedDict, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship, RelationshipType
from labels.parsers.cataloger.javascript.package_builder import new_package_lock
from labels.parsers.cataloger.utils import get_enriched_location


def parse_package_lock_v2(
    location: Location,
    package_json: IndexedDict[str, ParsedValue],
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    packages_dict = package_json.get("packages")
    if not isinstance(packages_dict, IndexedDict):
        return packages, relationships

    direct_dependencies = _get_direct_dependencies_v2_v3(package_json)
    packages = _collect_packages(location, packages_dict, direct_dependencies)
    dependency_map = _build_dependency_map(package_json)
    relationships = _build_relationships(packages, dependency_map)

    return packages, relationships


def _collect_packages(
    location: Location,
    packages_dict: IndexedDict[str, ParsedValue],
    direct_dependencies: list[str],
) -> list[Package]:
    packages: list[Package] = []

    for dependency_key, package_value in packages_dict.items():
        if not dependency_key or not isinstance(package_value, IndexedDict):
            continue

        name = _get_name(dependency_key, package_value) or _get_name_from_path(dependency_key)

        is_transitive = name not in direct_dependencies
        is_dev = package_value.get("dev") is True
        new_location = get_enriched_location(
            location,
            line=package_value.position.start.line,
            is_dev=is_dev,
            is_transitive=is_transitive,
        )

        package = new_package_lock(
            location=new_location, name=name, value=package_value, lockfile_version=2
        )
        if package:
            packages.append(package)

    return packages


def _build_dependency_map(
    package_json: IndexedDict[str, ParsedValue],
) -> dict[str, ParsedValue]:
    dependency_map: dict[str, ParsedValue] = {}

    packages_dict = package_json.get("packages")
    if not isinstance(packages_dict, IndexedDict):
        return dependency_map

    for dependency_key, package_value in packages_dict.items():
        if not dependency_key or not isinstance(package_value, IndexedDict):
            continue

        name = _get_name(dependency_key, package_value)
        dependencies = package_value.get("dependencies")
        dependency_map[name or dependency_key] = dependencies

    return dependency_map


def _build_relationships(
    packages: list[Package], dependency_map: dict[str, ParsedValue]
) -> list[Relationship]:
    relationships: list[Relationship] = []
    for package in packages:
        dependencies = dependency_map.get(package.name)
        if not isinstance(dependencies, IndexedDict):
            continue

        for dependency_name in dependencies:
            dependency_pkg = next(
                (package for package in packages if package.name == dependency_name), None
            )
            if dependency_pkg:
                relationships.append(
                    Relationship(
                        from_=dependency_pkg.id_,
                        to_=package.id_,
                        type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
                    ),
                )
    return relationships


def _get_direct_dependencies_v2_v3(package_lock_path: IndexedDict[str, ParsedValue]) -> list[str]:
    all_dependencies: ParsedValue = package_lock_path.get("packages", IndexedDict())
    if not isinstance(all_dependencies, IndexedDict):
        return []

    result: list[str] = []
    for dep, value in all_dependencies.items():
        if isinstance(value, IndexedDict) and dep == "":
            deps_candidate: ParsedValue = value.get("dependencies")
            if isinstance(deps_candidate, IndexedDict):
                result.extend(deps_candidate)
            dev_deps_candidate: ParsedValue = value.get("devDependencies")
            if isinstance(dev_deps_candidate, IndexedDict):
                result.extend(dev_deps_candidate)

    return result


def _get_name(dependency_key: str, package_value: IndexedDict[str, ParsedValue]) -> str | None:
    name = dependency_key
    if not name:
        if "name" not in package_value:
            return None
        name = str(package_value["name"])

    # Handle alias name
    if "name" in package_value and package_value["name"] != dependency_key:
        name = str(package_value["name"])

    return _get_name_from_path(name)


def _get_name_from_path(name: str) -> str:
    return name.split("node_modules/")[-1]
