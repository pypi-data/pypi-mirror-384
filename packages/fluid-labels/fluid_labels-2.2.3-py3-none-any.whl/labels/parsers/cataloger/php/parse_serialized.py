from typing import Any

import phpserialize

from labels.model.file import LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.php.package_builder import new_package_from_pecl
from labels.parsers.cataloger.utils import get_enriched_location


def parse_pecl_serialized(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    unserialized_data = phpserialize.loads(reader.read_closer.read().encode(), decode_strings=True)
    parsed_data = _php_to_python(unserialized_data)
    name = str(parsed_data.get("name", "")) or None
    version = str(parsed_data.get("version", {}).get("release", "")) or None

    new_location = get_enriched_location(reader.location)

    package = new_package_from_pecl(name=name, version=version, location=new_location)
    if package:
        packages.append(package)

    return packages, relationships


def _php_to_python(obj: Any) -> Any:  # noqa: ANN401
    if isinstance(obj, dict):
        return {_php_to_python(k): _php_to_python(v) for k, v in obj.items()}
    return obj
