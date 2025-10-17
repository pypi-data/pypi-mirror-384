from typing import Optional

from pydantic import Field

from anssformats.formatbasemodel import FormatBaseModel


class Amplitude(FormatBaseModel):
    """A conversion class used to create, parse, and validate amplitude data as part of
    detection data.

    Attributes
    ----------

    amplitude: optional float containing the amplitude

    period: optional float containing the period

    snr: optional float containing the signal to noise ratio, capped at 1E9
    """

    amplitude: Optional[float] = None
    period: Optional[float] = Field(None, ge=0.0)
    snr: Optional[float] = Field(None, ge=0.0, le=1e9)
