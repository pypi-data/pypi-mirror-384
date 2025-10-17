from urllib3.util import parse_url

from labels.model.file import Location, LocationReadCloser
from labels.model.indexables import IndexedDict, ParsedValue
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.dart.package_builder import DartPubspecLickEntry, new_pubspec_package
from labels.parsers.cataloger.utils import get_enriched_location
from labels.parsers.collection.yaml import parse_yaml_with_tree_sitter


def parse_pubspec_lock(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    package_yaml = parse_yaml_with_tree_sitter(reader.read_closer.read())
    if not isinstance(package_yaml, IndexedDict):
        return packages, relationships

    yaml_packages = package_yaml.get("packages")
    if not isinstance(yaml_packages, IndexedDict):
        return packages, relationships

    packages = _collect_packages(reader.location, yaml_packages)

    return packages, relationships


def _collect_packages(
    location: Location, yaml_packages: IndexedDict[str, ParsedValue]
) -> list[Package]:
    packages: list[Package] = []

    for package_name, package_value in yaml_packages.items():
        if not isinstance(package_value, IndexedDict):
            continue

        is_transitive = package_value.get("dependency") == "transitive"
        version = package_value.get("version")

        if not isinstance(version, str) or not package_name:
            continue

        new_location = get_enriched_location(
            location,
            line=yaml_packages.get_key_position(package_name).start.line,
            is_transitive=is_transitive,
        )

        metadata = DartPubspecLickEntry(
            hosted_url=_get_hosted_url(package_value),
            vcs_url=_get_vcs_url(package_value),
        )

        package = new_pubspec_package(package_name, version, new_location, metadata)
        if package:
            packages.append(package)

    return packages


def _get_hosted_url(entry: IndexedDict[str, ParsedValue]) -> str:
    hosted = entry.get("hosted")
    description = entry.get("description")

    if hosted != "hosted" or not isinstance(description, IndexedDict):
        return ""

    description_url = description.get("url")
    if not isinstance(description_url, str) or description_url == "https://pub.dartlang.org":
        return ""

    host_from_url = parse_url(description_url).host

    return host_from_url if host_from_url else description_url


def _get_vcs_url(entry: IndexedDict[str, ParsedValue]) -> str:
    source = entry.get("source")
    description = entry.get("description")

    if source != "git" or not isinstance(description, IndexedDict):
        return ""

    url = description.get("url")
    resolved_ref = description.get("resolved-ref")
    path = description.get("path")

    if not url or not resolved_ref:
        return ""

    if path == "." or not path:
        return f"{url}@{resolved_ref}"

    return f"{url}@{resolved_ref}#{path}"
