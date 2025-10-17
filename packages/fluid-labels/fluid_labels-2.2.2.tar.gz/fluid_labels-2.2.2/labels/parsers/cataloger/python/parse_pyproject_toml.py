import re

from labels.model.file import LocationReadCloser
from labels.model.indexables import IndexedDict, IndexedList, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.python.package_builder import new_python_package
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection.toml import parse_toml_with_tree_sitter


def parse_pyproject_toml(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    content = parse_toml_with_tree_sitter(reader.read_closer.read())

    packages = []
    packages.extend(_parse_poetry_dependencies(content, reader))
    packages.extend(_parse_uv_dependencies(content, reader))

    return packages, []


def _parse_poetry_dependencies(
    content: IndexedDict[str, ParsedValue],
    reader: LocationReadCloser,
) -> list[Package]:
    packages: list[Package] = []
    tool = content.get("tool")
    if not isinstance(tool, IndexedDict):
        return packages

    poetry = tool.get("poetry")
    if not isinstance(poetry, IndexedDict):
        return packages

    deps = poetry.get("dependencies")
    if isinstance(deps, IndexedDict):
        packages.extend(_get_poetry_packages(reader, deps))

    group = poetry.get("group")
    if isinstance(group, IndexedDict):
        dev = group.get("dev")
        if isinstance(dev, IndexedDict):
            dev_deps = dev.get("dependencies")
            if isinstance(dev_deps, IndexedDict):
                packages.extend(_get_poetry_packages(reader, dev_deps, is_dev=True))

    dev_dependencies = poetry.get("dev-dependencies")
    if isinstance(dev_dependencies, IndexedDict):
        packages.extend(_get_poetry_packages(reader, dev_dependencies, is_dev=True))

    return packages


def _get_poetry_packages(
    reader: LocationReadCloser,
    dependencies: IndexedDict[str, ParsedValue],
    *,
    is_dev: bool = False,
) -> list[Package]:
    packages: list[Package] = []

    items = dependencies.items()

    for name, value in items:
        version = _get_version(value)

        new_location = get_enriched_location(
            reader.location,
            line=dependencies.get_key_position(name).start.line,
            is_dev=is_dev,
            is_transitive=False,
        )

        package = new_python_package(name=name, version=version, location=new_location)
        if package:
            packages.append(package)

    return packages


def _get_version(value: ParsedValue) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, IndexedDict):
        return None
    return str(value.get("version", ""))


def _parse_uv_dependencies(
    content: IndexedDict[str, ParsedValue],
    reader: LocationReadCloser,
) -> list[Package]:
    packages: list[Package] = []
    project = content.get("project")
    if not isinstance(project, IndexedDict):
        return packages

    uv_deps = project.get("dependencies")
    if isinstance(uv_deps, IndexedList):
        packages.extend(_get_uv_packages(reader, uv_deps))

    optional_deps = project.get("optional-dependencies")
    if isinstance(optional_deps, IndexedDict):
        uv_dev_deps = optional_deps.get("dev")
        if isinstance(uv_dev_deps, IndexedList):
            packages.extend(_get_uv_packages(reader, uv_dev_deps, is_dev=True))

    dependency_groups = content.get("dependency-groups")
    if isinstance(dependency_groups, IndexedDict):
        dev_group = dependency_groups.get("dev")
        if isinstance(dev_group, IndexedList):
            packages.extend(_get_uv_packages(reader, dev_group, is_dev=True))

    return packages


def _get_uv_packages(
    reader: LocationReadCloser,
    dependencies: IndexedList[ParsedValue],
    *,
    is_dev: bool = False,
) -> list[Package]:
    packages: list[Package] = []
    dep_pattern = re.compile(r"^([A-Za-z0-9_.\-]+)\s*([<>=!~]+.*)?$")

    for index, dep_string in enumerate(dependencies):
        if not isinstance(dep_string, str):
            continue

        match = dep_pattern.match(dep_string.strip())
        if match:
            name = match.group(1)
            version = match.group(2).strip() if match.group(2) else "*"
        else:
            name = dep_string.strip()
            version = "*"

        new_location = get_enriched_location(
            reader.location,
            line=dependencies.get_position(index).start.line,
            is_dev=is_dev,
            is_transitive=False,
        )

        package = new_python_package(name=name, version=version, location=new_location)
        if package:
            packages.append(package)

    return packages
