from typing import NamedTuple

from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.parsers.cataloger.utils import log_malformed_package_warning


class DartPubspecLickEntry(NamedTuple):
    hosted_url: str
    vcs_url: str


def new_pubspec_package(
    name: str | None,
    version: str | None,
    location: Location,
    metadata: DartPubspecLickEntry | None = None,
) -> Package | None:
    if not name or not version:
        return None

    p_url = _package_url_for_pubspec(name, version, metadata)

    try:
        return Package(
            name=name,
            version=version,
            locations=[location],
            language=Language.DART,
            licenses=[],
            type=PackageType.DartPubPkg,
            p_url=p_url,
        )
    except ValidationError as ex:
        log_malformed_package_warning(location, ex)
        return None


def _package_url_for_pubspec(
    name: str, version: str, ecosystem_data: DartPubspecLickEntry | None = None
) -> str:
    qualifiers: dict[str, str] = {}
    if ecosystem_data:
        if ecosystem_data.hosted_url:
            qualifiers["hosted_url"] = ecosystem_data.hosted_url
        elif ecosystem_data.vcs_url:
            qualifiers["vcs_url"] = ecosystem_data.vcs_url

    return PackageURL(type="pub", name=name, version=version, qualifiers=qualifiers).to_string()  # type: ignore[misc]
