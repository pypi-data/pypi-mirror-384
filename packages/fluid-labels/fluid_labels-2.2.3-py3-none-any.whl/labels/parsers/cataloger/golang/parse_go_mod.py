import re
from collections.abc import Iterator
from typing import Final, cast

from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.golang.package_builder import new_go_package
from labels.parsers.cataloger.utils import get_enriched_location

GO_DIRECTIVE: re.Pattern[str] = re.compile(
    r"(?P<directive>require|replace) \(",
)
GO_MOD_DEP: re.Pattern[str] = re.compile(
    r"^\s+(?P<product>.+?/[\w\-\.~]+?)\sv(?P<version>\S+)",
)
GO_REPLACE: re.Pattern[str] = re.compile(
    r"^\s+(?P<old_prod>.+?/[\w\-\.~]+?)(\sv(?P<old_ver>\S+))?\s=>"
    r"\s(?P<new_prod>.+?/[\w\-\.~]+?)(\sv(?P<new_ver>\S+))?$",
)
GO_REP_DEP: re.Pattern[str] = re.compile(
    r"replace\s(?P<old_prod>.+?/[\w\-\.~]+?)(\sv(?P<old_ver>\S+))?\s=>"
    r"\s(?P<new_prod>.+?/[\w\-\.~]+?)(\sv(?P<new_ver>\S+))?$",
)
GO_REQ_MOD_DEP: re.Pattern[str] = re.compile(
    r"require\s(?P<product>.+?/[\w\-\.~]+?)\sv(?P<version>\S+)",
)
GO_VERSION: re.Pattern[str] = re.compile(
    r"\ngo (?P<major>\d)\.(?P<minor>\d+)(\.\d+)?\n",
)

MINIMUM_SUPPORTED_GO_VERSION: Final[tuple[int, int]] = (1, 17)


def parse_go_mod(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    content = reader.read_closer.read()

    if _is_go_version_supported(content):
        packages = list(_collect_packages(content, reader.location))

    return packages, relationships


def _collect_packages(
    content: str,
    location: Location,
) -> Iterator[Package]:
    go_req_directive: str = ""
    replace_list: list[tuple[re.Match[str], int]] = []
    req_dict: dict[str, Package] = {}

    for line_number, line in enumerate(content.splitlines(), 1):
        if matched := GO_REQ_MOD_DEP.search(line):
            _add_required_package(matched, req_dict, line_number, location)
        elif replace := GO_REP_DEP.search(line):
            replace_list.append((replace, line_number))
        elif not go_req_directive:
            if directive := GO_DIRECTIVE.match(line):
                go_req_directive = directive.group("directive")
        elif go_req_directive == "replace":
            if replace := GO_REPLACE.search(line):
                replace_list.append((replace, line_number))
                continue
            go_req_directive = ""
        elif matched := GO_MOD_DEP.search(line):
            _add_required_package(matched, req_dict, line_number, location)
        else:
            go_req_directive = ""
    return _apply_replace_directives(req_dict, replace_list, location)


def _add_required_package(
    matched: re.Match[str],
    req_dict: dict[str, Package],
    line_number: int,
    parent_location: Location,
) -> None:
    product: str = matched.group("product")
    version: str = matched.group("version")

    new_location = get_enriched_location(parent_location, line=line_number, is_transitive=False)

    package = new_go_package(product, version, new_location)
    if package:
        req_dict[product] = package


def _apply_replace_directives(
    req_dict: dict[str, Package],
    replace_list: list[tuple[re.Match[str], int]],
    parent_location: Location,
) -> Iterator[Package]:
    for matched, line_number in replace_list:
        match_dict = cast("dict[str, str]", matched.groupdict())
        old_pkg, old_version = match_dict["old_prod"], match_dict["old_ver"]
        repl_pkg, version = match_dict["new_prod"], match_dict["new_ver"]

        if old_pkg not in req_dict:
            continue

        if old_version and not version:
            version = req_dict[old_pkg].version

        if not version or (old_version and req_dict[old_pkg].version != old_version):
            continue

        new_location = get_enriched_location(parent_location, line=line_number, is_transitive=False)

        package = new_go_package(repl_pkg, version, new_location)
        if package:
            req_dict[old_pkg] = package

    return iter(req_dict.values())


def _is_go_version_supported(content: str) -> bool:
    go_version = GO_VERSION.search(content)
    if not go_version:
        return False

    major = int(go_version.group("major"))
    minor = int(go_version.group("minor"))

    return (major, minor) >= MINIMUM_SUPPORTED_GO_VERSION
