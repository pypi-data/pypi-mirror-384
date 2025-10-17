from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.ecosystem_data.python import WheelEggEcosystemData
from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.parsers.cataloger.utils import log_malformed_package_warning
from labels.utils.strings import normalize_name


def new_python_package(
    *,
    name: str | None,
    version: str | None,
    location: Location,
    ecosystem_data: WheelEggEcosystemData | None = None,
) -> Package | None:
    if not name or not version:
        return None

    normalized_name = normalize_name(name, PackageType.PythonPkg)

    p_url = PackageURL(type="pypi", name=normalized_name, version=version).to_string()

    try:
        return Package(
            name=normalized_name,
            version=version,
            locations=[location],
            language=Language.PYTHON,
            type=PackageType.PythonPkg,
            licenses=[],
            ecosystem_data=ecosystem_data,
            p_url=p_url,
        )
    except ValidationError as ex:
        log_malformed_package_warning(location, ex)
        return None
