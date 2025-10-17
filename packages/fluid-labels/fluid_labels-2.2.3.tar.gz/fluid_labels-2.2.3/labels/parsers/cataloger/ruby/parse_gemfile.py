import re
from collections.abc import Iterable

from gemfileparser import Dependency, GemfileParser

from labels.model.file import Location, LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.ruby.package_builder import new_gem_package
from labels.parsers.cataloger.utils import get_enriched_location

GEMFILE_DEP: re.Pattern[str] = re.compile(
    r'^\s*(?P<gem>gem [\'"].*?[\'"],?( [\'"][><~=]{0,2}\s?[\d\.]+[\'"],?){0,2})',
)
NOT_PROD_DEP: re.Pattern[str] = re.compile(
    r":group => \[?[:\w\-, ]*(:development|:test)",
)
NOT_PROD_GROUP: re.Pattern[str] = re.compile(r"(\s*)group :(test|development)")
GEM_LOCK_DEP: re.Pattern[str] = re.compile(
    r"^\s{4}(?P<gem>[^\s]*)\s\([^\d]*(?P<version>.*)\)$",
)


def parse_gemfile(
    _: Resolver | None,
    __: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    packages = []
    in_group_block = False
    end_line = ""

    for line_number, line in enumerate(
        reader.read_closer.read().splitlines(),
        1,
    ):
        if in_group_block:
            if line == end_line:
                in_group_block = False
            elif (
                (matched := GEMFILE_DEP.search(line))
                and matched
                and (dependency := _create_dependency(line_number, reader.location, matched, line))
            ):
                packages.append(dependency)
            continue

        if match_group := NOT_PROD_GROUP.search(line):
            in_group_block = True
            end_line = f"{match_group.group(1)}end"
            continue

        if (
            (matched := GEMFILE_DEP.search(line))
            and matched
            and (dependency := _create_dependency(line_number, reader.location, matched, line))
        ):
            packages.append(dependency)

    return packages, []


def _create_dependency(
    line_number: int,
    location: Location,
    matched: re.Match[str],
    line: str,
) -> Package | None:
    gem_info = GemfileParser.preprocess(matched.group("gem"))[3:]
    product, version = _parse_line(gem_info)

    is_dev = _is_dev_dependency(line)

    new_location = get_enriched_location(
        location, line=line_number, is_dev=is_dev, is_transitive=False
    )

    return new_gem_package(product, version, new_location)


def _parse_line(in_line: str) -> tuple[str, str]:
    line: list[str] = []
    line = in_line.split(",")

    column_list: list[str] = []
    for column in line:
        stripped_column = (
            column.replace("'", "")
            .replace('"', "")
            .replace("%q<", "")
            .replace("(", "")
            .replace(")", "")
            .replace("[", "")
            .replace("]", "")
            .strip()
        )
        column_list.append(stripped_column)

    deps = _match_dep_criteria(column_list)
    deps_dict = deps.to_dict()
    product: str = deps_dict["name"]
    version: str = _format_requirements(deps_dict["requirement"])
    return product, version


def _match_dep_criteria(
    column_list: Iterable[str],
) -> Dependency:
    dep = Dependency()
    for column in column_list:
        for criteria, criteria_regex in GemfileParser.gemfile_regexes.items():
            match = criteria_regex.match(column)
            if match:
                if criteria == "requirement":
                    dep.requirement.append(match.group(criteria))
                else:
                    setattr(dep, criteria, match.group(criteria))
                break
    return dep


def _format_requirements(requirements: list[str]) -> str:
    formatted: str = ""
    if len(requirements) == 0:
        return formatted
    requirements = [req.replace(" ", "") for req in requirements]
    first_req = requirements[0]
    if "~" in first_req:
        if len(requirements) == 1:
            dot_times = first_req.count(".")
            if dot_times <= 1:
                formatted = first_req.replace("~>", "^")
            else:
                formatted = first_req.replace("~>", "~")
        elif len(requirements) == 2:
            sec_req = requirements[1]
            if ">=" in sec_req:
                formatted = sec_req.replace(">=", "^")
            elif "!=" in sec_req:
                sec_ver = sec_req.replace("!=", "")
                first_ver = first_req.replace("!=", "")
                formatted = f">={first_ver} <{sec_ver}  || >{sec_ver}"
    else:
        formatted = " ".join(requirements)
    return formatted


def _is_dev_dependency(line: str) -> bool:
    return bool(NOT_PROD_DEP.search(line))
