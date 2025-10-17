from typing import Any, TextIO

from labels.model.ecosystem_data.arch import AlpmDBEntry
from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment, Release
from labels.model.resolver import Resolver
from labels.parsers.cataloger.arch.package_builder import new_arch_package

ALLOWED_STRING_KEYS: set[str] = {"name", "license", "base", "version", "arch"}
ALLOWED_NUMERIC_KEYS: set[str] = {"reason", "size"}


def parse_alpm_db(
    _resolver: Resolver,
    _env: Environment,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    alpm_db_entry = _collect_alpm_db_entry(reader.read_closer)
    if not alpm_db_entry or not reader.location.coordinates:
        return packages, relationships

    packages = _collect_packages(alpm_db_entry, _env.linux_release, reader.location)

    return packages, relationships


def _collect_packages(
    alpm_db_entry: AlpmDBEntry, linux_release: Release | None, location: Location
) -> list[Package]:
    packages: list[Package] = []
    package = new_arch_package(alpm_db_entry, linux_release, location)

    if package:
        packages.append(package)

    return packages


def _collect_alpm_db_entry(reader: TextIO) -> AlpmDBEntry | None:
    pkg_fields: dict[str, Any] = {}
    lines = reader.read().split("\n\n")

    for line in lines:
        if not line.strip():
            break  # End of block or file
        pkg_fields.update(_parse_key_value_pair(line))

    return _parse_raw_entry(pkg_fields)


def _parse_raw_entry(pkg_fields: dict[str, Any]) -> AlpmDBEntry | None:
    name = pkg_fields.get("name")
    if not name:
        return None

    return AlpmDBEntry(
        package=name,
        licenses=pkg_fields.get("license", ""),
        base_package=pkg_fields.get("base", ""),
        version=pkg_fields.get("version", ""),
        architecture=pkg_fields.get("arch", ""),
    )


def _parse_key_value_pair(line: str) -> dict[str, Any]:
    try:
        key, value = line.split("\n", 1)
    except ValueError:
        return {}

    key = key.replace("%", "").lower()
    value = value.strip()

    if key not in ALLOWED_STRING_KEYS | ALLOWED_NUMERIC_KEYS:
        return {}

    if key in ALLOWED_NUMERIC_KEYS:
        try:
            return {key: _parse_numeric_field(key, value)}
        except ValueError:
            return {}

    return {key: value}


def _parse_numeric_field(key: str, value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        error_msg = f"Failed to parse {key} to integer: {value}"
        raise ValueError(error_msg) from exc
