from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.file import Location
from labels.model.indexables import IndexedDict, ParsedValue
from labels.model.package import Language, Package, PackageType
from labels.parsers.cataloger.utils import log_malformed_package_warning


def new_package_lock(
    location: Location,
    name: str,
    value: IndexedDict[str, ParsedValue],
    lockfile_version: int,
) -> Package | None:
    version: str = str(value.get("version", ""))

    if not name or not version:
        return None

    if lockfile_version == 1:
        alias_prefix_package_lock = "npm:"
        if version.startswith(alias_prefix_package_lock):
            name, version = version.removeprefix(alias_prefix_package_lock).rsplit(
                "@",
                1,
            )

    p_url = get_npm_package_url(name, version)

    try:
        return Package(
            name=name,
            version=version,
            locations=[location],
            language=Language.JAVASCRIPT,
            licenses=[],
            type=PackageType.NpmPkg,
            p_url=p_url,
        )
    except ValidationError as ex:
        log_malformed_package_warning(location, ex)
        return None


def new_simple_npm_package(
    location: Location,
    name: str | None,
    version: str | None,
) -> Package | None:
    if not name or not version:
        return None

    p_url = get_npm_package_url(name, version)

    try:
        return Package(
            name=name,
            version=version,
            locations=[location],
            language=Language.JAVASCRIPT,
            licenses=[],
            type=PackageType.NpmPkg,
            p_url=p_url,
        )
    except ValidationError as ex:
        log_malformed_package_warning(location, ex)
        return None


def get_npm_package_url(name: str, version: str) -> str:
    namespace = ""
    fields = name.split("/", 2)
    if len(fields) > 1:
        namespace = fields[0]
        name = fields[1]

    if not name:
        return ""

    return PackageURL(type="npm", namespace=namespace, name=name, version=version).to_string()  # type: ignore[misc]
