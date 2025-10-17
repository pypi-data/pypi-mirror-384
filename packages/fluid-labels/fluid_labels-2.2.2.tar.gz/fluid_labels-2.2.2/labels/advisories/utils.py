import json
import logging

from cvss import CVSS4
from cvss.exceptions import CVSS4MalformedError
from pydantic import ValidationError

from labels.model.advisories import Advisory, AdvisoryRecord
from labels.utils.strings import format_exception

LOGGER = logging.getLogger(__name__)


def _resolve_severity_level(
    severity_v4: str | None, precalculated_severity_level: str | None
) -> str:
    return _get_severity_level_from_cvss_v4(severity_v4) or precalculated_severity_level or "Low"


def _get_severity_level_from_cvss_v4(severity_v4: str | None) -> str | None:
    if not severity_v4:
        return None

    try:
        return CVSS4(severity_v4).severity
    except CVSS4MalformedError:
        LOGGER.exception(
            "Could not determine severity level from provided CVSS4 vector: %s", severity_v4
        )
        return None


def generate_cpe(package_manager: str, package_name: str, vulnerable_version: str) -> str:
    part = "a"
    vendor = package_name.split(":")[0] if ":" in package_name else "*"
    product = package_name.lower()
    version = vulnerable_version
    language = package_manager
    update = edition = sw_edition = target_sw = target_hw = other = "*"

    return (
        f"cpe:2.3:{part}:{vendor}:{product}:{version}:{update}:{edition}:"
        f"{language}:{sw_edition}:{target_sw}:{target_hw}:{other}"
    )


def create_advisory_from_record(
    advisory_db_record: AdvisoryRecord,
    package_manager: str,
    package_name: str,
    version: str,
    upstream_package: str | None = None,
) -> Advisory | None:
    try:
        return Advisory(
            id=advisory_db_record[0],
            source=advisory_db_record[1],
            vulnerable_version=advisory_db_record[2],
            severity_level=_resolve_severity_level(
                severity_v4=advisory_db_record[5],
                precalculated_severity_level=advisory_db_record[3],
            ),
            severity=advisory_db_record[4],
            severity_v4=advisory_db_record[5],
            epss=float(advisory_db_record[6]) if advisory_db_record[6] else 0.0,
            details=advisory_db_record[7],
            percentile=float(advisory_db_record[8]) if advisory_db_record[8] else 0.0,
            cwe_ids=json.loads(advisory_db_record[9]) if advisory_db_record[9] else ["CWE-1395"],
            cve_finding=advisory_db_record[10],
            auto_approve=bool(advisory_db_record[11]),
            fixed_versions=json.loads(advisory_db_record[12]) if advisory_db_record[12] else None,
            cpes=[generate_cpe(package_manager, package_name, version)],
            package_manager=package_manager,
            upstream_package=upstream_package if upstream_package else None,
            kev_catalog=bool(advisory_db_record[13]),
            platform_version=(
                advisory_db_record[14]
                if len(advisory_db_record) > 14 and advisory_db_record[14]
                else None
            ),
        )
    except ValidationError as ex:
        LOGGER.exception(
            "Unable to build advisory from database record",
            extra={
                "exception": format_exception(str(ex)),
                "advisory_db_record": advisory_db_record,
            },
        )
        return None
