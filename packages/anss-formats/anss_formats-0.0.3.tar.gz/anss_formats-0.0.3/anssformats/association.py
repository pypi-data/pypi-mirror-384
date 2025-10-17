from typing import Optional

from pydantic import Field

from anssformats.formatbasemodel import FormatBaseModel


class Association(FormatBaseModel):
    """A conversion class used to create, parse, and validate association data as part
    of detection data.

    Attributes
    ----------

    phase: optional string containing the associated phase name

    distance: optional float containing the associated distance in degrees between the
        detection's and the data's locations if associated

    azimuth: optional float containing the associated azimuth in degrees between the
        detection's and the data's locations if associated

    residual: optional float containing the associated residual in seconds of the data
        if associated

    sigma: optional float containing the number of standard deviations of the data from
        the calculated value if associated
    """

    phase: Optional[str] = Field(None, pattern=r"^[A-Za-z]+$")

    distance: Optional[float] = Field(None, ge=0.0)
    azimuth: Optional[float] = Field(None, ge=0.0)
    residual: Optional[float] = None
    sigma: Optional[float] = None
