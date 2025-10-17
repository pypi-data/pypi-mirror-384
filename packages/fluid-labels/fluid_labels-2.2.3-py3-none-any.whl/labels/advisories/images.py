import sqlite3
from typing import Any

from labels.advisories.database import BaseDatabase
from labels.advisories.match_fixes import match_fixed_versions
from labels.advisories.match_versions import match_vulnerable_versions
from labels.advisories.utils import create_advisory_from_record
from labels.model.advisories import Advisory


class ImagesDatabase(BaseDatabase):
    def __init__(self) -> None:
        super().__init__(db_name="skims_sca_advisories_for_images.db")


DATABASE = ImagesDatabase()


def _normalize_platform_version_for_query(platform_version: str) -> str:
    return platform_version.split(".")[0]


def fetch_advisory_from_database(
    cursor: sqlite3.Cursor,
    package_manager: str,
    platform_version: str,
    package_name: str,
) -> list[Any]:
    normalized_platform_version = (
        _normalize_platform_version_for_query(platform_version)
        if package_manager == "rpm"
        else platform_version
    )

    cursor.execute(
        """
        SELECT
            adv_id,
            source,
            vulnerable_version,
            severity_level,
            severity,
            severity_v4,
            epss,
            details,
            percentile,
            cwe_ids,
            cve_finding,
            auto_approve,
            fixed_versions,
            kev_catalog,
            platform_version
        FROM advisories
        WHERE package_manager = ? AND platform_version = ? AND package_name = ?;
        """,
        (package_manager, normalized_platform_version, package_name),
    )
    return cursor.fetchall()


def get_package_advisories(
    package_manager: str,
    package_name: str,
    version: str,
    platform_version: str,
    upstream_package: str | None = None,
) -> list[Advisory]:
    connection = DATABASE.get_connection()
    cursor = connection.cursor()

    return [
        adv
        for record in fetch_advisory_from_database(
            cursor,
            package_manager,
            platform_version,
            package_name,
        )
        if (
            adv := create_advisory_from_record(
                record, package_manager, package_name, version, upstream_package
            )
        )
    ]


def get_vulnerabilities(
    platform: str,
    product: str,
    version: str,
    platform_version: str | None,
    upstream_info: tuple[str | None, str | None] | None = None,
) -> list[Advisory]:
    advisories_list = []
    if (
        product
        and version
        and platform_version
        and (
            advisories := get_package_advisories(
                platform,
                product.lower(),
                version,
                platform_version,
            )
        )
    ):
        advisories_list.extend(
            [
                match_fixed_versions(version.lower(), advisor, None)
                for advisor in advisories
                if match_vulnerable_versions(version.lower(), advisor.vulnerable_version)
            ]
        )
    upstream_package, upstream_version = upstream_info or (None, None)
    if (
        upstream_package
        and upstream_version
        and platform_version
        and (
            origin_advisories := get_package_advisories(
                platform,
                upstream_package.lower(),
                upstream_version,
                platform_version,
                upstream_package,
            )
        )
    ):
        advisories_list.extend(
            [
                match_fixed_versions(version.lower(), advisor, None)
                for advisor in origin_advisories
                if match_vulnerable_versions(version.lower(), advisor.vulnerable_version)
            ]
        )

    return advisories_list
