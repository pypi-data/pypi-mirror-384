from typing import Optional, List, Literal

from pydantic import Field, field_validator, ValidationInfo
from anssformats.formatbasemodel import FormatBaseModel


class ChannelGeometry(FormatBaseModel):
    """A class holding the geojson geometry for the channel

    type: string containing the type of this geometry

    coordinates: List of floats containing the longitude in degrees, latitude in degrees, and elevation in meters, in that order
    """

    type: str = "Point"
    coordinates: List[float]

    # check that coordinates are valid
    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(
        cls, value: List[float], info: ValidationInfo
    ) -> List[float]:
        if value is None:
            raise ValueError("Missing coordinates")

        if len(value) != 3:
            raise ValueError("Incomplete coordinates")

        # longitude
        if value[0] < -180.0 or value[0] > 180.0:
            raise ValueError("Longitude coordinate out of valid range")

        # latitude
        if value[1] < -90.0 or value[1] > 90.0:
            raise ValueError("Latitude coordinate out of valid range")

        # don't bother validating elevation
        # value[2]

        return value


class ChannelProperties(FormatBaseModel):
    """A class holding the channe specific custom properties for a geojson point feature

    Station: string containing the station code

    Channel: optional string containing the channel code

    Network: string containing the network code

    Location: optional string containing the location code
    """

    station: str
    channel: Optional[str] = None
    network: str
    location: Optional[str] = None


class Channel(FormatBaseModel):
    """A conversion class used to create, parse, and validate geojson Channel data as part of
    detection data.

    type: string containing the type of this geojson

    geometry: ChannelGeometry object containing the geojson geometry for this feature

    properties: ChannelProperties object containing the channel properties
    """

    type: str = "Feature"

    geometry: ChannelGeometry
    properties: ChannelProperties
