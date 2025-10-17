import re

from labels.model.ecosystem_data.debian import DpkgDBEntry
from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship, RelationshipType
from labels.model.release import Environment, Release
from labels.model.resolver import Resolver
from labels.parsers.cataloger.debian.package_builder import new_dpkg_package, package_url

VERSION_SPECIFIERS = "[(<>="
PACKAGE_BLOCK_SEPARATOR = "\n\n"
DEPENDENCY_SEPARATOR = ","
CHOICE_SEPARATOR = "|"


def parse_dpkg_db(
    resolver: Resolver | None,
    environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    content = reader.read_closer.read()
    if not content:
        return packages, relationships

    dpkg_entries = _collect_dpkg_entries(content)
    packages = _collect_packages(dpkg_entries, reader.location, resolver, environment)
    relationships = _collect_relationships(packages)

    return packages, relationships


def _collect_dpkg_entries(content: str) -> list[DpkgDBEntry]:
    entries = []
    for package in content.strip().split(PACKAGE_BLOCK_SEPARATOR):
        lines = package.split("\n")
        data = {}
        prev_key = ""
        for line in lines:
            key, value = _handle_new_key_value(line)

            if key is not None:
                data[key] = value
                prev_key = key
            elif prev_key in data:
                data[prev_key] = f"{data[prev_key]}\n{value}"

        if all(not value for value in data.values()):
            continue

        entry = _parse_raw_entry(data)
        if entry:
            entries.append(entry)

    return entries


def _collect_packages(
    dpkg_entries: list[DpkgDBEntry],
    location: Location,
    resolver: Resolver | None,
    environment: Environment | None,
) -> list[Package]:
    packages: list[Package] = []

    release = environment.linux_release if environment else None
    for entry in dpkg_entries:
        package = new_dpkg_package(entry, location, resolver, release)

        if package:
            packages.append(package)
            source_package = _collect_source_package(package, release)
            if source_package:
                packages.append(source_package)

    return packages


def _collect_relationships(packages: list[Package]) -> list[Relationship]:
    relationships: list[Relationship] = []
    lookup_table = _build_lookup_table(packages)

    for package in packages:
        if not isinstance(package.ecosystem_data, DpkgDBEntry):
            continue

        ecosystem_data = package.ecosystem_data
        all_dependencies = [
            *(ecosystem_data.dependencies or []),
            *(ecosystem_data.pre_dependencies or []),
        ]

        for dep_specifier in all_dependencies:
            dependencies = _split_package_choices(dep_specifier)
            for dependency in dependencies:
                relationships.extend(
                    Relationship(
                        from_=dependency_package.id_,
                        to_=package.id_,
                        type=RelationshipType.DEPENDENCY_OF_RELATIONSHIP,
                    )
                    for dependency_package in lookup_table.get(dependency, [])
                )

    return relationships


def _parse_raw_entry(raw_entry: dict[str, str]) -> DpkgDBEntry | None:
    source_name, source_version = _extract_source_version(raw_entry.get("Source"))
    package = raw_entry.get("Package")
    if not package:
        return None

    return DpkgDBEntry(
        package=package,
        source=source_name,
        version=raw_entry.get("Version"),
        source_version=source_version or None,
        architecture=raw_entry.get("Architecture"),
        maintainer=raw_entry.get("Maintainer"),
        provides=_split_deps(raw_entry.get("Provides")),
        dependencies=_split_deps(raw_entry.get("Depends")),
        pre_dependencies=_split_deps(raw_entry.get("Pre-Depends")),
    )


def _collect_source_package(
    package: Package,
    release: Release | None,
) -> Package | None:
    entry = package.ecosystem_data
    if not isinstance(entry, DpkgDBEntry):
        return None

    if _should_create_source_package(entry, package):
        updated_entry: dict[str, str | None] = {
            "package": entry.source,
            "version": entry.source_version or package.version,
            "source": None,
            "source_version": None,
            "provides": None,
        }
        new_entry = entry.model_copy(update=updated_entry, deep=True)

        updated_package: dict[str, str | DpkgDBEntry | None] = {
            "name": new_entry.package,
            "version": new_entry.version,
            "p_url": package_url(new_entry, release),
            "ecosystem_data": new_entry,
        }

        return package.model_copy(update=updated_package)

    return None


def _should_create_source_package(entry: DpkgDBEntry, package: Package) -> bool:
    has_different_source = entry.source and entry.source != package.name

    has_different_version = (
        entry.source and entry.source_version and entry.source_version != package.version
    )

    return bool(has_different_source or has_different_version)


def _build_lookup_table(packages: list[Package]) -> dict[str, list[Package]]:
    lookup: dict[str, list[Package]] = {}

    for package in packages:
        lookup.setdefault(package.name, []).append(package)

    for package in packages:
        if not isinstance(package.ecosystem_data, DpkgDBEntry):
            continue

        ecosystem_data = package.ecosystem_data
        for provides in ecosystem_data.provides or []:
            key = _strip_version_specifier(provides)
            lookup.setdefault(key, []).append(package)

    return lookup


def _split_deps(value: str | None) -> list[str] | None:
    if not value:
        return None

    fields = value.split(DEPENDENCY_SEPARATOR)
    return [field.strip() for field in fields if field.strip()]


def _extract_source_version(source: str | None) -> tuple[str | None, str | None]:
    if not source:
        return None, None

    if match_result := re.compile(r"(?P<name>\S+)( \((?P<version>.*)\))?").match(source):
        result = match_result.groupdict()

        return result["name"], result["version"] or None

    return source, None


def _handle_new_key_value(line: str) -> tuple[str | None, str]:
    if _is_key_value_line(line):
        key, value = line.split(":", 1)
        value = value.strip()

        return key, value

    return None, line


def _is_key_value_line(line: str) -> bool:
    return ":" in line and not line.startswith(" ")


def _strip_version_specifier(item: str) -> str:
    # Define the characters that indicate the start of a version specifier
    specifiers = VERSION_SPECIFIERS

    # Find the index of the first occurrence of any specifier character
    index = next((i for i, char in enumerate(item) if char in specifiers), None)

    # If no specifier character is found, return the original string
    if index is None:
        return item.strip()

    # Return the substring up to the first specifier character, stripped of
    # leading/trailing whitespace
    return item[:index].strip()


def _split_package_choices(value: str) -> list[str]:
    fields = value.split(CHOICE_SEPARATOR)
    return [_strip_version_specifier(field) for field in fields if field.strip()]
