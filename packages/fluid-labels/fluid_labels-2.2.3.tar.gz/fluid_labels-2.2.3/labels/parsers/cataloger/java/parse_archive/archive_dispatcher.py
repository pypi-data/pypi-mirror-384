import shutil
import tempfile
from pathlib import Path

from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.java.parse_archive.archive_parser import ArchiveParser
from labels.parsers.cataloger.java.utils.archive_filename import parse_filename
from labels.utils.zip import new_zip_file_manifest

TMP_FOLDER_PREFIX = "sbom-archive-contents-"


def parse_java_archive(
    _resolver: Resolver | None,
    _environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    with tempfile.TemporaryDirectory(prefix=TMP_FOLDER_PREFIX) as tmp_dir:
        parser = _build_java_archive_parser(reader.location, tmp_dir, detect_nested=True)

        if parser is None:
            return [], []

        return parser.parse()


def _build_java_archive_parser(
    location: Location, tmp_dir: str, *, detect_nested: bool
) -> ArchiveParser | None:
    if not location.coordinates:
        return None

    current_file_path = location.coordinates.real_path
    temp_archive_path = _setup_archive_tpm_dir(current_file_path, tmp_dir)

    file_info = parse_filename(current_file_path)
    file_manifest = new_zip_file_manifest(temp_archive_path)

    return ArchiveParser(
        file_manifest=file_manifest,
        location=location,
        archive_path=temp_archive_path,
        file_info=file_info,
        detect_nested=detect_nested,
    )


def _setup_archive_tpm_dir(archive_virtual_path: str, tmp_dir: str) -> str:
    name = Path(archive_virtual_path).name

    archive_path = Path(tmp_dir, f"archive-{name}")
    shutil.copy(archive_virtual_path, archive_path)

    return str(archive_path)
