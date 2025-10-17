import re

from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.java.utils.package_builder import JavaPackageSpec, new_java_package
from labels.parsers.cataloger.utils import get_enriched_location

GRADLE_DISTRIBUTION = re.compile("^distributionUrl=.+gradle-(?P<gradle_version>[^-]+)-.+")


def parse_gradle_properties(
    _resolver: Resolver | None,
    _environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    file_content = reader.read_closer.read()
    if not file_content:
        return packages, relationships

    packages = _collect_packages(file_content, reader.location)

    return packages, relationships


def _collect_packages(file_content: str, location: Location) -> list[Package]:
    packages: list[Package] = []

    for line_no, raw_line in enumerate(file_content.splitlines(), start=1):
        line = raw_line.strip()

        matched_gradle_distribution = GRADLE_DISTRIBUTION.match(line)
        if not matched_gradle_distribution:
            continue

        version = matched_gradle_distribution.group("gradle_version")

        new_location = get_enriched_location(location, line=line_no)

        package_spec = JavaPackageSpec(
            simple_name="gradle",
            version=version,
            location=new_location,
        )

        package = new_java_package(package_spec)

        if package:
            packages.append(package)

    return packages
