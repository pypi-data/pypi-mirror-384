from typing import NamedTuple

from packageurl import PackageURL
from pydantic_core import ValidationError

from labels.model.ecosystem_data.java import JavaArchive, JavaPomProject, JavaPomProperties
from labels.model.file import Location
from labels.model.package import Language, Package, PackageType
from labels.parsers.cataloger.java.utils.package import group_id_from_java_metadata
from labels.parsers.cataloger.java.utils.parse_pom_project import ParsedPomProject
from labels.parsers.cataloger.java.utils.utils import get_java_package_type_from_group_id
from labels.parsers.cataloger.utils import get_enriched_location, log_malformed_package_warning


class JavaPackageSpec(NamedTuple):
    simple_name: str | None
    version: str | None
    location: Location
    composed_name: str | None = None
    ecosystem_data: JavaArchive | None = None
    licenses: list[str] | None = None


def new_java_package(package_spec: JavaPackageSpec) -> Package | None:
    simple_name = package_spec.simple_name
    version = package_spec.version

    if not simple_name or not version:
        return None

    p_url = _get_package_url_for_java(simple_name, version, package_spec.ecosystem_data)

    name = package_spec.composed_name or simple_name

    try:
        return Package(
            name=name,
            version=version,
            locations=[package_spec.location],
            language=Language.JAVA,
            type=PackageType.JavaPkg,
            p_url=p_url,
            ecosystem_data=package_spec.ecosystem_data,
            licenses=[],
        )
    except ValidationError as ex:
        log_malformed_package_warning(package_spec.location, ex)
        return None


def new_package_from_maven_data(
    pom_properties: JavaPomProperties,
    parsed_pom_project: ParsedPomProject | None,
    location: Location,
) -> Package | None:
    artifact_id = pom_properties.artifact_id
    version = pom_properties.version

    if not artifact_id or not version:
        return None

    ecosystem_data = JavaArchive(
        pom_properties=pom_properties,
        pom_project=parsed_pom_project.java_pom_project if parsed_pom_project else None,
    )

    authoritative_group_id = (
        group_id_from_java_metadata(artifact_id, ecosystem_data) or pom_properties.group_id
    )
    authoritative_full_name = f"{authoritative_group_id}:{artifact_id}"

    new_location = get_enriched_location(location)

    try:
        return Package(
            name=authoritative_full_name,
            version=version,
            licenses=[],
            locations=[new_location],
            type=get_java_package_type_from_group_id(pom_properties.group_id),
            language=Language.JAVA,
            ecosystem_data=ecosystem_data,
            p_url=_get_package_url_for_java(artifact_id, version, ecosystem_data),
        )
    except ValidationError as ex:
        log_malformed_package_warning(new_location, ex)
        return None


def new_package_from_maven_data_v2(
    pom_properties: JavaPomProperties,
    parsed_pom_project: JavaPomProject | None,
    location: Location,
) -> Package | None:
    artifact_id = pom_properties.artifact_id
    version = pom_properties.version

    if not artifact_id or not version:
        return None

    ecosystem_data = JavaArchive(
        pom_properties=pom_properties,
        pom_project=parsed_pom_project if parsed_pom_project else None,
    )

    authoritative_group_id = (
        group_id_from_java_metadata(artifact_id, ecosystem_data) or pom_properties.group_id
    )
    authoritative_full_name = f"{authoritative_group_id}:{artifact_id}"

    new_location = get_enriched_location(location)

    try:
        return Package(
            name=authoritative_full_name,
            version=version,
            licenses=[],
            locations=[new_location],
            type=get_java_package_type_from_group_id(pom_properties.group_id),
            language=Language.JAVA,
            ecosystem_data=ecosystem_data,
            p_url=_get_package_url_for_java(artifact_id, version, ecosystem_data),
        )
    except ValidationError as ex:
        log_malformed_package_warning(new_location, ex)
        return None


def _get_package_url_for_java(
    name: str, version: str, ecosystem_data: JavaArchive | None = None
) -> str:
    group_id = name

    group_id_from_metadata = group_id_from_java_metadata(name, ecosystem_data)
    if group_id_from_metadata:
        group_id = group_id_from_metadata

    return PackageURL(type="maven", namespace=group_id, name=name, version=version).to_string()
