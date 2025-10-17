from labels.model.file import LocationReadCloser
from labels.model.indexables import IndexedDict
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.javascript.parse_package_lock.parse_package_lock_v1 import (
    parse_package_lock_v1,
)
from labels.parsers.cataloger.javascript.parse_package_lock.parse_package_lock_v2 import (
    parse_package_lock_v2,
)
from labels.parsers.collection.json import parse_json_with_tree_sitter


def parse_package_lock(
    _resolver: Resolver | None, _environment: Environment | None, reader: LocationReadCloser
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    package_json = parse_json_with_tree_sitter(reader.read_closer.read())
    if not isinstance(package_json, IndexedDict):
        return packages, relationships

    match package_json.get("lockfileVersion", 1):
        case 1:
            return parse_package_lock_v1(reader.location, package_json)
        case 2 | 3:
            return parse_package_lock_v2(reader.location, package_json)

    return packages, relationships
