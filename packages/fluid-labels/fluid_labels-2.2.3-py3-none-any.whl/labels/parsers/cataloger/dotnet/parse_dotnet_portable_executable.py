import re

import packaging.version
import pefile

from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.dotnet.package_builder import new_dotnet_package

SPACE_REGEX = re.compile(r"[\s]+")
NUMBER_REGEX = re.compile(r"\d")
VERSION_PUNCTUATION_REGEX = re.compile(r"[.,]+")


def parse_dotnet_portable_executable(
    _resolver: Resolver | None,
    _env: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    pe_representation = _safe_parse_version_pe_file(reader)
    if not pe_representation:
        return packages, relationships

    packages = _collect_packages(pe_representation, reader.location)

    return packages, relationships


def _safe_parse_version_pe_file(reader: LocationReadCloser) -> pefile.PE | None:
    if not reader.location.coordinates:
        return None

    try:
        pe_representation = pefile.PE(reader.location.coordinates.real_path, fast_load=False)
    except pefile.PEFormatError:
        return None

    return pe_representation


def _collect_packages(pe_representation: pefile.PE, location: Location) -> list[Package]:
    packages: list[Package] = []

    version_resource = _parse_version_resource(pe_representation)
    if not version_resource:
        return packages

    name = _find_name(version_resource)
    version = _find_version(version_resource)

    dotnet_package = new_dotnet_package(name, version, location)
    if dotnet_package:
        packages.append(dotnet_package)

    return packages


def _parse_version_resource(portable: pefile.PE) -> dict[str, str] | None:
    if not hasattr(portable, "VS_VERSIONINFO"):
        return None

    for idx, _ in enumerate(portable.VS_VERSIONINFO):
        if not hasattr(portable, "FileInfo") or len(portable.FileInfo) <= idx:
            continue

        parsed_file_info = _process_file_info(portable.FileInfo[idx])
        if parsed_file_info:
            return parsed_file_info

    return None


def _process_file_info(
    file_info: list["pefile._StringFileInfo"],
) -> dict[str, str] | None:
    for entry in file_info:
        if not hasattr(entry, "StringTable"):
            continue

        parsed_file_info = _process_string_table(entry.StringTable)
        if parsed_file_info:
            return parsed_file_info

    return None


def _process_string_table(
    string_table: list["pefile._StringTable"],
) -> dict[str, str]:
    string_table_dict: dict[str, str] = {}

    for string_table_entry in string_table:
        string_table_dict["LangID"] = string_table_entry.LangID.decode("utf-8")
        for key, value in string_table_entry.entries.items():
            string_table_dict[key.decode("utf-8")] = value.decode("utf-8")

    return string_table_dict


def _find_name(version_resources: dict[str, str]) -> str:
    name_fields = [
        "ProductName",
        "FileDescription",
        "InternalName",
        "OriginalFilename",
    ]

    if _is_microsoft(version_resources):
        name_fields = [
            "FileDescription",
            "InternalName",
            "OriginalFilename",
            "ProductName",
        ]

    for field in name_fields:
        value = _space_normalize(version_resources.get(field, ""))
        if value:
            return value

    return ""


def _is_microsoft(version_resources: dict[str, str]) -> bool:
    company_name = version_resources.get("CompanyName", "").lower()
    product_name = version_resources.get("ProductName", "").lower()

    return "microsoft" in company_name or "microsoft" in product_name


def _space_normalize(value: str) -> str:
    value = value.strip()

    if value == "":
        return ""

    value = value.encode("utf-8", "replace").decode("utf-8")

    value = SPACE_REGEX.sub(" ", value)

    value = re.sub(r"[\x00-\x1f]", "", value)

    value = SPACE_REGEX.sub(" ", value)

    return value.strip()


def _find_version(version_resources: dict[str, str]) -> str:
    raw_product_version = version_resources.get("ProductVersion", "")
    raw_file_version = version_resources.get("FileVersion", "")

    product_version = _extract_version(raw_product_version)
    file_version = _extract_version(raw_file_version)

    if not product_version and not file_version:
        return ""

    if not product_version:
        return file_version

    if not file_version:
        return product_version

    semantic_choice = _keep_greater_semantic_version(product_version, file_version)
    if semantic_choice:
        return semantic_choice

    return _choose_by_detail_and_numbers(product_version, file_version)


def _choose_by_detail_and_numbers(product_version: str, file_version: str) -> str:
    product_detail = _punctuation_count(product_version)
    file_detail = _punctuation_count(file_version)

    has_num_product = _contains_number(product_version)
    has_num_file = _contains_number(file_version)

    if has_num_file and file_detail > 0 and (not has_num_product or file_detail > product_detail):
        return file_version

    if has_num_product:
        return product_version
    if has_num_file:
        return file_version

    return product_version or file_version


def _keep_greater_semantic_version(product_version: str, file_version: str) -> str:
    try:
        semantic_product_version = packaging.version.parse(product_version)
    except ValueError:
        return ""

    try:
        semantic_file_version = packaging.version.parse(file_version)
    except ValueError:
        return product_version

    if semantic_product_version == semantic_file_version:
        return ""

    if semantic_file_version > semantic_product_version:
        return file_version

    return product_version


def _punctuation_count(string: str) -> int:
    return len(VERSION_PUNCTUATION_REGEX.findall(string))


def _extract_version(version: str) -> str:
    version = version.strip()

    result = ""

    for index, character in enumerate(version.split()):
        if _contains_number(result) and not _contains_number(character):
            return result

        if index == 0:
            result = character
        else:
            result += " " + character

    return result


def _contains_number(string: str) -> bool:
    return any(character.isdigit() for character in string)
