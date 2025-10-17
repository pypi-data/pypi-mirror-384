import re
from typing import TypeGuard

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.dotnet.package_builder import new_dotnet_package
from labels.parsers.cataloger.utils import get_enriched_location

RUNTIME_TAG_NAME = "supportedruntime"
RUNTIME_TAG_PARENT_NAME = "startup"
RUNTIME_TAG_SKU_ATTRIBUTE = "sku"
RUNTIME_TAG_DEPENDENCY_PATTERN = re.compile(r".NETFramework,Version=v(?P<version>[^\s,]*)")

EXECUTABLE_PACKAGE_NAME = "netframework"


def parse_dotnet_config_executable(
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

    net_runtime_tag = root.find(RUNTIME_TAG_NAME)

    if _is_valid_runtime_tag(net_runtime_tag):
        runtime_info = net_runtime_tag.get(RUNTIME_TAG_SKU_ATTRIBUTE, "")
        version_match = RUNTIME_TAG_DEPENDENCY_PATTERN.match(str(runtime_info))
        if not runtime_info or not version_match:
            return packages

        version = version_match.group("version")

        new_location = get_enriched_location(
            location, line=net_runtime_tag.sourceline, is_transitive=False, is_dev=False
        )

        new_package = new_dotnet_package(EXECUTABLE_PACKAGE_NAME, version, new_location)
        if new_package:
            packages.append(new_package)

    return packages


def _is_valid_runtime_tag(
    net_runtime_tag: Tag | NavigableString | None,
) -> TypeGuard[Tag]:
    return bool(
        isinstance(net_runtime_tag, Tag)
        and isinstance(net_runtime_tag.parent, Tag)
        and net_runtime_tag.parent.name == RUNTIME_TAG_PARENT_NAME
    )
