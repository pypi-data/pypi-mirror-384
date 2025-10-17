import json
import sqlite3
from typing import Any

from labels.advisories.database import BaseDatabase
from labels.advisories.match_fixes import match_fixed_versions
from labels.advisories.match_versions import match_vulnerable_versions
from labels.advisories.utils import create_advisory_from_record
from labels.model.advisories import Advisory


class RootsDatabase(BaseDatabase):
    def __init__(self) -> None:
        super().__init__(db_name="skims_sca_advisories.db")


DATABASE = RootsDatabase()


def fetch_advisory_from_database(
    cursor: sqlite3.Cursor,
    package_manager: str,
    package_name: str,
) -> list[Any]:
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
            kev_catalog
        FROM advisories
        WHERE package_manager = ? AND package_name = ?;
        """,
        (package_manager, package_name),
    )
    return cursor.fetchall()


def fetch_safe_versions_from_database(
    cursor: sqlite3.Cursor,
    package_manager: str,
    package_name: str,
) -> list[str]:
    cursor.execute(
        """
        SELECT safe_versions
        FROM safe_versions
        WHERE package_manager = ? AND package_name = ?;
        """,
        (package_manager, package_name),
    )
    row = cursor.fetchone()
    if row and row[0]:
        return json.loads(row[0])
    return []


def get_package_advisories(
    package_manager: str,
    package_name: str,
    version: str,
) -> list[Advisory]:
    connection = DATABASE.get_connection()
    cursor = connection.cursor()

    return [
        adv
        for advisory_record in fetch_advisory_from_database(cursor, package_manager, package_name)
        if (
            adv := create_advisory_from_record(
                advisory_record, package_manager, package_name, version
            )
        )
    ]


def get_safe_versions(
    package_manager: str,
    package_name: str,
) -> list[str]:
    connection = DATABASE.get_connection()
    cursor = connection.cursor()
    return fetch_safe_versions_from_database(cursor, package_manager, package_name)


def get_vulnerabilities(
    platform: str, product: str, version: str, safe_versions: list[str] | None
) -> list[Advisory]:
    if (
        product
        and version
        and (advisories := get_package_advisories(platform, product.lower(), version))
    ):
        return [
            match_fixed_versions(version.lower(), advisor, safe_versions)
            for advisor in advisories
            if match_vulnerable_versions(version.lower(), advisor.vulnerable_version)
        ]
    return []
