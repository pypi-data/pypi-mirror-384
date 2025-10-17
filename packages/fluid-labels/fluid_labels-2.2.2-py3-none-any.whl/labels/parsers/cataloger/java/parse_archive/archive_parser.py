import logging
import tempfile
import zipfile
from contextlib import suppress
from pathlib import Path
from zipfile import ZipInfo

from pydantic import BaseModel, ConfigDict, ValidationError

from labels.model.ecosystem_data.java import JavaArchive, JavaManifest, JavaPomProperties
from labels.model.file import Location
from labels.model.package import Language, Package
from labels.model.relationship import Relationship, RelationshipType
from labels.parsers.cataloger.java.utils.archive_filename import ArchiveFilename, parse_filename
from labels.parsers.cataloger.java.utils.integrity import artifact_id_matches_filename
from labels.parsers.cataloger.java.utils.package import group_id_from_java_metadata, package_url
from labels.parsers.cataloger.java.utils.package_builder import new_package_from_maven_data
from labels.parsers.cataloger.java.utils.parse_java_manifest import (
    parse_java_manifest,
    select_licenses,
    select_name,
    select_version,
)
from labels.parsers.cataloger.java.utils.parse_pom_project import (
    ParsedPomProject,
    pom_project_by_parent,
)
from labels.parsers.cataloger.java.utils.parse_pom_properties import pom_properties_by_parent
from labels.parsers.cataloger.utils import get_enriched_location, log_malformed_package_warning
from labels.utils.licenses import parser
from labels.utils.zip import (
    contents_from_zip,
    new_zip_file_manifest,
    traverse_files_in_zip,
    zip_glob_match,
)

LOGGER = logging.getLogger(__name__)


