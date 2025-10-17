from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.parsers.cataloger.utils import log_malformed_package_warning


def new_rust_package(name: str | None, version: str | None, location: Location) -> Package | None:
    if not name or not version:
        return None

    try:
        return Package(
            name=name,
            version=version,
            locations=[location],
            language=Language.RUST,
            licenses=[],
            p_url=PackageURL(type="cargo", name=name, version=version).to_string(),  # type: ignore[misc]
            type=PackageType.RustPkg,
        )
    except ValidationError as ex:
        log_malformed_package_warning(location, ex)
        return None
