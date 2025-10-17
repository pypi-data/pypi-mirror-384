from labels.model.ecosystem_data.base import EcosystemDataModel


class RpmDBEntry(EcosystemDataModel):
    name: str
    version: str
    epoch: int | None
    arch: str
    release: str
    source_rpm: str
