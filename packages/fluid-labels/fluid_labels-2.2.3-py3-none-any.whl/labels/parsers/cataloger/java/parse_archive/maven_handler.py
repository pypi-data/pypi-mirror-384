import re
from pathlib import Path
from typing import NamedTuple
from zipfile import ZipInfo

from bs4 import BeautifulSoup, Tag

from labels.model.ecosystem_data.java import (
    JavaArchive,
    JavaManifest,
    JavaPomParent,
    JavaPomProject,
    JavaPomProperties,
)
from labels.model.file import Location
from labels.model.package import Package
from labels.parsers.cataloger.java.utils.archive_filename import ArchiveFilename
from labels.parsers.cataloger.java.utils.maven_repo_utils import get_direct_child_text
from labels.parsers.cataloger.java.utils.package_builder import new_package_from_maven_data_v2
from labels.parsers.cataloger.java.utils.parse_java_manifest import select_name, select_version
from labels.parsers.cataloger.java.utils.parse_pom_project import _safe_string
from labels.utils.zip import contents_from_zip, new_zip_glob_match


class JavaPackageIdentity(NamedTuple):
    artifact_id: str | None
    version: str | None
    group_id: str | None


class MavenHandler:
    def __init__(
        self,
        *,
        file_manifest: list[ZipInfo],
        archive_path: str,
        location: Location,
        file_info: ArchiveFilename,
    ) -> None:
        self.file_manifest = file_manifest
        self.archive_path = archive_path
        self.location = location
        self.file_info = file_info
        self._properties_cache: dict[str, JavaPomProperties] | None = None
        self._projects_cache: dict[str, JavaPomProject] | None = None

    def discover_auxiliary_packages(self, parent_package: Package) -> list[Package]:
        properties = self._load_properties()
        projects = self._load_projects()

        packages = []
        for parent_path, properties_obj in properties.items():
            pom_project = projects.get(parent_path)

            package = new_package_from_maven_data_v2(properties_obj, pom_project, self.location)
            if package and not self._same_as_parent_package(parent_package, package):
                packages.append(package)

        return packages

    def _same_as_parent_package(self, parent_package: Package, package: Package) -> bool:
        return package.name == parent_package.name and package.version == parent_package.version

    def extract_identity(self, manifest: JavaManifest) -> JavaPackageIdentity:
        properties = self._load_properties()
        projects = self._load_projects()
        props_obj, proj_obj = self._find_matching_objects(properties, projects)

        artifact_id = None
        version = None
        group_id = None

        if props_obj:
            artifact_id = props_obj.artifact_id
            version = props_obj.version
            group_id = props_obj.group_id

        if proj_obj and not version:
            version = proj_obj.version

        artifact_id = artifact_id or select_name(manifest, self.file_info)
        version = version or select_version(manifest, self.file_info)
        group_id = group_id or select_name(manifest, self.file_info)

        return JavaPackageIdentity(artifact_id=artifact_id, version=version, group_id=group_id)

    def _find_matching_objects(
        self, properties: dict[str, JavaPomProperties], projects: dict[str, JavaPomProject]
    ) -> tuple[JavaPomProperties | None, JavaPomProject | None]:
        artifacts_map = {props.artifact_id for props in properties.values() if props.artifact_id}

        for parent_path, properties_obj in properties.items():
            if properties_obj.artifact_id:
                artifact_matches_filename = self._artifact_id_matches_filename(
                    properties_obj.artifact_id, self.file_info.name, artifacts_map
                )
                project_object = projects.get(parent_path)
                if artifact_matches_filename and project_object:
                    return properties_obj, project_object

        return None, None

    def _artifact_id_matches_filename(
        self, artifact_id: str, filename: str, artifacts_map: set[str]
    ) -> bool:
        if filename in artifacts_map:
            return artifact_id == filename

        return artifact_id.startswith(filename) or filename.endswith(artifact_id)

    def build_ecosystem_data(self, manifest: JavaManifest) -> JavaArchive:
        properties = self._load_properties()
        projects = self._load_projects()
        props_obj, proj_obj = self._find_matching_objects(properties, projects)

        return JavaArchive(
            manifest=manifest,
            pom_properties=props_obj,
            pom_project=proj_obj if proj_obj else None,
        )

    def _load_properties(self) -> dict[str, JavaPomProperties]:
        if self._properties_cache is None:
            matches = new_zip_glob_match(
                self.file_manifest, ("*pom.properties",), case_sensitive=False
            )
            self._properties_cache = self._pom_properties_by_parent(self.archive_path, matches)
        return self._properties_cache or {}

    def _pom_properties_by_parent(
        self, archive_path: str, extract_paths: list[str]
    ) -> dict[str, JavaPomProperties]:
        properties_by_parent_path = {}
        contents_of_maven_properties = contents_from_zip(archive_path, *extract_paths)

        for file_path, file_contents in contents_of_maven_properties.items():
            if not file_contents:
                continue

            pom_properties = self._parse_pom_properties(file_contents)

            if not pom_properties.group_id:
                continue

            properties_by_parent_path[str(Path(file_path).parent)] = pom_properties

        return properties_by_parent_path

    def _parse_pom_properties(self, file_content: str) -> JavaPomProperties:
        properties_map = {}

        for raw_line in file_content.splitlines():
            line = raw_line.strip()

            if line == "" or line.lstrip().startswith("#"):
                continue

            idx = next((i for i in range(len(line)) if line[i] in ":="), -1)
            if idx == -1:
                continue

            key = line[:idx].strip()
            value = line[idx + 1 :].strip()
            properties_map[key] = value

        converted_props = {}
        for raw_key, value in properties_map.items():
            key = re.sub(r"(?<!^)(?=[A-Z])", "_", raw_key).lower()
            if key in set(JavaPomProperties.__annotations__.keys()):
                converted_props[key] = value

        return JavaPomProperties(**converted_props)

    def _load_projects(self) -> dict[str, JavaPomProject]:
        if self._projects_cache is None:
            matches = new_zip_glob_match(self.file_manifest, ("*pom.xml",), case_sensitive=False)
            self._projects_cache = self._pom_project_by_parent(self.archive_path, matches)
        return self._projects_cache or {}

    def _pom_project_by_parent(
        self, archive_path: str, extract_paths: list[str]
    ) -> dict[str, JavaPomProject]:
        contents_of_maven_project = contents_from_zip(archive_path, *extract_paths)

        project_by_parent = {}

        for file_path, file_contents in contents_of_maven_project.items():
            pom_project = self._parse_pom_xml_project(file_contents)
            if not pom_project:
                continue

            if (not pom_project.parent and not pom_project.version) or not pom_project.artifact_id:
                continue

            project_by_parent[str(Path(file_path).parent)] = pom_project

        return project_by_parent

    def _parse_pom_xml_project(self, reader: str) -> JavaPomProject | None:
        project = BeautifulSoup(reader, features="xml").project
        if not project:
            return None

        return self._build_pom_project(project)

    def _build_pom_project(self, project: Tag) -> JavaPomProject:
        artifact_id = _safe_string(self._find_direct_child(project, "artifactId"))
        name = _safe_string(self._find_direct_child(project, "name"))

        licenses: list[str] = []
        if project.licenses:
            for license_ in project.licenses.find_all("license"):
                license_name: str | None = None
                license_url: str | None = None
                if name_node := license_.find_next("name"):
                    license_name = name_node.get_text()
                elif url_node := license_.find_next("url"):
                    license_url = url_node.get_text()

                license_value = license_name or license_url
                if license_value is None:
                    continue

                licenses.append(license_value)

        return JavaPomProject(
            parent=self._build_pom_parent(self._find_direct_child(project, "parent")),
            group_id=_safe_string(self._find_direct_child(project, "groupId")),
            artifact_id=artifact_id,
            version=_safe_string(self._find_direct_child(project, "version")),
            name=name,
            licenses=licenses,
        )

    def _build_pom_parent(self, parent: Tag | None) -> JavaPomParent | None:
        if not parent:
            return None

        group_id = get_direct_child_text(parent, "groupId")
        artifact_id = get_direct_child_text(parent, "artifactId")
        version = get_direct_child_text(parent, "version")

        if (
            not group_id
            or not artifact_id
            or not version
            or not group_id.strip()
            or not artifact_id.strip()
            or not version.strip()
        ):
            return None

        return JavaPomParent(
            group_id=group_id,
            artifact_id=artifact_id,
            version=version,
        )

    def _find_direct_child(self, parent: Tag, tag: str) -> Tag | None:
        return next(
            (child for child in parent.find_all(tag, recursive=False) if child.parent == parent),
            None,
        )
