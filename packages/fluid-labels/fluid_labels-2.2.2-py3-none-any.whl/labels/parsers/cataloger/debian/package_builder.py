import logging
import re
from pathlib import Path
from typing import TextIO, cast

from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.ecosystem_data.debian import DpkgDBEntry
from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.model.release import Release
from labels.model.resolver import Resolver
from labels.parsers.cataloger.utils import (
    get_enriched_location,
    log_malformed_package_warning,
    purl_qualifiers,
)
from labels.utils.licenses.validation import validate_licenses

LOGGER = logging.getLogger(__name__)


def new_dpkg_package(
    entry: DpkgDBEntry,
    db_location: Location,
    resolver: Resolver | None,
    release: Release | None = None,
) -> Package | None:
    name = entry.package
    version = entry.version

    if not name or not version:
        return None

    new_location = get_enriched_location(db_location)

    try:
        package = Package(
            name=name,
            version=version,
            licenses=[],
            p_url=package_url(entry, release),
            locations=[new_location],
            type=PackageType.DebPkg,
            ecosystem_data=entry,
            found_by=None,
            language=Language.UNKNOWN_LANGUAGE,
        )
    except ValidationError as ex:
        log_malformed_package_warning(new_location, ex)
        return None

    if resolver is not None:
        _apply_side_effects(resolver, db_location, package)

    return package


def package_url(pkg: DpkgDBEntry, distro: Release | None = None) -> str:
    qualifiers = {"arch": pkg.architecture}
    if distro and (distro.id_ == "debian" or "debian" in (distro.id_like or [])):
        if distro.version_id:
            qualifiers["distro_version_id"] = distro.version_id
        qualifiers["distro_id"] = distro.id_
    if pkg.source:
        qualifiers["upstream"] = (
            f"{pkg.source}@{pkg.source_version}" if pkg.source_version else pkg.source
        )

    return PackageURL(  # type: ignore[misc]
        type="deb",
        namespace=distro.id_ if distro and distro.id_ else "",
        name=pkg.package,
        version=pkg.version,
        qualifiers=purl_qualifiers(qualifiers, distro),
    ).to_string()


def _apply_side_effects(resolver: Resolver, db_location: Location, pkg: Package) -> None:
    merge_file_listing(resolver, db_location, pkg)
    add_licenses(resolver, db_location, pkg)


def merge_file_listing(resolver: Resolver, db_location: Location, pkg: Package) -> None:
    if not isinstance(pkg.ecosystem_data, DpkgDBEntry):
        return

    info_locations = get_additional_file_listing(resolver, db_location, pkg.ecosystem_data)

    pkg.locations.extend(info_locations)


def get_additional_file_listing(
    resolver: Resolver,
    db_location: Location,
    entry: DpkgDBEntry,
) -> list[Location]:
    locations: list[Location] = []
    md5_result = fetch_md5_content(resolver, db_location, entry)
    if not md5_result:
        return locations

    md5_reader, md5_location = md5_result
    if md5_reader is not None and md5_location is not None:
        locations.append(md5_location)

    conffiles = fetch_conffile_contents(resolver, db_location, entry)
    if not conffiles:
        return locations

    conffiles_reader, conffiles_location = conffiles
    if conffiles_reader is not None and conffiles_location is not None:
        locations.append(conffiles_location)

    return locations


def fetch_md5_content(
    resolver: Resolver,
    db_location: Location,
    entry: DpkgDBEntry,
) -> tuple[TextIO | None, Location | None] | None:
    if not db_location.coordinates:
        return None
    search_path = Path(db_location.coordinates.real_path).parent
    if not str(search_path).endswith("status.d"):
        search_path = search_path / "info"
    name = md5_key(entry)
    md5_file = name + ".md5sums"
    location = resolver.relative_file_path(
        db_location,
        str(search_path / md5_file),
    )
    if not location:
        md5_file = entry.package + ".md5sums"
        location = resolver.relative_file_path(
            db_location,
            str(search_path / md5_file),
        )
    if not location:
        return None

    reader = resolver.file_contents_by_location(location)
    if not reader:
        LOGGER.warning(
            "failed to fetch deb md5 contents (package=%s)",
            entry.package,
        )
    return reader, location


def fetch_conffile_contents(
    resolver: Resolver,
    db_location: Location,
    entry: DpkgDBEntry,
) -> tuple[TextIO | None, Location | None] | None:
    if not db_location.coordinates:
        return None
    parent_path = Path(db_location.coordinates.real_path).parent

    name = md5_key(entry)
    md5_file = name + ".conffiles"
    location = resolver.relative_file_path(
        db_location,
        str(parent_path.joinpath("info", md5_file)),
    )
    if not location:
        md5_file = entry.package + ".conffiles"
        location = resolver.relative_file_path(
            db_location,
            str(parent_path.joinpath("info", md5_file)),
        )
    if not location:
        return None, None
    reader = resolver.file_contents_by_location(location)
    if not reader:
        LOGGER.warning(
            "failed to fetch deb conffiles contents (package=%s)",
            entry.package,
        )
    return reader, location


def add_licenses(resolver: Resolver, db_location: Location, pkg: Package) -> None:
    metadata: DpkgDBEntry = cast("DpkgDBEntry", pkg.ecosystem_data)

    pkg.licenses = []
    copyright_reader, copyright_location = fetch_copyright_contents(resolver, db_location, metadata)

    if copyright_reader is not None and copyright_location is not None:
        licenses_strs = parse_licenses_from_copyright(copyright_reader)
        pkg.licenses = validate_licenses(licenses_strs)


def fetch_copyright_contents(
    resolver: Resolver | None,
    db_location: Location,
    metadata: DpkgDBEntry,
) -> tuple[TextIO | None, Location | None]:
    if not resolver:
        return None, None

    copyright_path = Path("/usr/share/doc").joinpath(metadata.package, "copyright")
    location = resolver.relative_file_path(db_location, str(copyright_path))

    if not location:
        return None, None

    reader = resolver.file_contents_by_location(location)
    if not reader:
        LOGGER.warning(
            "Failed to fetch deb copyright contents (package=%s)",
            metadata.package,
        )

    return reader, location


def parse_licenses_from_copyright(reader: TextIO) -> list[str]:
    result = []
    for raw_line in reader:
        line = raw_line.rstrip("\n")
        if value := find_license_clause(r"^License: (?P<license>\S*)", "license", line):
            result.append(value)
        if value := find_license_clause(
            r"/usr/share/common-licenses/(?P<license>[0-9A-Za-z_.\-]+)",
            "license",
            line,
        ):
            result.append(value)

    return list(set(result))


def find_license_clause(pattern: str, value_group: str, line: str) -> str | None:
    match = re.search(pattern, line)
    if match:
        license_value = match.group(value_group)
        return ensure_is_single_license(license_value)
    return None


def ensure_is_single_license(candidate: str) -> str | None:
    candidate = candidate.strip()
    if " or " in candidate or " and " in candidate:
        return None
    if candidate and candidate.lower() != "none":
        return candidate.rstrip(".")
    return None


def md5_key(metadata: DpkgDBEntry) -> str:
    content_key = metadata.package
    if metadata.architecture not in ("", "all"):
        return f"{content_key}:{metadata.architecture}"
    return content_key
