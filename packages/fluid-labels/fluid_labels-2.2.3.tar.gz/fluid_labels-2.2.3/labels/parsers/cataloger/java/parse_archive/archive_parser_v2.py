import logging
import tempfile
from collections.abc import Generator
from contextlib import contextmanager, suppress
from pathlib import Path
from zipfile import ZipFile, ZipInfo

from labels.model.ecosystem_data.java import JavaArchive
from labels.model.file import Location
from labels.model.package import Package
from labels.model.relationship import Relationship, RelationshipType
from labels.parsers.cataloger.java.parse_archive.license_extractor import LicenseExtractor
from labels.parsers.cataloger.java.parse_archive.manifest_parser import ManifestParser
from labels.parsers.cataloger.java.parse_archive.maven_handler import (
    JavaPackageIdentity,
    MavenHandler,
)
from labels.parsers.cataloger.java.utils.archive_filename import ArchiveFilename, parse_filename
from labels.parsers.cataloger.java.utils.package import group_id_from_java_metadata
from labels.parsers.cataloger.java.utils.package_builder import JavaPackageSpec, new_java_package
from labels.parsers.cataloger.utils import get_enriched_location
from labels.utils.zip import new_zip_file_manifest, new_zip_glob_match, traverse_files_in_zip

LOGGER = logging.getLogger(__name__)

NESTED_FILES_EXTENSIONS = (
    "*.jar",
    "*.war",
    "*.ear",
    "*.par",
    "*.sar",
    "*.nar",
    "*.jpi",
    "*.hpi",
    "*.kar",
    "*.lpkg",
)


class ArchiveParser:
    def __init__(
        self,
        *,
        file_manifest: list[ZipInfo],
        location: Location,
        archive_path: str,
        file_info: ArchiveFilename,
        detect_nested: bool,
    ) -> None:
        self.file_manifest = file_manifest
        self.location = location
        self.archive_path = archive_path
        self.file_info = file_info
        self.detect_nested = detect_nested

        self.manifest_parser = ManifestParser(
            file_manifest=file_manifest,
            archive_path=archive_path,
            location=location,
        )
        self.maven_handler = MavenHandler(
            file_manifest=file_manifest,
            archive_path=archive_path,
            location=location,
            file_info=file_info,
        )
        self.license_extractor = LicenseExtractor(
            file_manifest=file_manifest,
            archive_path=archive_path,
        )
        self.nested_handler = NestedArchiveHandler(
            file_manifest=file_manifest,
            archive_path=archive_path,
            location=location,
        )

    def parse(self) -> tuple[list[Package], list[Relationship]]:
        packages: list[Package] = []
        relationships: list[Relationship] = []

        parent_package = self._discover_main_package()

        if parent_package:
            auxiliary_packages = self.maven_handler.discover_auxiliary_packages(parent_package)
            packages.append(parent_package)

            for auxiliary_package in auxiliary_packages:
                packages.append(auxiliary_package)
                relationships.append(
                    Relationship(
                        from_=auxiliary_package.id_,
                        to_=parent_package.id_,
                        type=RelationshipType.CONTAINS_RELATIONSHIP,
                    )
                )

        if self.detect_nested:
            nested_packages, nested_relationships = self.nested_handler.discover_packages()
            packages.extend(nested_packages)
            relationships.extend(nested_relationships)

        return packages, relationships

    def _discover_main_package(self) -> Package | None:
        manifest = self.manifest_parser.parse()
        if not manifest:
            return None

        licenses = self.license_extractor.extract_all(manifest)
        package_identity = self.maven_handler.extract_identity(manifest)
        ecosystem_data = self.maven_handler.build_ecosystem_data(manifest)
        package_spec = self._build_package_spec(package_identity, licenses, ecosystem_data)

        return new_java_package(package_spec)

    def _build_package_spec(
        self,
        package_identity: JavaPackageIdentity,
        licenses: list[str],
        ecosystem_data: JavaArchive,
    ) -> JavaPackageSpec:
        artifact_id = package_identity.artifact_id
        version = package_identity.version
        group_id = package_identity.group_id

        new_location = get_enriched_location(self.location)

        authoritative_group_id = (
            group_id_from_java_metadata(artifact_id, ecosystem_data) or group_id
        )

        return JavaPackageSpec(
            simple_name=artifact_id,
            version=version,
            location=new_location,
            composed_name=f"{authoritative_group_id}:{artifact_id}",
            ecosystem_data=ecosystem_data,
            licenses=licenses,
        )


class NestedArchiveHandler:
    def __init__(
        self, *, file_manifest: list[ZipInfo], archive_path: str, location: Location
    ) -> None:
        self.file_manifest = file_manifest
        self.archive_path = archive_path
        self.location = location

    def discover_packages(self) -> tuple[list[Package], list[Relationship]]:
        nested_paths = self._find_nested_archives()
        if not nested_paths:
            return [], []

        packages: list[Package] = []
        relationships: list[Relationship] = []
        for path in nested_paths:
            try:
                nested_packages, nested_relationships = self._process_single_archive(path)
                packages.extend(nested_packages)
                relationships.extend(nested_relationships)
            except (OSError, ValueError, KeyError):
                LOGGER.exception("Unable to process nested archive %s:", path)
                continue

        return packages, relationships

    def _find_nested_archives(self) -> list[str]:
        return new_zip_glob_match(self.file_manifest, NESTED_FILES_EXTENSIONS, case_sensitive=True)

    def _process_single_archive(
        self, archive_path: str
    ) -> tuple[list[Package], list[Relationship]]:
        nested_bytes = self._extract_archive_bytes(archive_path)
        if not nested_bytes:
            return [], []

        with self._create_temp_file(archive_path, nested_bytes) as temp_path:
            nested_location = Location(
                coordinates=self.location.coordinates,
                access_path=f"{self.location.access_path}:{archive_path}",
            )

            nested_parser = ArchiveParser(
                file_manifest=new_zip_file_manifest(temp_path),
                location=nested_location,
                archive_path=temp_path,
                file_info=parse_filename(archive_path),
                detect_nested=True,
            )

            return nested_parser.parse()

    def _extract_archive_bytes(self, file_path: str) -> bytes | None:
        try:
            result = None

            def visitor(file: ZipInfo) -> None:
                nonlocal result
                if not file.is_dir():
                    with (
                        ZipFile(self.archive_path, "r") as zip_reader,
                        zip_reader.open(file) as file_data,
                    ):
                        result = file_data.read()

            traverse_files_in_zip(self.archive_path, visitor, file_path)
        except (OSError, ValueError, KeyError) as ex:
            LOGGER.debug("Error extracting binary file %s: %s", file_path, ex)
            return None
        else:
            return result

    @contextmanager
    def _create_temp_file(self, archive_path: str, content: bytes) -> Generator[str]:
        suffix = f"_{Path(archive_path).name}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            temp_path = tmp.name

        try:
            yield temp_path
        finally:
            with suppress(OSError):
                Path(temp_path).unlink()
