import re
from contextlib import suppress

from bs4 import BeautifulSoup

from labels.model.file import LocationReadCloser
from labels.model.package import Package
from labels.model.relationship import Relationship
from labels.model.release import Environment
from labels.model.resolver import Resolver
from labels.parsers.cataloger.javascript.package_builder import new_simple_npm_package
from labels.parsers.cataloger.utils import get_enriched_location

SCRIPT_DEP = re.compile(
    r"(?P<name>[^\s\/]*)(?P<separator>[-@\/])"
    r"(?P<version>(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*))",
)

NPM_CDNS = (
    "https://cdn.jsdelivr.net/npm/",
    "https://unpkg.com/",
    "https://cdn.skypack.dev/",
    "https://cdn.esm.sh/",
    "https://code.jquery.com/",
    "https://cdnjs.cloudflare.com/",
)


def parse_ascx_scripts(
    _resolver: Resolver | None,
    _env: Environment | None,
    reader: LocationReadCloser,
) -> tuple[list[Package], list[Relationship]]:
    html = None
    with suppress(UnicodeError):
        try:
            html = BeautifulSoup(reader.read_closer, features="html.parser")
        except AssertionError:
            return [], []

    if not html:
        return [], []

    packages = []
    for script in html("script"):
        src_attribute = str(script.attrs.get("src"))
        if not (src_attribute and src_attribute.endswith(".js")):
            continue

        if not src_attribute.startswith(NPM_CDNS):
            continue

        matched = SCRIPT_DEP.search(src_attribute)

        if not matched:
            continue

        name = matched.group("name")
        version = matched.group("version")

        if not name or not version:
            continue

        new_location = get_enriched_location(reader.location, line=script.sourceline)

        package = new_simple_npm_package(new_location, name, version)
        if package:
            packages.append(package)

    return packages, []
