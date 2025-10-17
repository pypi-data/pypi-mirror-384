from labels.model.ecosystem_data.base import EcosystemDataModel


class WheelEggEcosystemData(EcosystemDataModel):
    dependencies: list[str] | None = None
