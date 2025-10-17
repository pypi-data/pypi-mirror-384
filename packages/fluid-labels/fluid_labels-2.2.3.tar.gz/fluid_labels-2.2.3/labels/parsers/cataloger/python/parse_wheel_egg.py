from typing import NamedTuple, TextIO

from labels.model.ecosystem_data.python import WheelEggEcosystemData
from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.python.package_builder import new_python_package


class WheelEggPackageData(NamedTuple):
    name: str
    version: str
    ecosystem_data: WheelEggEcosystemData | None = None


def parse_wheel_or_egg(
    resolver: Resolver,
    _: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    package_data = _assemble_wheel_egg_package_data(resolver, reader.location)
    if not package_data:
        return packages, relationships

    package = new_python_package(
        name=package_data.name,
        version=package_data.version,
        location=reader.location,
        ecosystem_data=package_data.ecosystem_data,
    )
    if package:  # pragma: no cover
        packages.append(package)

    return packages, relationships


def _assemble_wheel_egg_package_data(
    resolver: Resolver,
    metadata_location: Location,
) -> WheelEggPackageData | None:
    metadata_content = resolver.file_contents_by_location(metadata_location)

    if not metadata_content or not metadata_location.coordinates:
        return None

    package_data = _parse_wheel_egg_package_data(metadata_content)
    if not package_data:
        return None

    return package_data


def _parse_wheel_egg_package_data(reader: TextIO) -> WheelEggPackageData | None:
    metadata_dict = _parse_metadata(reader.read())

    name = metadata_dict.get("Name")
    version = metadata_dict.get("Version")

    if not isinstance(name, str) or not isinstance(version, str):
        return None

    dependencies = _extract_dependencies(metadata_dict)

    return WheelEggPackageData(
        name=name,
        version=version,
        ecosystem_data=WheelEggEcosystemData(dependencies=dependencies),
    )


def _extract_dependencies(metadata_dict: dict[str, str | list[str]]) -> list[str]:
    dependencies: list[str] = []

    requires_dist = metadata_dict.get("Requires-Dist")
    provides_extra = metadata_dict.get("Provides-Extra")

    if not isinstance(provides_extra, list):
        provides_extra = None

    if requires_dist:
        dependencies = _required_dependencies(requires_dist, provides_extra)

    return dependencies


def _parse_metadata(data: str) -> dict[str, str | list[str]]:
    parsed_data: dict[str, str | list[str]] = {}
    lines = _split_lines(data)
    multi_line_key: str | None = None

    for line in lines:
        if not line:
            break
        if multi_line_key and line.startswith((" ", "\t")):
            multi_line_key = _handle_multiline_values(line, multi_line_key, parsed_data)
        else:
            multi_line_key = _process_line(line, parsed_data)
    return parsed_data


def _split_lines(data: str) -> list[str]:
    return data.strip().split("\n")


def _process_line(line: str, parsed_data: dict[str, str | list[str]]) -> str:
    multi_line_key = None
    if ": " in line:
        key, value = line.split(": ", 1)
        _update_parsed_data(key, value, parsed_data)
        if key in ["Description", "Classifier"]:
            multi_line_key = key
    return multi_line_key or ""


def _handle_multiline_values(
    line: str,
    multi_line_key: str,
    parsed_data: dict[str, str | list[str]],
) -> str:
    if multi_line_key and isinstance(parsed_data[multi_line_key], str):
        parsed_data[multi_line_key] += "\n" + line.strip()  # type: ignore[operator]
    return multi_line_key


def _update_parsed_data(key: str, value: str, parsed_data: dict[str, str | list[str]]) -> None:
    if key in parsed_data:
        if isinstance(parsed_data[key], list):
            parsed_data[key].append(value)  # type: ignore[union-attr]
        else:
            parsed_data[key] = [parsed_data[key], value]  # type: ignore[list-item]
    else:
        parsed_data[key] = value


def _required_dependencies(
    requires_dis: list[str] | str,
    provides_extra: list[str] | None = None,
) -> list[str]:
    if isinstance(requires_dis, str):
        requires_dis = [requires_dis]
    result: list[str] = []
    provides_extra = provides_extra or []
    for item in requires_dis:
        parts = item.split(";")
        if any(x in parts[-1] for x in provides_extra):
            continue
        result.append(parts[0].strip())
    return result
