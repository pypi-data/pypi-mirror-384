from labels.model.indexables import IndexedDict
from labels.model.package import Package, PackageType
from labels.model.relationship import Relationship, RelationshipType
from labels.utils.strings import normalize_name


def build_relationships_from_json_dependencies(
    dependencies: IndexedDict,
    current_package: Package,
    packages_by_key: dict[tuple[str, str], Package],
) -> list[Relationship]:
    relationships: list[Relationship] = []

    for dependency_name, dependency_version in dependencies.items():
        if not isinstance(dependency_name, str) or not isinstance(dependency_version, str):
            continue

        dependency_name_normalized = normalize_name(dependency_name, PackageType.DotnetPkg)
        dependency_package = packages_by_key.get((dependency_name_normalized, dependency_version))

        if dependency_package:
            relationships.append(
                Relationship(
                    from_=dependency_package.id_,
                    to_=current_package.id_,
                    type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
                )
            )

    return relationships
