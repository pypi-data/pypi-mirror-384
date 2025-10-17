import logging
from zipfile import ZipInfo

from labels.model.ecosystem_data.java import JavaManifest
from labels.model.file import Location
from labels.utils.zip import contents_from_zip, new_zip_glob_match

LOGGER = logging.getLogger(__name__)


class ManifestParser:
    def __init__(
        self, *, file_manifest: list[ZipInfo], archive_path: str, location: Location
    ) -> None:
        self.file_manifest = file_manifest
        self.archive_path = archive_path
        self.location = location

    def parse(self) -> JavaManifest | None:
        manifest_matches = self._find_manifest_files()
        if not self._validate_matches(manifest_matches):
            return None

        contents = self._read_manifest(manifest_matches[0])
        if not contents:
            return None

        manifest = self._parse_java_manifest(contents)

        if self._should_exclude(manifest):
            return None

        return manifest

    def _find_manifest_files(self) -> list[str]:
        return new_zip_glob_match(
            self.file_manifest, ("/META-INF/MANIFEST.MF",), case_sensitive=True
        )

    def _validate_matches(self, matches: list[str]) -> bool:
        if len(matches) != 1:
            if len(matches) > 1:
                LOGGER.error("Found multiple manifests in the jar: %s", matches)
            else:
                LOGGER.warning("No manifests found in the jar")
            return False
        return True

    def _read_manifest(self, manifest_path: str) -> str | None:
        contents = contents_from_zip(self.archive_path, manifest_path)
        return contents.get(manifest_path) if contents else None

    def _should_exclude(self, manifest: JavaManifest | None) -> bool:
        if not manifest:
            LOGGER.warning("failed to parse java manifest: %s", self.location)
            return True

        if manifest.main and "Weave-Classes" in manifest.main:
            LOGGER.warning("excluding archive due to Weave-Classes: %s", self.location)
            return True

        return False

    def _parse_java_manifest(self, content: str) -> JavaManifest | None:
        sections = self._process_section(content)

        return self._build_manifest(sections)

    def _process_section(self, content: str) -> list[dict[str, str]]:
        sections: list[dict[str, str]] = []
        current_section = -1
        last_key = ""

        for line in content.splitlines():
            if not line.strip():
                last_key = ""
                continue

            last_key = self._parse_line(line, last_key, current_section, sections)
            current_section = len(sections) - 1

        return sections

    def _parse_line(
        self, line: str, last_key: str, current_section: int, sections: list[dict[str, str]]
    ) -> str:
        line = line.strip()

        idx = line.find(":")
        if idx == -1:
            return last_key

        key = line[:idx].strip()
        value = line[idx + 1 :].strip()

        if not key:
            return last_key

        if last_key == "" or current_section == -1:
            sections.append({})
            current_section += 1

        sections[current_section][key] = value

        return key

    def _build_manifest(self, sections: list[dict[str, str]]) -> JavaManifest | None:
        if sections:
            main_section = sections[0]
            other_sections = sections[1:] if len(sections) > 1 else None
            return JavaManifest(main=main_section, sections=other_sections)

        return None
