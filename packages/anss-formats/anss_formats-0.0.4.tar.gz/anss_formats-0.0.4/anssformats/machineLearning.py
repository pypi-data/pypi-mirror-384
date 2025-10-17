from typing import Optional

from pydantic import Field

from anssformats.eventType import EventType as EventTypeFormat
from anssformats.formatbasemodel import FormatBaseModel
from anssformats.source import Source as SourceFormat


class MachineLearning(FormatBaseModel):
    """A conversion class used to create, parse, and validate value added MachineLearning
    data from advanced algorithms such as machine learning as part of detection formats
    data.

    Attributes
    ----------

    phase: optional string containing MachineLearning phase name

    phaseProbability: optional float containing the probability of the MachineLearning
        phase name

    distance: optional float containing the MachineLearning distance in degrees

    distanceProbability: optional float containing the probability of the MachineLearning
        distance

    backAzimuth: optional float containing the MachineLearning back azimuth in degrees

    backAzimuthProbability: optional float containing the probability of the
        MachineLearning back azimuth

    magnitude: optional float containing the MachineLearning magnitude

    magnitudeType: optional string containing the MachineLearning magnitude type

    magnitudeProbability: optional float containing the probability of the
        MachineLearning magnitude

    depth: optional float containing the MachineLearning depth in kilometers

    depthProbability: optional float containing the probability of the MachineLearning
        depth

    eventType: optional EventType object containing the MachineLearning event type

    eventTypeProbability: optional float containing the probability of the
        MachineLearning event type

    repickShift: optional float containing the repick shift value in seconds

    repickSTD: optional float containing the repick shift standard deviation

    repickCredibleIntervalLower: optional float containing the repick shift lower credible interval

    repickCredibleIntervalUpper: optional float containing the repick shift upper credible interval

    source: optional Source object containing the source of the MachineLearning
        information
    """

    phase: Optional[str] = Field(None, pattern=r"^[A-Za-z]+$")
    phaseProbability: Optional[float] = None

    distance: Optional[float] = Field(None, ge=0.0)
    distanceProbability: Optional[float] = None

    backAzimuth: Optional[float] = Field(None, ge=0.0)
    backAzimuthProbability: Optional[float] = None

    magnitude: Optional[float] = Field(None, ge=-2.0, le=10.0)
    magnitudeType: Optional[str] = None
    magnitudeProbability: Optional[float] = None

    depth: Optional[float] = Field(None, ge=-100.0, le=1500.0)
    depthProbability: Optional[float] = None

    eventType: Optional[EventTypeFormat] = None
    eventTypeProbability: Optional[float] = None

    distanceRangeHalfWidth: Optional[float] = None
    distanceRangeSigma: Optional[float] = None

    repickShift: Optional[float] = None
    repickSTD: Optional[float] = None
    repickCredibleIntervalLower: Optional[float] = None
    repickCredibleIntervalUpper: Optional[float] = None

    source: Optional[SourceFormat] = None
