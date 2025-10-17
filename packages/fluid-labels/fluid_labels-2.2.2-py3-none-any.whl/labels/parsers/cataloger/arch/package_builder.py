from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.ecosystem_data.arch import AlpmDBEntry
from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.model.release import Release
from labels.parsers.cataloger.utils import (
    get_enriched_location,
    log_malformed_package_warning,
    purl_qualifiers,
)
from labels.utils.licenses.validation import validate_licenses


def new_arch_package(
    entry: AlpmDBEntry, release: Release | None, db_location: Location
) -> Package | None:
    name = entry.package
    version = entry.version

    if not name or not version:
        return None

    new_location = get_enriched_location(db_location)

    licenses_candidates = entry.licenses.split("\n")

    p_url = _package_url(entry, release)

    try:
        return Package(
            name=name,
            version=version,
            locations=[new_location],
            licenses=validate_licenses(licenses_candidates),
            type=PackageType.AlpmPkg,
            ecosystem_data=entry,
            p_url=p_url,
            language=Language.UNKNOWN_LANGUAGE,
        )
    except ValidationError as ex:
        log_malformed_package_warning(new_location, ex)
        return None


def _package_url(entry: AlpmDBEntry, distro: Release | None = None) -> str:
    qualifiers: dict[str, str | None] = {"arch": entry.architecture}
    if entry.base_package:
        qualifiers["upstream"] = entry.base_package

    return PackageURL(  # type: ignore[misc]
        type="alpm",
        name=entry.package,
        version=entry.version,
        qualifiers=purl_qualifiers(qualifiers, distro),
    ).to_string()
