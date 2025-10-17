from anssformats.formatbasemodel import FormatBaseModel


class Source(FormatBaseModel):
    """A conversion class used to create, parse, and validate source data as part of
    detection data.

    Attributes
    ----------

    agencyID: string containing the originating agency FDSN ID

    author: string containing the source author
    """

    agencyID: str
    author: str