class ArchiveParser(BaseModel):
    file_manifest: list[ZipInfo]
    location: Location
    archive_path: str | None
    file_info: ArchiveFilename
    detect_nested: bool
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def parse(self) -> tuple[list[Package], list[Relationship]]:
        packages = []
        relationships = []

        parent_pkg = self.discover_main_package()

        # Process aux packages from Maven files (even if no parent package)
        aux_pkgs = self.discover_pkgs_from_all_maven_files(parent_pkg)

        if parent_pkg:
            packages.append(parent_pkg)

            for aux_pkg in aux_pkgs:
                packages.append(aux_pkg)
                relationships.append(
                    Relationship(
                        from_=aux_pkg.id_,
                        to_=parent_pkg.id_,
                        type=RelationshipType.CONTAINS_RELATIONSHIP,
                    )
                )
        else:
            # If no parent package, add aux packages without relationships
            packages.extend(aux_pkgs)

        if self.detect_nested:
            nested_pkgs, nested_relationships = self.discover_pkgs_from_nested_archives()
            packages.extend(nested_pkgs)
            relationships.extend(nested_relationships)
        else:
            # Check for nested archives and log warning if found
            nested_archives = zip_glob_match(
                self.file_manifest, case_sensitive=False, patterns=("*.jar", "*.war")
            )
            if nested_archives:
                LOGGER.warning(
                    "nested archives not cataloged: %s", ", ".join(sorted(nested_archives))
                )

        return packages, relationships

    def discover_pkgs_from_nested_archives(self) -> tuple[list[Package], list[Relationship]]:
        if not self.archive_path:
            return [], []

        # Find nested Java archives
        nested_archives = zip_glob_match(
            self.file_manifest,
            case_sensitive=False,
            patterns=(
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
            ),
        )

        if not nested_archives:
            return [], []

        packages = []
        relationships = []

        for archive_path in nested_archives:
            try:
                # Extract the nested archive
                nested_pkgs, nested_rels = self._process_nested_archive(archive_path)
                packages.extend(nested_pkgs)
                relationships.extend(nested_rels)
            except (OSError, ValueError, KeyError) as e:
                LOGGER.warning("unable to process nested archive %s: %s", archive_path, e)
                continue
        return packages, relationships

    def _process_nested_archive(
        self, archive_path: str
    ) -> tuple[list[Package], list[Relationship]]:
        if not self.archive_path:
            return [], []

        try:
            # Extract the nested archive to a temporary location
            # For binary files like .jar, we need to extract as bytes, not text
            nested_content_bytes = self._extract_binary_from_zip(self.archive_path, archive_path)
            if not nested_content_bytes:
                return [], []

            # Create a temporary file for the nested archive
            with tempfile.NamedTemporaryFile(
                suffix=f"_{Path(archive_path).name}", delete=False
            ) as temp_file:
                temp_file.write(nested_content_bytes)
                temp_archive_path = temp_file.name

            try:
                # Create a new location for the nested archive
                nested_location = Location(
                    coordinates=self.location.coordinates,
                    access_path=f"{self.location.access_path}:{archive_path}",
                )

                # Create a new parser for the nested archive
                nested_parser = ArchiveParser(
                    file_manifest=new_zip_file_manifest(temp_archive_path),
                    location=nested_location,
                    archive_path=temp_archive_path,
                    file_info=parse_filename(archive_path),
                    detect_nested=True,
                )

                nested_pkgs, nested_rels = nested_parser.parse()

                return nested_pkgs or [], nested_rels or []

            finally:
                with suppress(OSError):
                    Path(temp_archive_path).unlink()

        except (OSError, ValueError, KeyError) as e:
            LOGGER.debug("error processing nested archive %s: %s", archive_path, e)
            return [], []

    def _extract_binary_from_zip(self, archive_path: str, file_path: str) -> bytes | None:
        """Extract a binary file from a zip archive using existing zip utilities."""
        try:
            result = None

            def visitor(file: zipfile.ZipInfo) -> None:
                nonlocal result
                if not file.is_dir():
                    with (
                        zipfile.ZipFile(archive_path, "r") as zip_reader,
                        zip_reader.open(file) as file_data,
                    ):
                        result = file_data.read()

            traverse_files_in_zip(archive_path, visitor, file_path)
        except (OSError, ValueError, KeyError) as e:
            LOGGER.debug("Error extracting binary file %s: %s", file_path, e)
            return None
        return result

    def discover_pkgs_from_all_maven_files(self, parent_pkg: Package | None) -> list[Package]:
        if not parent_pkg or not self.archive_path:
            return []
        pkgs: list[Package] = []

        properties = pom_properties_by_parent(
            self.archive_path,
            zip_glob_match(self.file_manifest, case_sensitive=False, patterns=("*pom.properties",)),
        )

        projects = pom_project_by_parent(
            self.archive_path,
            self.location,
            zip_glob_match(self.file_manifest, case_sensitive=False, patterns=("*pom.xml",)),
        )

        for parent_path, properties_obj in properties.items():
            pom_project: ParsedPomProject | None = projects.get(parent_path, None)
            if pkg_from_pom := new_package_from_maven_data(
                properties_obj, pom_project, self.location
            ):
                pkgs.append(pkg_from_pom)
        return pkgs

    def discover_main_package(self) -> Package | None:
        manifest_matches = zip_glob_match(
            self.file_manifest,
            case_sensitive=False,
            patterns=("/META-INF/MANIFEST.MF",),
        )

        # Early validation checks
        if len(manifest_matches) != 1:
            if len(manifest_matches) > 1:
                LOGGER.error("found multiple manifests in the jar: %s", manifest_matches)
            else:
                LOGGER.warning("no manifests found in the jar")
            return None

        if not self.archive_path or not (
            contents := contents_from_zip(self.archive_path, *manifest_matches)
        ):
            return None

        manifest_contents = contents[manifest_matches[0]]
        manifest = parse_java_manifest(manifest_contents)

        if not manifest or (manifest.main and "Weave-Classes" in manifest.main):
            if not manifest:
                LOGGER.warning("failed to parse java manifest: %s", self.location)  # type: ignore[unreachable]
            else:
                LOGGER.warning(
                    "excluding archive due to Weave-Classes manifest entry: %s", self.location
                )
            return None

        licenses_, name, version, group_id = self.parse_licenses(manifest)
        if not name or not version:
            return None

        # Extract pom_properties and pom_project to include in ecosystem_data
        properties, projects = self.extract_properties_and_projects()
        properties_obj, project_obj = self.find_relevant_objects(properties, projects)

        # Build ecosystem_data with all available metadata
        ecosystem_data = JavaArchive(
            manifest=manifest,
            pom_properties=properties_obj,
            pom_project=project_obj.java_pom_project if project_obj else None,
        )

        new_location = get_enriched_location(self.location)

        try:
            authoritative_group_id = group_id_from_java_metadata(name, ecosystem_data) or group_id
            return Package(
                name=f"{authoritative_group_id}:{name}",
                version=version,
                licenses=licenses_,
                locations=[new_location],
                type=self.file_info.pkg_type(),
                language=Language.JAVA,
                ecosystem_data=ecosystem_data,
                p_url=package_url(name, version, ecosystem_data),
            )
        except ValidationError as ex:
            log_malformed_package_warning(new_location, ex)
            return None

    def get_license_from_file_in_archive(self) -> list[str]:
        file_licenses = []
        for filename in parser.LICENSES_FILE_NAMES:
            license_matches = zip_glob_match(
                self.file_manifest,
                case_sensitive=True,
                patterns=(f"/META-INF/{filename}",),
            )
            if not license_matches:
                license_matches = zip_glob_match(
                    self.file_manifest,
                    case_sensitive=True,
                    patterns=(f"/{filename}",),
                )

            if license_matches and self.archive_path:
                contents = contents_from_zip(self.archive_path, *license_matches)
                for license_match in license_matches:
                    license_contents = contents.get(license_match, "")

                    parsed = parser.parse_license(license_contents)
                    if parsed:
                        file_licenses.extend(parsed)

        return file_licenses

    def parse_licenses(self, manifest: JavaManifest) -> tuple[list[str], str, str, str]:
        licenses_ = select_licenses(manifest)
        (
            name,
            version,
            pom_licenses,
            group_id,
        ) = self.guess_main_package_name_and_version_from_pom()

        if not name:
            name = select_name(manifest, self.file_info)
        if not version:
            version = select_version(manifest, self.file_info)
        if not group_id:
            group_id = select_name(manifest, self.file_info)

        if not licenses_:
            licenses_.extend(pom_licenses or [])

        if not licenses_:
            file_licenses = self.get_license_from_file_in_archive()
            if file_licenses:
                licenses_.extend(file_licenses)

        return licenses_, name, version, group_id

    def extract_properties_and_projects(
        self,
    ) -> tuple[dict[str, JavaPomProperties], dict[str, ParsedPomProject]]:
        properties = {}
        projects = {}

        pom_property_matches = zip_glob_match(
            self.file_manifest,
            case_sensitive=False,
            patterns=("*pom.properties",),
        )
        pom_matches = zip_glob_match(
            self.file_manifest,
            case_sensitive=False,
            patterns=("*pom.xml",),
        )
        if self.archive_path:
            properties = pom_properties_by_parent(self.archive_path, pom_property_matches)
            projects = pom_project_by_parent(self.archive_path, self.location, pom_matches)

        return properties, projects

    def find_relevant_objects(
        self,
        properties: dict[str, JavaPomProperties],
        projects: dict[str, ParsedPomProject],
    ) -> tuple[JavaPomProperties | None, ParsedPomProject | None]:
        # Create artifacts map for exact matching
        artifacts_map = {props.artifact_id for props in properties.values() if props.artifact_id}

        for parent_path, properties_obj in properties.items():
            if (
                properties_obj.artifact_id
                and artifact_id_matches_filename(
                    properties_obj.artifact_id, self.file_info.name, artifacts_map
                )
                and (proj := projects.get(parent_path))
            ):
                return properties_obj, proj
        return None, None

    def extract_name_version(
        self,
        properties_obj: JavaPomProperties,
        project_obj: ParsedPomProject,
    ) -> tuple[str | None, str | None, str | None]:
        name = properties_obj.artifact_id if properties_obj else None
        version = properties_obj.version if properties_obj else None
        group_id = properties_obj.group_id if properties_obj else None

        if not name and project_obj:
            name = project_obj.java_pom_project.artifact_id
        if not version and project_obj:
            version = project_obj.java_pom_project.version
        if not group_id and project_obj:
            group_id = project_obj.java_pom_project.group_id

        return name, version, group_id

    def guess_main_package_name_and_version_from_pom(
        self,
    ) -> tuple[str | None, str | None, list[str] | None, str | None]:
        properties, projects = self.extract_properties_and_projects()
        properties_obj, project_obj = self.find_relevant_objects(properties, projects)

        if not properties_obj or not project_obj:
            return None, None, None, None

        name, version, group_id = self.extract_name_version(properties_obj, project_obj)

        return name, version, [], group_id
