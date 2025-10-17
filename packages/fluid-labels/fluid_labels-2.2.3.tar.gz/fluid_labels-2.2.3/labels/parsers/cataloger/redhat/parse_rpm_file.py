import logging
import struct
from pathlib import Path
from typing import BinaryIO

from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.redhat.package_builder import new_redhat_package
from labels.parsers.cataloger.redhat.rpmdb.domain.entry import IndexEntry, header_import
from labels.parsers.cataloger.redhat.rpmdb.domain.package import get_nevra

LOGGER = logging.getLogger(__name__)


def parse_rpm_file(
    _: Resolver,
    env: Environment,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    """Parse an individual .rpm file to extract package metadata.

    An RPM file structure:
    - Lead (96 bytes) - legacy header
    - Signature Header - signatures and checksums
    - Header - package metadata (what we need)
    - Payload - compressed files
    """
    packages: list[Package] = []
    relationships: list[Relationship] = []

    packages = _collect_packages(reader.location, env)

    return packages, relationships


def _collect_packages(location: Location, env: Environment) -> list[Package]:
    packages: list[Package] = []

    if not location.coordinates:
        return packages

    try:
        with Path(location.coordinates.real_path).open("rb") as rpm_file:
            rpm_file.seek(96)  # Skip the lead (96 bytes)

            index_entries = _parse_rpm_header(rpm_file)
            if not index_entries:
                return packages

            package_info = get_nevra(index_entries)
            package = new_redhat_package(entry=package_info, env=env, location=location)
            if package:
                packages.append(package)

    except (OSError, ValueError, struct.error) as ex:
        LOGGER.warning("Failed to parse RPM file %s: %s", location.coordinates.real_path, ex)

    return packages


def _parse_rpm_header(f: BinaryIO) -> list[IndexEntry] | None:
    if not _skip_signature_section(f):
        return None

    header_data = _read_main_header_block(f)

    if not header_data:
        return None

    return header_import(header_data)


def _skip_signature_section(f: BinaryIO) -> bool:
    magic = f.read(8)
    if len(magic) < 8 or not _has_rpm_header_magic(magic):
        return False

    index_length = _read_u32_be(f)
    data_length = _read_u32_be(f)
    f.seek(index_length * 16 + data_length, 1)
    _align_to_8_bytes(f)

    return True


def _align_to_8_bytes(f: BinaryIO) -> None:
    pos = f.tell()
    f.seek((8 - (pos % 8)) % 8, 1)


def _read_main_header_block(f: BinaryIO) -> bytes | None:
    magic = f.read(8)
    if len(magic) < 8 or not _has_rpm_header_magic(magic):
        return None

    index_length = _read_u32_be(f)
    data_length = _read_u32_be(f)
    total = 8 + (index_length * 16) + data_length
    f.seek(-8, 1)

    data = f.read(total)

    return data if len(data) >= total else None


def _read_u32_be(f: BinaryIO) -> int:
    return int.from_bytes(f.read(4), "big")


def _has_rpm_header_magic(buf: bytes) -> bool:
    return len(buf) >= 3 and buf[:3] == b"\x8e\xad\xe8"
