import logging
import os
import stat
import tempfile
import zipfile
from pathlib import Path

from labels.model.ecosystem_data.java import JavaArchive, JavaPomProperties
from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.java.utils.package_builder import JavaPackageSpec, new_java_package
from labels.parsers.cataloger.utils import get_enriched_location

LOGGER = logging.getLogger(__name__)


def parse_apk(
    _resolver: Resolver | None,
    _environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_paths = _extract_apk_to_tempdir(reader, tmp_dir)
        if not file_paths:
            return packages, relationships

        packages = _collect_packages(file_paths, reader.location)

    return packages, relationships


def _extract_apk_to_tempdir(reader: LocationReadCloser, output_folder: str) -> list[Path]:
    files_paths: list[Path] = []
    try:
        with zipfile.ZipFile(reader.read_closer.name, "r") as apk_file:
            _safe_extract(apk_file, output_folder)
    except zipfile.BadZipFile:
        return files_paths

    meta_dir_path = Path(output_folder) / "META-INF"
    if meta_dir_path.exists():
        files_paths = [
            file_path
            for file_path in meta_dir_path.iterdir()
            if file_path.name.endswith(".version")
        ]

    return files_paths


def _safe_extract(apk_file: zipfile.ZipFile, destination: str) -> None:
    for file_info in apk_file.infolist():
        file_name = file_info.filename
        if Path(file_name).is_absolute() or file_name.startswith(("..", "./")):
            continue

        target_path = Path(destination, file_name)

        if not _is_safe_path(destination, str(target_path)):
            continue

        if (file_info.external_attr >> 16) & stat.S_IFLNK:
            continue

        try:
            apk_file.extract(file_name, destination)
        except Exception:
            LOGGER.exception("Error extracting %s", file_name)


def _is_safe_path(base_path: str, target_path: str) -> bool:
    base_path = os.path.normpath(base_path)
    target_path = os.path.normpath(target_path)
    return os.path.commonpath([base_path]) == os.path.commonpath([base_path, target_path])


def _collect_packages(file_paths: list[Path], location: Location) -> list[Package]:
    packages: list[Package] = []

    for file_path in file_paths:
        result = _read_version_and_ids(file_path)
        if not result:
            continue

        group_id, artifact_id, version = result

        java_archive = JavaArchive(
            pom_properties=JavaPomProperties(
                group_id=group_id,
                artifact_id=artifact_id,
                version=version,
            ),
        )

        new_location = get_enriched_location(location)

        package_spec = JavaPackageSpec(
            simple_name=artifact_id,
            composed_name=f"{group_id}:{artifact_id}",
            version=version,
            location=new_location,
            ecosystem_data=java_archive,
        )

        package = new_java_package(package_spec)
        if package:
            packages.append(package)

    return packages


def _read_version_and_ids(file_path: Path) -> tuple[str, str, str] | None:
    with file_path.open(encoding="utf-8") as f:
        version = f.read().strip()

    parts = file_path.name.replace(".version", "").split("_", 1)

    if len(parts) < 2 or not version:
        return None

    group_id, artifact_id = parts

    if not group_id or not artifact_id:
        return None

    group_id, artifact_id = parts

    return group_id, artifact_id, version
