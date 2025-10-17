from zipfile import ZipInfo

from labels.model.ecosystem_data.java import JavaManifest
from labels.utils.licenses.parser import LICENSES_FILE_NAMES, parse_license
from labels.utils.zip import contents_from_zip, new_zip_glob_match


class LicenseExtractor:
    def __init__(self, *, file_manifest: list[ZipInfo], archive_path: str) -> None:
        self.file_manifest = file_manifest
        self.archive_path = archive_path

    def extract_all(self, manifest: JavaManifest) -> list[str]:
        licenses = self._extract_from_manifest(manifest)

        if not licenses:
            licenses = self._extract_from_files()

        return licenses

    def _extract_from_manifest(self, manifest: JavaManifest) -> list[str]:
        return [
            value
            for field in ("Bundle-License", "Plugin-License-Name")
            if (value := self._field_value_from_manifest(manifest, field))
        ]

    def _field_value_from_manifest(self, manifest: JavaManifest, field: str) -> str:
        if (value := manifest.main.get(field, None)) and value:
            return value

        for section in manifest.sections or []:
            if (value := section.get(field, None)) and value:
                return value
        return ""

    def _extract_from_files(self) -> list[str]:
        licenses = []
        for filename in LICENSES_FILE_NAMES:
            matches = self._find_license_files(filename)
            licenses.extend(self._parse_license_files(matches))

        return licenses

    def _find_license_files(self, filename: str) -> list[str]:
        matches = new_zip_glob_match(
            self.file_manifest, (f"/META-INF/{filename}",), case_sensitive=True
        )

        if not matches:
            matches = new_zip_glob_match(self.file_manifest, (f"/{filename}",), case_sensitive=True)

        return matches

    def _parse_license_files(self, matches: list[str]) -> list[str]:
        if not matches:
            return []

        licenses = []
        contents = contents_from_zip(self.archive_path, *matches)

        for match in matches:
            license_contents = contents.get(match, "")
            if parsed := parse_license(license_contents):
                licenses.extend(parsed)

        return licenses
