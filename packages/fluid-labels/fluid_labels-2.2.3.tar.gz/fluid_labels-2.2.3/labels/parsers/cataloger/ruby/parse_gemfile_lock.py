import re

from labels.model.file import LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.ruby.package_builder import new_gem_package
from labels.parsers.cataloger.utils import get_enriched_location

GEM_LOCK_DEP: re.Pattern[str] = re.compile(r"^\s{4}(?P<gem>[^\s]*)\s\([^\d]*(?P<version>.*)\)$")


def parse_gemfile_lock(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []
    line_gem: bool = False

    for line_number, line in enumerate(reader.read_closer.read().splitlines(), 1):
        if line.startswith("GEM"):
            line_gem = True
        elif line_gem:
            if matched := GEM_LOCK_DEP.match(line):
                pkg_name = matched.group("gem")
                pkg_version = matched.group("version")

                new_location = get_enriched_location(
                    reader.location, line=line_number, is_transitive=False
                )

                package = new_gem_package(pkg_name, pkg_version, new_location)
                if package:
                    packages.append(package)
            elif not line:
                break

    return packages, relationships
