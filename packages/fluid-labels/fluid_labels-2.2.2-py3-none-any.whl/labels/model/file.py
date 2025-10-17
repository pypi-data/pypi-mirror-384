from enum import StrEnum
from io import TextIOWrapper
from typing import TextIO

from pydantic import BaseModel, ConfigDict


class DependencyType(StrEnum):
    DIRECT = "DIRECT"
    TRANSITIVE = "TRANSITIVE"
    UNDETERMINABLE = "UNDETERMINABLE"


class Scope(StrEnum):
    BUILD = "BUILD"
    RUN = "RUN"
    UNDETERMINABLE = "UNDETERMINABLE"


class Coordinates(BaseModel):
    real_path: str
    file_system_id: str | None = None
    line: int | None = None


class Location(BaseModel):
    scope: Scope = Scope.UNDETERMINABLE
    coordinates: Coordinates | None = None
    access_path: str | None = None
    dependency_type: DependencyType = DependencyType.UNDETERMINABLE
    reachable_cves: list[str] = []

    def path(self) -> str:
        path = self.access_path or (self.coordinates.real_path if self.coordinates else None)
        if not path:
            error_msg = "Both access_path and coordinates.real_path are empty"
            raise ValueError(error_msg)
        return path


class LocationReadCloser(BaseModel):
    location: Location
    read_closer: TextIO | TextIOWrapper
    model_config = ConfigDict(arbitrary_types_allowed=True)
