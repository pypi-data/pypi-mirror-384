import re
from typing import NamedTuple

from labels.model.ecosystem_data.java import JavaArchive, JavaPomProject
from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.java.utils.package_builder import JavaPackageSpec, new_java_package
from labels.parsers.cataloger.utils import get_enriched_location

QUOTE = r'["\']'
NL = r"(\n?\s*)?"
TEXT = r'[^"\']+'
LINE_COMMENT_RE = re.compile(rf"^.*{NL}//.*$")

CONFIG_TO_DEV_STATUS = {
    "testRuntimeOnly": True,
    "testCompileOnly": True,
    "testImplementation": True,
    "compileOnly": True,
    "testCompile": True,
    "compile": False,
    "runtime": False,
    "implementation": False,
    "api": False,
    "runtimeOnly": False,
}


class GradleDependency(NamedTuple):
    group: str
    name: str
    version: str
    config: str
    line: int | None = None


def parse_gradle(
    _resolver: Resolver | None,
    _environment: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages: list[Package] = []
    relationships: list[Relationship] = []

    file_content = reader.read_closer.read()
    if not file_content:
        return packages, relationships

    gradle_dependencies = _parse_dependencies(file_content)
    packages = _collect_packages(gradle_dependencies, reader.location)

    return packages, relationships


def _collect_packages(
    gradle_dependencies: list[GradleDependency], reader_location: Location
) -> list[Package]:
    packages: list[Package] = []

    for dependency in gradle_dependencies:
        name = dependency.name
        version = dependency.version

        is_dev = CONFIG_TO_DEV_STATUS.get(dependency.config, None)

        new_location = get_enriched_location(reader_location, line=dependency.line, is_dev=is_dev)

        ecosystem_data = JavaArchive(
            pom_project=JavaPomProject(
                group_id=dependency.group,
                name=name,
                artifact_id=name,
                version=version,
            ),
        )

        package_spec = JavaPackageSpec(
            simple_name=name.rsplit(":", 1)[-1],
            composed_name=name,
            version=version,
            location=new_location,
            ecosystem_data=ecosystem_data,
        )

        package = new_java_package(package_spec)
        if package:
            packages.append(package)

    return packages


def _parse_dependencies(file_content: str) -> list[GradleDependency]:
    configs = _extract_gradle_configs(file_content)
    maven_regexes = _build_regex_with_configs(configs)

    dependencies = _get_block_deps(file_content, maven_regexes)

    for line_no, raw_line in enumerate(file_content.splitlines(), start=1):
        dependency = _parse_line_dependency_line(raw_line, line_no, maven_regexes)
        if dependency:
            dependencies.append(dependency)

    return dependencies


def _extract_gradle_configs(content: str) -> set[str]:
    config_pattern = re.compile(r"configurations\s*\{([^}]+)\}", re.DOTALL)
    custom_config_pattern = re.compile(r"\s*(\w+)\s*")
    configs = {
        "runtimeOnly",
        "api",
        "compile",
        "compileOnly",
        "implementation",
        "testRuntimeOnly",
        "testCompileOnly",
        "testImplementation",
        "runtime",
    }

    config_blocks = config_pattern.findall(content)
    for block in config_blocks:
        custom_configs = custom_config_pattern.findall(block)
        configs.update(custom_configs)

    return configs


def _build_regex_with_configs(configs: set[str]) -> dict[str, re.Pattern[str]]:
    config_pattern = "|".join(configs)

    return {
        "RE_GRADLE_A": re.compile(
            rf"^{NL}(?P<config_name>{config_pattern}){NL}[(]?{NL}"
            rf"group{NL}:{NL}{QUOTE}(?P<group>{TEXT}){QUOTE}{NL},"
            rf"{NL}name{NL}:{NL}{QUOTE}(?P<name>{TEXT}){QUOTE}{NL}"
            rf"(?:,{NL}version{NL}:{NL}{QUOTE}(?P<version>{TEXT}){QUOTE}{NL})"
            rf"?.*$",
        ),
        "RE_GRADLE_B": re.compile(
            rf"^.*{NL}(?P<config_name>{config_pattern}){NL}[(]?{NL}{QUOTE}(?P<statement>{TEXT}){QUOTE}",
        ),
        "RE_GRADLE_C": re.compile(
            rf"{NL}(?P<config_name>{config_pattern}){NL}\("
            rf"{NL}{QUOTE}(?P<statement>{TEXT}){QUOTE}{NL}\)"
            rf"{NL}{{({NL})version{NL}{{({NL})strictly{NL}\({NL}"
            rf"{QUOTE}(?P<version>{TEXT}){QUOTE}{NL}\){NL}}}{NL}}}",
            re.DOTALL,
        ),
        "BLOCK": re.compile(
            rf"{NL}(?P<config_name>{config_pattern}){NL}\("
            rf"{NL}{QUOTE}(?P<statement>{TEXT}){QUOTE}{NL}\)"
            rf"{NL}\{{(.*?version{NL}\{{.*?\}}){NL}\}}",
            re.DOTALL,
        ),
        "VERSION": re.compile(
            rf"version{NL}{{({NL})strictly{NL}\("
            rf"{NL}{QUOTE}(?P<version>{TEXT}){QUOTE}{NL}\){NL}}}",
            re.DOTALL,
        ),
    }


def _parse_line_dependency_line(
    line: str, line_no: int, regexes: dict[str, re.Pattern]
) -> GradleDependency | None:
    line, _ = _avoid_cmt(line, is_block_cmt=False)

    for regex_key in ("RE_GRADLE_A", "RE_GRADLE_B"):
        if match := regexes[regex_key].match(line):
            if regex_key == "RE_GRADLE_A":
                group = match.group("group")
                product = f"{group}:{match.group('name')}"
                version = match.group("version") or ""
            else:
                statement = match.group("statement")
                product, version = (
                    statement.rsplit(":", maxsplit=1)
                    if statement.count(":") >= 2
                    else (statement, "")
                )
                group = product.split(":")[0]

            # Assuming a wildcard in Maven if the version is not found can # result in issues.
            # https://gitlab.com/fluidattacks/universe/-/issues/5635
            if not version or re.match(r"\${.*}", version):
                return None

            return GradleDependency(
                group=group,
                name=product,
                version=version,
                line=line_no,
                config=match.group("config_name"),
            )

    return None


def _avoid_cmt(line: str, *, is_block_cmt: bool) -> tuple[str, bool]:
    if LINE_COMMENT_RE.match(line):
        line = line.split("//", 1)[0]
    if is_block_cmt:
        if "*/" in line:
            is_block_cmt = False
            line = line.split("*/", 1).pop()
        else:
            return "", is_block_cmt
    if "/*" in line:
        line_cmt_open = line.split("/*", 1)[0]
        if "*/" in line:
            line = line_cmt_open + line.split("*/", 1).pop()
        else:
            line = line_cmt_open
            is_block_cmt = True
    return line, is_block_cmt


def _get_block_deps(content: str, regexes: dict[str, re.Pattern[str]]) -> list[GradleDependency]:
    dependencies = []

    for block in regexes["BLOCK"].finditer(content):
        product = block.group("statement")
        hit = regexes["VERSION"].search(block.group())
        if not hit:
            continue

        version = hit.group("version")
        if version == "":
            continue

        config = block.group("config_name")

        line_no = _get_line_number(content, block.start())

        dependencies.append(
            GradleDependency(
                group=product.split(":")[0],
                name=product,
                version=version,
                line=line_no,
                config=config,
            ),
        )

    return dependencies


def _get_line_number(content: str, match_start: int) -> int:
    return content[:match_start].count("\n") + 2
