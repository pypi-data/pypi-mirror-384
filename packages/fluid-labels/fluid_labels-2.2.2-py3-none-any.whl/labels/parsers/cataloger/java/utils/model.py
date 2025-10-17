from typing import NamedTuple

from bs4 import Tag


class PomContext(NamedTuple):
    project: Tag
    dependencies: Tag
    parent_info: dict[str, str] | None
    parent_version_properties: dict[str, str] | None
    manage_deps: dict[str, str] | None
