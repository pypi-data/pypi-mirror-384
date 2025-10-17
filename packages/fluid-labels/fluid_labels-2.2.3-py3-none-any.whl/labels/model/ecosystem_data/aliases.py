from typing import TypeAlias

from labels.model.ecosystem_data.alpine import ApkDBEntry
from labels.model.ecosystem_data.arch import AlpmDBEntry
from labels.model.ecosystem_data.debian import DpkgDBEntry
from labels.model.ecosystem_data.java import JavaArchive
from labels.model.ecosystem_data.python import WheelEggEcosystemData
from labels.model.ecosystem_data.redhat import RpmDBEntry

AcceptedEcosystemData: TypeAlias = (
    AlpmDBEntry | ApkDBEntry | DpkgDBEntry | JavaArchive | RpmDBEntry | WheelEggEcosystemData
)
