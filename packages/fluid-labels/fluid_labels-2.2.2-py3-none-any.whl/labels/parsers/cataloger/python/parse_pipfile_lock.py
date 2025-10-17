from typing import cast

from labels.model.file import LocationReadCloser
from labels.model.indexables import IndexedDict, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.python.package_builder import new_python_package
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection.json import parse_json_with_tree_sitter


def parse_pipfile_lock_deps(
    _resolver: Resolver | None,
    _env: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    content = cast(
        "IndexedDict[str, ParsedValue]",
        parse_json_with_tree_sitter(reader.read_closer.read()),
    )
    deps: ParsedValue | None = content.get("default")
    dev_deps: ParsedValue | None = content.get("develop")
    packages = [
        *_get_packages(reader, deps),
        *_get_packages(reader, dev_deps, is_dev=True),
    ]
    return packages, []


def _get_version(value: IndexedDict[str, ParsedValue]) -> str:
    version = value.get("version")
    if not isinstance(version, str):
        return ""
    return version.strip("=<>~^ ")


def _get_packages(
    reader: LocationReadCloser,
    dependencies: ParsedValue | None,
    *,
    is_dev: bool = False,
) -> list[Package]:
    if dependencies is None or not isinstance(dependencies, IndexedDict):
        return []

    packages = []

    items = dependencies.items()
    for name, value in items:
        if not isinstance(value, IndexedDict) or not isinstance(name, str):
            continue

        version = _get_version(value)

        new_location = get_enriched_location(
            reader.location, line=value.position.start.line, is_dev=is_dev
        )

        package = new_python_package(name=name, version=version, location=new_location)
        if package:
            packages.append(package)

    return packages
