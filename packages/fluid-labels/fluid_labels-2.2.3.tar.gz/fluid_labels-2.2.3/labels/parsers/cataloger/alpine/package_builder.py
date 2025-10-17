from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.ecosystem_data.alpine import ApkDBEntry
from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.model.release import Release
from labels.parsers.cataloger.utils import get_enriched_location, log_malformed_package_warning
from labels.utils.licenses.validation import validate_licenses


def new_alpine_package(
    data: ApkDBEntry,
    release: Release | None,
    db_location: Location,
) -> Package | None:
    name = data.package
    version = data.version

    if not name or not version:
        return None

    new_location = get_enriched_location(db_location)

    try:
        return Package(
            name=name,
            version=version,
            locations=[new_location],
            licenses=validate_licenses(data.licenses.split(" ")) if data.licenses else [],
            p_url=package_url(data, release),
            type=PackageType.ApkPkg,
            ecosystem_data=data,
            found_by=None,
            health_metadata=None,
            language=Language.UNKNOWN_LANGUAGE,
        )
    except ValidationError as ex:
        log_malformed_package_warning(new_location, ex)
        return None


def package_url(entry: ApkDBEntry, distro: Release | None) -> str:
    qualifiers = {"arch": entry.architecture or ""} if entry else {}

    if entry and entry.origin_package != entry.package and entry.origin_package:
        qualifiers["upstream"] = entry.origin_package
    distro_qualifiers = []

    if distro and distro.id_:
        qualifiers["distro_id"] = distro.id_
        distro_qualifiers.append(distro.id_)

    if distro and distro.version_id:
        qualifiers["distro_version_id"] = distro.version_id
        distro_qualifiers.append(distro.version_id)
    elif distro and distro.build_id:
        distro_qualifiers.append(distro.build_id)

    if distro_qualifiers:
        qualifiers["distro"] = "-".join(distro_qualifiers)

    return PackageURL(  # type: ignore[misc]
        type="apk",
        namespace=distro.id_.lower() if distro and distro.id_ else "",
        name=entry.package,
        version=entry.version,
        qualifiers=qualifiers,
    ).to_string()
