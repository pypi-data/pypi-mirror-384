from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.parsers.cataloger.utils import log_malformed_package_warning


def new_package_from_composer(
    *,
    name: str | None,
    version: str | None,
    location: Location,
) -> Package | None:
    if not name or not version:
        return None

    p_url = _package_url_from_composer(name, version)

    try:
        return Package(
            name=name,
            version=version,
            locations=[location],
            language=Language.PHP,
            licenses=[],
            type=PackageType.PhpComposerPkg,
            p_url=p_url,
        )
    except ValidationError as ex:
        log_malformed_package_warning(location, ex)
        return None


def new_package_from_pecl(
    *,
    name: str | None,
    version: str | None,
    location: Location,
) -> Package | None:
    if not name or not version:
        return None

    try:
        return Package(
            name=name,
            version=version,
            locations=[location],
            language=Language.PHP,
            licenses=[],
            type=PackageType.PhpPeclPkg,
            p_url=PackageURL(type="pecl", name=name, version=version).to_string(),  # type: ignore[misc]
        )
    except ValidationError as ex:
        log_malformed_package_warning(location, ex)
        return None


def _package_url_from_composer(name: str, version: str) -> str:
    fields = name.split("/")

    vendor = ""
    if len(fields) == 1:
        name = fields[0]
    else:
        vendor = fields[0]
        name = "-".join(fields[1:])

    return PackageURL(type="composer", namespace=vendor, name=name, version=version).to_string()  # type: ignore[misc]
