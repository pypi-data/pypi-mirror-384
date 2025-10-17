import re

from labels.model.ecosystem_data.alpine import ApkDBEntry
from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship, RelationshipType
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.alpine.package_builder import new_alpine_package

APK_DB_GLOB = "**/lib/apk/db/installed"


def parse_apk_db(
    _resolver: Resolver,
    environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    file_content = reader.read_closer.read()
    if not file_content:
        return packages, relationships

    apk_db_entries = _collect_apk_db_entries(file_content)

    packages = _collect_packages(apk_db_entries, environment, reader.location)
    relationships = _collect_relationships(packages)

    return packages, relationships


def _collect_apk_db_entries(content: str) -> list[ApkDBEntry]:
    apk_db_entries: list[ApkDBEntry] = []
    stripped_content = content.strip().split("\n\n")

    for package_content in stripped_content:
        if not package_content:
            continue

        apk_db_entry = _parse_package_content(package_content)
        if apk_db_entry:
            apk_db_entries.append(apk_db_entry)

    return apk_db_entries


def _parse_package_content(content: str) -> ApkDBEntry | None:
    parsed_data_dict: dict[str, str] = {}
    lines = content.split("\n")
    key = ""

    for line in lines:
        key = _process_line_and_update_data(line, key, parsed_data_dict)

    return _construct_apk_db_entry(parsed_data_dict)


def _process_line_and_update_data(line: str, key: str, data: dict[str, str]) -> str:
    if ":" in line:
        key, value = line.split(":", 1)
        data[key] = value
    elif key and key in data:
        data[key] += "\n" + line.strip()
    return key


def _construct_apk_db_entry(data: dict[str, str]) -> ApkDBEntry | None:
    package = data.get("P")
    version = data.get("V")
    if not package or not version:
        return None

    return ApkDBEntry(
        package=package,
        version=version,
        origin_package=data.get("o"),
        maintainer=data.get("m"),
        architecture=data.get("A"),
        dependencies=_parse_list_values(data.get("D")),
        provides=_parse_list_values(data.get("p")),
        licenses=data.get("L"),
    )


def _parse_list_values(value: str | None, delimiter: str | None = None) -> list[str]:
    delimiter = delimiter or " "
    if not value:
        return []

    return value.split(delimiter)


def _collect_packages(
    apk_db_entries: list[ApkDBEntry], environment: Environment | None, location: Location
) -> list[Package]:
    packages: list[Package] = []
    release = environment.linux_release if environment else None

    for apk_db_entry in apk_db_entries:
        package = new_alpine_package(apk_db_entry, release, location)
        if package:
            packages.append(package)

    return packages


def _collect_relationships(packages: list[Package]) -> list[Relationship]:
    relationships: list[Relationship] = []
    lookup = _build_lookup_table(packages)

    for package in packages:
        if not isinstance(package.ecosystem_data, ApkDBEntry):
            continue

        package_apk_db_entry = package.ecosystem_data
        for dep_specifier in package_apk_db_entry.dependencies:
            dependency_name = _strip_version_specifier(dep_specifier)
            relationships.extend(
                Relationship(
                    from_=dependency_package.id_,
                    to_=package.id_,
                    type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
                )
                for dependency_package in lookup.get(dependency_name, [])
            )

    return relationships


def _build_lookup_table(packages: list[Package]) -> dict[str, list[Package]]:
    lookup: dict[str, list[Package]] = {}

    for package in packages:
        if package.ecosystem_data is None:
            continue

        if not isinstance(package.ecosystem_data, ApkDBEntry):
            continue

        apkg = package.ecosystem_data
        if package.name not in lookup:
            lookup[package.name] = [package]
        else:
            lookup[package.name].append(package)

        for provides in apkg.provides:
            provides_k = _strip_version_specifier(provides)
            if provides_k not in lookup:
                lookup[provides_k] = [package]
            else:
                lookup[provides_k].append(package)

    return lookup


def _strip_version_specifier(version: str) -> str:
    splitted_version: list[str] = re.split("[<>=]", version)
    return splitted_version[0]
