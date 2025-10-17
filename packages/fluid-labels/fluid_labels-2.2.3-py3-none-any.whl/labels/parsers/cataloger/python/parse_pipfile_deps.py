from labels.model.file import LocationReadCloser
from labels.model.indexables import IndexedDict, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.python.package_builder import new_python_package
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection import toml


def parse_pipfile_deps(
    _resolver: Resolver | None,
    _env: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    file_content = reader.read_closer.read()
    toml_content: IndexedDict[str, ParsedValue] = toml.parse_toml_with_tree_sitter(file_content)

    toml_packages = toml_content.get("packages")
    if not isinstance(toml_packages, IndexedDict):
        return [], []

    packages = _get_packages(reader, toml_packages)

    dev_deps = toml_content.get("dev-packages")
    if isinstance(dev_deps, IndexedDict):
        dev_pkgs = _get_packages(reader, dev_deps, is_dev=True)
        packages.extend(dev_pkgs)

    return packages, []


def _get_packages(
    reader: LocationReadCloser,
    toml_packages: IndexedDict[str, ParsedValue],
    *,
    is_dev: bool = False,
) -> list[Package]:
    result = []
    for raw_package, version_data in toml_packages.items():
        version: str = ""
        if isinstance(version_data, str):
            version = version_data.strip("=<>~^ ")
        if isinstance(version_data, IndexedDict):
            version = str(version_data.get("version", "*")).strip("=<>~^ ")

        if "*" in version:
            continue

        new_location = get_enriched_location(
            reader.location,
            line=raw_package.position.start.line
            if isinstance(raw_package, IndexedDict)
            else toml_packages.get_key_position(raw_package).start.line,
            is_dev=is_dev,
            is_transitive=False,
        )

        package = new_python_package(name=raw_package, version=version, location=new_location)
        if package:
            result.append(package)

    return result
