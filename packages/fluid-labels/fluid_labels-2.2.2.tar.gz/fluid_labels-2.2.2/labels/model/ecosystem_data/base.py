from pydantic import BaseModel


class EcosystemDataModel(BaseModel):
    """Base class for ecosystem data models used in ecosystem_data.

    Purpose:
        This class exists solely to avoid Pydantic's Union/type alias casting issues
        with simple structural data. It is used only for ecosystem data.
        Ecosystem data models remain simple and immutable, similar to NamedTuple behavior.
    """

    model_config = {"frozen": True}
