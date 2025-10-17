from datetime import datetime

from pydantic import BaseModel

from labels.model.constraints import NonEmptyStr


class Digest(BaseModel):
    algorithm: NonEmptyStr | None = None
    value: NonEmptyStr | None = None


class Artifact(BaseModel):
    url: NonEmptyStr
    integrity: Digest | None = None


class HealthMetadata(BaseModel):
    latest_version: NonEmptyStr | None = None
    latest_version_created_at: NonEmptyStr | datetime | None = None
    artifact: Artifact | None = None
    authors: NonEmptyStr | None = None
