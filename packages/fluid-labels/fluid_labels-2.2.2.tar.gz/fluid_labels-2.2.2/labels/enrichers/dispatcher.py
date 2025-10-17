import contextlib
import logging
from collections.abc import Callable
from typing import cast

from pydantic import ValidationError

import labels.enrichers.alpine.complete as enrich_alpine
import labels.enrichers.dart.complete as enrich_dart
import labels.enrichers.debian.complete as enrich_debian
import labels.enrichers.dotnet.complete as enrich_dotnet
import labels.enrichers.elixir.complete as enrich_elixir
import labels.enrichers.golang.complete as enrich_go
import labels.enrichers.java.complete as enrich_java
import labels.enrichers.javascript.complete as enrich_js
import labels.enrichers.php.complete as enrich_php
import labels.enrichers.python.complete as enrich_python
import labels.enrichers.ruby.complete as enrich_ruby
import labels.enrichers.rust.complete as enrich_rust
from labels.advisories import images as images_advisories
from labels.advisories import roots as roots_advisories
from labels.model.advisories import Advisory
from labels.model.ecosystem_data.alpine import ApkDBEntry
from labels.model.ecosystem_data.arch import AlpmDBEntry
from labels.model.ecosystem_data.debian import DpkgDBEntry
from labels.model.ecosystem_data.redhat import RpmDBEntry
from labels.model.file import Location
from labels.model.metadata import HealthMetadata
from labels.model.package import Language, Package, PackageType
from labels.parsers.cataloger.utils import extract_distro_info
from labels.utils.strings import format_exception

LOGGER = logging.getLogger(__name__)


ROOT_TYPES: set[PackageType] = {
    PackageType.NpmPkg,
    PackageType.DartPubPkg,
    PackageType.DotnetPkg,
    PackageType.JavaPkg,
    PackageType.PhpComposerPkg,
    PackageType.PythonPkg,
    PackageType.GemPkg,
    PackageType.RustPkg,
    PackageType.GoModulePkg,
    PackageType.HexPkg,
    PackageType.ConanPkg,
    PackageType.GithubActionPkg,
    PackageType.SwiftPkg,
}

IMAGES_TYPES: set[PackageType] = {
    PackageType.DebPkg,
    PackageType.ApkPkg,
    PackageType.RpmPkg,
}

COMPLETION_MAP: dict[PackageType, Callable[[Package], Package]] = {
    PackageType.NpmPkg: enrich_js.complete_package,
    PackageType.DartPubPkg: enrich_dart.complete_package,
    PackageType.DotnetPkg: enrich_dotnet.complete_package,
    PackageType.JavaPkg: enrich_java.complete_package,
    PackageType.PhpComposerPkg: enrich_php.complete_package,
    PackageType.PythonPkg: enrich_python.complete_package,
    PackageType.GemPkg: enrich_ruby.complete_package,
    PackageType.RustPkg: enrich_rust.complete_package,
    PackageType.GoModulePkg: enrich_go.complete_package,
    PackageType.HexPkg: enrich_elixir.complete_package,
    PackageType.DebPkg: enrich_debian.complete_package,
    PackageType.ApkPkg: enrich_alpine.complete_package,
}

ALLOWED_TYPE = dict[
    str,
    str
    | Language
    | list[str]
    | list[Location]
    | PackageType
    | list[Advisory]
    | list[Package]
    | HealthMetadata
    | bool
    | object
    | None,
]


def update_root_advisories(package: Package) -> list[Advisory]:
    if pkg_platform := package.type.get_platform_value():
        safe_versions = roots_advisories.get_safe_versions(pkg_platform.lower(), package.name)
        package.safe_versions = safe_versions
        return roots_advisories.get_vulnerabilities(
            pkg_platform.lower(),
            package.name,
            package.version,
            safe_versions,
        )
    return []


def _get_upstream_info(package: Package) -> tuple[str | None, str | None]:
    """Extract upstream package information based on package type."""
    # APK packages
    if (
        package.type == PackageType.ApkPkg
        and isinstance(package.ecosystem_data, ApkDBEntry)
        and package.ecosystem_data
        and package.ecosystem_data.origin_package
    ):
        return package.ecosystem_data.origin_package, package.version

    # Debian packages
    if (
        package.type == PackageType.DebPkg
        and isinstance(package.ecosystem_data, DpkgDBEntry)
        and package.ecosystem_data
        and package.ecosystem_data.source
    ):
        return (
            package.ecosystem_data.source,
            package.ecosystem_data.source_version or package.version,
        )

    # Arch Linux packages
    if (
        package.type == PackageType.AlpmPkg
        and isinstance(package.ecosystem_data, AlpmDBEntry)
        and package.ecosystem_data
        and package.ecosystem_data.base_package
    ):
        return package.ecosystem_data.base_package, package.version

    # RPM packages
    if (
        package.type == PackageType.RpmPkg
        and isinstance(package.ecosystem_data, RpmDBEntry)
        and package.ecosystem_data
        and package.ecosystem_data.source_rpm
    ):
        return _extract_rpm_upstream_info(package.ecosystem_data.source_rpm)

    return None, None


