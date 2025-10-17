from anssformats.formatbasemodel import FormatBaseModel


class Quality(FormatBaseModel):
    """A conversion class used to create, parse, and validate Quality data as part of
    detection data.

    Attributes
    ----------

    standard: string containing the name of the quality standard used

    value: float containing the Quality value
    """

    standard: str
    value: float
