from typing import Optional

from pydantic import Field

from anssformats.formatbasemodel import FormatBaseModel


class Beam(FormatBaseModel):
    """A conversion class used to create, parse, and validate beam detection data.

    Attributes
    ----------

    backAzimuth: float containing the back azimuth in degrees

    backAzimuthError: optional float containing the back azimuth error

    slowness: float containing the horizontal slowness

    slownessError: optional float containing the horizontal slowness error

    powerRatio: optional float containing the power ratio

    powerRatioError: optional float containing the power ratio error
    """

    backAzimuth: float = Field(ge=0.0)
    backAzimuthError: Optional[float] = Field(None, ge=0.0)

    slowness: float = Field(ge=0.0)
    slownessError: Optional[float] = Field(None, ge=0.0)

    powerRatio: Optional[float] = Field(None, ge=0.0)
    powerRatioError: Optional[float] = Field(None, ge=0.0)
