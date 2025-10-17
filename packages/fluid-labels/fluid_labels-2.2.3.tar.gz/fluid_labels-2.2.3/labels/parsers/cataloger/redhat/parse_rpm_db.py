from labels.model.file import LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.redhat.package_builder import new_redhat_package
from labels.parsers.cataloger.redhat.rpmdb.dispatcher import open_db


def parse_rpm_db(
    _: Resolver,
    env: Environment,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []

    if not reader.location.coordinates:
        return packages, []

    database = open_db(reader.location.coordinates.real_path)

    if not database:
        return packages, []

    for entry in database.list_packages():
        package = new_redhat_package(entry=entry, env=env, location=reader.location)
        if package is not None:
            packages.append(package)

    return packages, []
