from packageurl import PackageURL
from pydantic_core import ValidationError

from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.parsers.cataloger.utils import log_malformed_package_warning
from labels.utils.strings import normalize_name


def new_dotnet_package(
    name: str | None, version: str | None, new_location: Location
) -> Package | None:
    if not name or not version:
        return None

    normalized_package_name = normalize_name(name, PackageType.DotnetPkg)
    p_url = PackageURL(type="nuget", name=normalized_package_name, version=version).to_string()

    try:
        return Package(
            name=normalized_package_name,
            version=version,
            locations=[new_location],
            language=Language.DOTNET,
            licenses=[],
            type=PackageType.DotnetPkg,
            p_url=p_url,
        )
    except ValidationError as ex:
        log_malformed_package_warning(new_location, ex)

    return None
