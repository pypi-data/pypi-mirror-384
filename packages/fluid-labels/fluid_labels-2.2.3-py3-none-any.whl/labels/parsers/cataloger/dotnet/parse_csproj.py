import re

from bs4 import BeautifulSoup, Tag

from labels.model.file import LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.dotnet.package_builder import new_dotnet_package
from labels.parsers.cataloger.utils import get_enriched_location

PACKAGE = re.compile(r".+\\packages\\(?P<package_info>[^\s\\]*)\\.+")
DEP_INFO = re.compile(r"(?P<package_name>.*?)\.(?P<version>\d+[^\s]*)$")


PACKAGE_REFERENCE_ELEMENT = "packagereference"
PRIVATE_ASSETS_ELEMENT = "privateassets"
REFERENCE_ELEMENT = "reference"
HINT_PATH_ELEMENT = "hintpath"


def parse_csproj(
    _resolver: Resolver | None,
    _env: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    root = BeautifulSoup(reader.read_closer.read(), features="html.parser")

    packages = _collect_packages(root, reader)

    return packages, relationships


def _collect_packages(root: BeautifulSoup, reader: LocationReadCloser) -> list[Package]:
    packages: list[Package] = []

    for raw_package in root.find_all(PACKAGE_REFERENCE_ELEMENT, recursive=True):
        package_name = raw_package.get("include")
        version = raw_package.get("version")
        if not package_name or not version:
            continue

        is_dev = _is_dev_dependency(raw_package)
        new_location = get_enriched_location(
            reader.location, line=raw_package.sourceline, is_transitive=False, is_dev=is_dev
        )

        package = new_dotnet_package(package_name, version, new_location)

        if package:
            packages.append(package)

    packages.extend(_collect_package_from_reference_dependencies(root, reader))

    return packages


def _is_dev_dependency(pkg: BeautifulSoup) -> bool:
    checking_attr = "all"

    element = pkg.find(PRIVATE_ASSETS_ELEMENT)
    if isinstance(element, Tag):
        return element.get_text(strip=True).lower() == checking_attr

    attr = pkg.get(PRIVATE_ASSETS_ELEMENT)
    if isinstance(attr, str):
        return attr.strip().lower() == checking_attr

    return False


def _collect_package_from_reference_dependencies(
    raw_package: Tag, reader: LocationReadCloser
) -> list[Package]:
    packages: list[Package] = []
    references = raw_package.find_all(REFERENCE_ELEMENT, recursive=True)

    for reference in references:
        package = _extract_package_from_reference(reference, reader)
        if package:
            packages.append(package)

    return packages


def _extract_package_from_reference(reference: Tag, reader: LocationReadCloser) -> Package | None:
    package = _extract_from_hint_path(reference, reader)
    if package:
        return package

    return _extract_from_include_attribute(reference, reader)


def _extract_from_hint_path(reference: Tag, reader: LocationReadCloser) -> Package | None:
    dll_path = reference.find(HINT_PATH_ELEMENT)
    if not isinstance(dll_path, Tag):
        return None

    dll_package = PACKAGE.match(dll_path.text)
    if not dll_package:
        return None

    package_info = DEP_INFO.match(dll_package.group("package_info"))
    if not package_info:
        return None

    new_location = get_enriched_location(
        reader.location, line=dll_path.sourceline, is_transitive=False
    )

    name = str(package_info.group("package_name").lower())
    version = str(package_info.group("version"))

    return new_dotnet_package(name, version, new_location)


def _extract_from_include_attribute(raw_package: Tag, reader: LocationReadCloser) -> Package | None:
    include = raw_package.get("include")
    if not isinstance(include, str):
        return None

    include_info = include.replace(" ", "").split(",")
    if not include_info:
        return None

    package_name = include_info[0].strip()
    version = _get_version(include_info)

    if not package_name or not version:
        return None

    new_location = get_enriched_location(
        reader.location, line=raw_package.sourceline, is_transitive=False
    )

    return new_dotnet_package(package_name, version, new_location)


def _get_version(include_info: list[str]) -> str | None:
    return next(
        (
            package_info.lstrip("Version=")
            for package_info in include_info
            if package_info.startswith("Version=")
        ),
        None,
    )
