from labels.model.file import LocationReadCloser
from labels.model.indexables import IndexedDict, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.javascript.package_builder import new_simple_npm_package
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection.json import parse_json_with_tree_sitter


def parse_package_json(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    package_json = parse_json_with_tree_sitter(reader.read_closer.read())

    if not isinstance(package_json, IndexedDict):
        return packages, relationships

    packages = [
        *_create_packages(package_json, reader, is_dev=False),
        *_create_packages(package_json, reader, is_dev=True),
    ]

    return packages, relationships


def _create_packages(
    package_json: IndexedDict[str, ParsedValue], reader: LocationReadCloser, *, is_dev: bool
) -> list[Package]:
    packages: list[Package] = []
    dependencies_key = "devDependencies" if is_dev else "dependencies"

    dependencies = package_json.get(dependencies_key)
    if not isinstance(dependencies, IndexedDict):
        return packages

    for package_name, specifier in dependencies.items():
        if not package_name or not specifier:
            continue

        new_location = get_enriched_location(
            reader.location,
            line=dependencies.get_key_position(package_name).start.line,
            is_dev=is_dev,
            is_transitive=False,
        )

        package = new_simple_npm_package(new_location, package_name, str(specifier))
        if package:
            packages.append(package)

    return packages