def _extract_rpm_upstream_info(source_rpm: str) -> tuple[str | None, str | None]:
    """Extract upstream package name and version from RPM source package.

    RPM format: NAME-VERSION-RELEASE[.ARCH].src.rpm or NAME-VERSION-RELEASE[.ARCH].nosrc.rpm
    Example: pam-1.5.1-25.el9_6.x86_64.src.rpm -> (pam, 1.5.1-25.el9_6)
    Example: pam-1.5.1-25.el9_6.src.rpm -> (pam, 1.5.1-25.el9_6)
    Example: foo-1-1.el7.nosrc.rpm -> (foo, 1-1.el7.nosrc)
    """
    # Remove source RPM suffixes
    if source_rpm.endswith(".nosrc.rpm"):
        source_rpm = source_rpm[:-10]  # Remove .nosrc.rpm
    elif source_rpm.endswith(".src.rpm"):
        source_rpm = source_rpm[:-8]  # Remove .src.rpm

    # Known RPM architectures - only remove if last component matches these
    known_architectures = {
        "x86_64",
        "i386",
        "i486",
        "i586",
        "i686",
        "aarch64",
        "armv7hl",
        "armv7l",
        "armv6hl",
        "ppc64le",
        "ppc64",
        "s390x",
        "noarch",
    }

    # Remove architecture only if present and recognized
    if "." in source_rpm:
        possible_arch = source_rpm.rsplit(".", 1)[1]
        if possible_arch in known_architectures:
            source_rpm = source_rpm.rsplit(".", 1)[0]

    # Now split by hyphens: NAME-VERSION-RELEASE
    parts = source_rpm.split("-")
    if len(parts) >= 3:
        name = "-".join(parts[:-2])
        version = parts[-2]
        release = parts[-1]
        full_version = f"{version}-{release}"
        return name, full_version

    return None, None


def _get_rhel_distro_info(package: Package) -> tuple[str | None, str | None]:
    """Extract RHEL distribution information from RPM package.

    Returns:
        tuple: (distro_id, distro_version) where:
        - distro_id: "rpm" for RHEL packages
        - distro_version: "rhel9.6" for RHEL 9.6, "rhel8" for RHEL 8, etc.

    """
    # Check if it's a valid RPM package with release info
    if not (
        package.type == PackageType.RpmPkg
        and isinstance(package.ecosystem_data, RpmDBEntry)
        and package.ecosystem_data
        and package.ecosystem_data.release
    ):
        return None, None

    release = package.ecosystem_data.release

    # Look for RHEL pattern: .elX or .elX_Y
    if ".el" not in release:
        return None, None

    # Extract the part after .el (e.g., "9_6" from "63.el9_6")
    el_part = release.split(".el")[-1]
    if not el_part or not el_part[0].isdigit():
        return None, None
    # Parse RHEL version
    if "_" in el_part:
        # Full version: "9_6.1" -> "rhel9.6.1"
        parts = el_part.split("_")
        if len(parts) >= 2:
            major, minor = parts[0], parts[1]
            return "rpm", f"rhel{major}.{minor}"
    else:
        # Major version only: "9" -> "rhel9"
        with contextlib.suppress(ValueError):
            major = el_part
            return "rpm", f"rhel{major}"

    return None, None


def _normalize_rpm_version(version: str) -> str:
    """Normalize RPM version by adding epoch 0: if not present."""
    # Check if version already has an epoch (contains ':')
    if ":" in version:
        return version

    # Add epoch 0: if not present
    return f"0:{version}"


def _get_upstream_info_if_different(
    package: Package, upstream_package: str | None, upstream_version: str | None
) -> tuple[str | None, str | None] | None:
    if (
        upstream_package
        and upstream_version
        and (upstream_package != package.name or upstream_version != package.version)
    ):
        return (upstream_package, upstream_version)
    return None


def update_image_advisories(package: Package) -> list[Advisory]:
    distro_id = None
    distro_version = None
    if package.type in [PackageType.DebPkg, PackageType.AlpmPkg, PackageType.ApkPkg]:
        distro_id, distro_version, _ = extract_distro_info(package.p_url)
        distro_version = (
            "v" + ".".join(str(distro_version).split(".")[0:2])
            if package.type == PackageType.ApkPkg
            else str(distro_version)
        )

    if package.type == PackageType.RpmPkg:
        distro_id, distro_version = _get_rhel_distro_info(package)

    upstream_package, upstream_version = _get_upstream_info(package)
    upstream_info = _get_upstream_info_if_different(package, upstream_package, upstream_version)

    normalized_version = package.version
    if package.type == PackageType.RpmPkg:
        normalized_version = _normalize_rpm_version(package.version)
    return images_advisories.get_vulnerabilities(
        str(distro_id),
        package.name,
        normalized_version,
        distro_version,
        upstream_info,
    )


def add_package_advisories(package: Package) -> list[Advisory] | None:
    try:
        pkg_advisories = []
        if package.type in ROOT_TYPES:
            pkg_advisories = update_root_advisories(package)
        if package.type in IMAGES_TYPES:
            pkg_advisories = update_image_advisories(package)
    except ValidationError as ex:
        LOGGER.exception(
            "Unable to complete package advisories",
            extra={
                "extra": {
                    "exception": format_exception(str(ex)),
                    "location": package.locations,
                    "package_type": package.type,
                },
            },
        )
        return None
    return pkg_advisories


def complete_package_advisories_only(package: Package) -> Package:
    if pkg_advisories := add_package_advisories(package):
        package.advisories = pkg_advisories
    return package


def complete_package(package: Package) -> Package:
    try:
        if pkg_advisories := add_package_advisories(package):
            package.advisories = pkg_advisories

        completed_package = None
        if package.type in COMPLETION_MAP:
            try:
                completed_package = COMPLETION_MAP[package.type](package)

            except Exception as ex:
                LOGGER.exception(
                    "Unable to complete package",
                    extra={
                        "extra": {
                            "exception": format_exception(str(ex)),
                            "location": package.locations,
                            "package_type": package.type,
                        },
                    },
                )
                return package
        if completed_package:
            completed_package.model_validate(
                cast("ALLOWED_TYPE", package.__dict__),
            )
    except ValidationError:
        LOGGER.warning(
            "Malformed package metadata completion. "
            "Required fields are missing or data types are incorrect.",
        )
        return package

    return completed_package if completed_package is not None else package
