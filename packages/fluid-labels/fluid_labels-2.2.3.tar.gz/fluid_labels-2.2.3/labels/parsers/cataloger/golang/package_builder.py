from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.parsers.cataloger.utils import log_malformed_package_warning


def new_go_package(name: str | None, version: str | None, location: Location) -> Package | None:
    if not name or not version:
        return None

    p_url = _get_package_url_for_go(name, version)

    try:
        return Package(
            name=name,
            version=version,
            type=PackageType.GoModulePkg,
            locations=[location],
            p_url=p_url,
            ecosystem_data=None,
            language=Language.GO,
            licenses=[],
        )
    except ValidationError as ex:
        log_malformed_package_warning(location, ex)
        return None


def _get_package_url_for_go(module_name: str, module_version: str) -> str:
    fields = module_name.split("/")

    if all(not f.strip() for f in fields):
        return ""

    namespace = ""
    name = ""
    subpath = ""

    if len(fields) == 1:
        name = fields[0]
    elif len(fields) == 2:
        name = fields[1]
        namespace = fields[0]
    else:
        name = fields[2]
        namespace = "/".join(fields[:2])
        subpath = "/".join(fields[3:])

    return PackageURL(  # type: ignore[misc]
        type="golang", namespace=namespace, name=name, version=module_version, subpath=subpath
    ).to_string()
