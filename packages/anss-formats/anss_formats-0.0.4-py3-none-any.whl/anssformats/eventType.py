from typing import Literal, Optional

from anssformats.formatbasemodel import FormatBaseModel


class EventType(FormatBaseModel):
    """A conversion class used to create, parse, and validate source data as part of
    detection data. Detection formats supports a subset of the QuakeML 1.2 event types
    that are automatically classifiable.

    Attributes
    ----------

    type: optional string containing the type of detection that was found; allowed type
        strings are: "Earthquake", "MineCollapse", "NuclearExplosion", "QuarryBlast",
        "InducedOrTriggered", "RockBurst", "FluidInjection", "IceQuake", and
        "VolcanicEruption"

    certainty: optional string containing the certainty of the event type; allowed
        strings are "Suspected" and "Confirmed"
    """

    type: Optional[
        Literal[
            "Earthquake",
            "MineCollapse",
            "NuclearExplosion",
            "QuarryBlast",
            "InducedOrTriggered",
            "RockBurst",
            "FluidInjection",
            "IceQuake",
            "VolcanicEruption",
        ]
    ] = None

    certainty: Optional[Literal["Suspected", "Confirmed"]] = None
