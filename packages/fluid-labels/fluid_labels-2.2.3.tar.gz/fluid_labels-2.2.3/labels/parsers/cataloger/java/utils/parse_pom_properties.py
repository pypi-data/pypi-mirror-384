import logging
import re
from pathlib import Path

from labels.model.ecosystem_data.java import JavaPomProperties
from labels.utils.zip import contents_from_zip

LOGGER = logging.getLogger(__name__)


def parse_pom_properties(file_content: str) -> JavaPomProperties | None:
    prop_map = {}

    for raw_line in file_content.splitlines():
        line = raw_line.strip()
        # Skip empty lines and comments
        if line == "" or line.lstrip().startswith("#"):
            continue

        # Find the first occurrence of ':' or '='
        idx = next((i for i in range(len(line)) if line[i] in ":="), -1)
        if idx == -1:
            LOGGER.error("Unable to split pom.properties line into key-value pairs: %s", line)
            continue

        key = line[:idx].strip()
        value = line[idx + 1 :].strip()
        prop_map[key] = value

    # Convert the dictionary to a JavaPomProperties object
    converted_props = {}
    for raw_key, value in prop_map.items():
        key = re.sub(r"(?<!^)(?=[A-Z])", "_", raw_key).lower()
        if key in set(JavaPomProperties.__annotations__.keys()):
            converted_props[key] = value

    return JavaPomProperties(**converted_props)


def pom_properties_by_parent(
    archive_path: str,
    extract_paths: list[str],
) -> dict[str, JavaPomProperties]:
    properties_by_parent_path = {}
    contents_of_maven_properties = contents_from_zip(archive_path, *extract_paths)

    for file_path, file_contents in contents_of_maven_properties.items():
        if not file_contents:
            continue
        pom_properties = parse_pom_properties(file_contents)
        if not pom_properties:
            continue
        if not pom_properties.group_id or not pom_properties.version:
            continue
        properties_by_parent_path[str(Path(file_path).parent)] = pom_properties

    return properties_by_parent_path
