from labels.model.file import LocationReadCloser
from labels.model.indexables import IndexedDict, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.rust.utils import new_rust_package
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection.toml import parse_toml_with_tree_sitter


def parse_cargo_toml(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    content: IndexedDict[
        str,
        ParsedValue,
    ] = parse_toml_with_tree_sitter(reader.read_closer.read())

    deps: ParsedValue = content.get(
        "dependencies",
    )
    dev_deps: ParsedValue = content.get(
        "dev-dependencies",
    )
    packages = [
        *_get_packages(reader, deps, is_dev=False),
        *_get_packages(reader, dev_deps, is_dev=True),
    ]
    return packages, []


def _get_packages(
    reader: LocationReadCloser,
    dependencies: ParsedValue,
    *,
    is_dev: bool,
) -> list[Package]:
    packages: list[Package] = []
    if dependencies is None or not isinstance(dependencies, IndexedDict):
        return packages

    items = dependencies.items()

    for name, value in items:
        version = _get_version(value)

        new_location = get_enriched_location(
            reader.location,
            line=dependencies.get_key_position(name).start.line,
            is_dev=is_dev,
            is_transitive=False,
        )

        package = new_rust_package(name=name, version=version, location=new_location)
        if package:
            packages.append(package)

    return packages


def _get_version(value: ParsedValue) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, IndexedDict):
        return None
    if "git" in value:
        repo_url: str = str(value.get("git", ""))
        branch: str = str(value.get("branch", ""))
        if repo_url and branch:
            return f"{repo_url}@{branch}"
    version: str = str(value.get("version", ""))
    return version
