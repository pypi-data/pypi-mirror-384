from packageurl import PackageURL
from pydantic import ValidationError

from labels.model.ecosystem_data.redhat import RpmDBEntry
from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.model.release import Environment
from labels.parsers.cataloger.redhat.rpmdb.domain.package import PackageInfo
from labels.parsers.cataloger.utils import get_enriched_location, log_malformed_package_warning


def new_redhat_package(
    *, entry: PackageInfo, location: Location, env: Environment
) -> Package | None:
    name = entry.name
    version = entry.version

    if not name or not version:
        return None

    ecosystem_data = RpmDBEntry(
        name=name,
        version=version,
        epoch=entry.epoch,
        arch=entry.arch,
        release=entry.release,
        source_rpm=entry.source_rpm,
    )

    new_location = get_enriched_location(location)
    p_url = _package_url(entry, env)

    el_version = _to_el_version(entry.epoch, version, entry.release)

    try:
        return Package(
            name=name,
            version=el_version,
            locations=[new_location],
            language=Language.UNKNOWN_LANGUAGE,
            licenses=[entry.license],
            type=PackageType.RpmPkg,
            ecosystem_data=ecosystem_data,
            p_url=p_url,
        )
    except ValidationError as ex:
        log_malformed_package_warning(new_location, ex)
        return None


def _package_url(entry: PackageInfo, env: Environment) -> str:
    namespace = ""
    if env.linux_release:
        namespace = env.linux_release.id_
    qualifiers: dict[str, str] = {}
    if entry.arch:
        qualifiers["arch"] = entry.arch
    if entry.epoch:
        qualifiers["epoch"] = str(entry.epoch)
    if entry.source_rpm:
        qualifiers["upstream"] = entry.source_rpm

    return PackageURL(
        type="rpm",
        namespace=namespace,
        name=entry.name,
        version=f"{entry.version}-{entry.release}",
        qualifiers=qualifiers,
        subpath="",
    ).to_string()


def _to_el_version(epoch: int | None, version: str, release: str) -> str:
    if epoch:
        return f"{epoch}:{version}-{release}"
    return f"{version}-{release}"
