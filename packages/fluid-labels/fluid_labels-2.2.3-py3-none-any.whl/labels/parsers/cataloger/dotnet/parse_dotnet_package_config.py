from bs4 import BeautifulSoup

from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.dotnet.package_builder import new_dotnet_package
from labels.parsers.cataloger.utils import get_enriched_location

PACKAGE_TAG = "package"


def parse_dotnet_pkgs_config(
    _resolver: Resolver | None,
    _env: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    root = BeautifulSoup(reader.read_closer.read(), features="html.parser")

    packages = _collect_packages(root, reader.location)

    return packages, relationships


def _collect_packages(root: BeautifulSoup, location: Location) -> list[Package]:
    packages: list[Package] = []

    for raw_package in root.find_all(PACKAGE_TAG, recursive=True):
        name: str | None = raw_package.get("id")
        version: str | None = raw_package.get("version")

        if not name or not version:
            continue

        new_location = get_enriched_location(
            location, line=raw_package.sourceline, is_transitive=False
        )

        new_package = new_dotnet_package(name, version, new_location)
        if new_package:
            packages.append(new_package)

    return packages
