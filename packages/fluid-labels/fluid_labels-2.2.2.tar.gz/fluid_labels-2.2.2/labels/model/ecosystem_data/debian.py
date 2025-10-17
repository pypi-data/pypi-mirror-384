from labels.model.ecosystem_data.base import EcosystemDataModel


class DpkgDBEntry(EcosystemDataModel):
    package: str
    source: str | None = None
    version: str | None = None
    source_version: str | None = None
    architecture: str | None = None
    maintainer: str | None = None
    provides: list[str] | None = None
    dependencies: list[str] | None = None
    pre_dependencies: list[str] | None = None
