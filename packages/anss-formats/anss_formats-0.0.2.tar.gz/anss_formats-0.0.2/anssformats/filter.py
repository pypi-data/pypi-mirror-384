from typing import Optional

from anssformats.formatbasemodel import FormatBaseModel


class Filter(FormatBaseModel):
    """A conversion class used to create, parse, and validate filter data as part of
    detection data.

    Attributes
    ----------

    type: optional string containing the type of filter

    highPass: optional float containing the high pass frequency

    lowPass: optional float containing the low pass frequency

    units: optional string containing the filter frequency units
    """

    type: Optional[str] = None
    highPass: Optional[float] = None
    lowPass: Optional[float] = None
    units: Optional[str] = None
