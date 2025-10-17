from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.parsers.cataloger.utils import log_malformed_package_warning


def new_cocoa_pods_package(
    *, name: str | None, version: str | None, location: Location
) -> Package | None:
    if not name or not version:
        return None

    try:
        return Package(
            name=name,
            version=version,
            p_url=PackageURL(type="cocoapods", name=name, version=version).to_string(),  # type: ignore[misc]
            locations=[location],
            type=PackageType.CocoapodsPkg,
            language=Language.SWIFT,
            licenses=[],
        )
    except ValidationError as ex:
        log_malformed_package_warning(location, ex)
        return None


def new_swift_package_manager_package(
    *, source_url: str | None, version: str | None, location: Location
) -> Package | None:
    if not source_url or not version:
        return None

    name = extract_package_name(source_url)

    try:
        return Package(
            name=name,
            version=version,
            p_url=PackageURL(type="swift", name=name, version=version).to_string(),  # type: ignore[misc]
            locations=[location],
            type=PackageType.SwiftPkg,
            language=Language.SWIFT,
            licenses=[],
        )
    except ValidationError as ex:
        log_malformed_package_warning(location, ex)
        return None


def extract_package_name(url: str) -> str:
    return url.split("://", 1)[-1].replace('"', "").removesuffix(".git")
