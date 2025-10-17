from typing import List, Literal, Optional

from pydantic import Field

from anssformats.amplitude import Amplitude
from anssformats.association import Association
from anssformats.beam import Beam
from anssformats.machineLearning import MachineLearning
from anssformats.filter import Filter
from anssformats.formatbasemodel import CustomDT, FormatBaseModel
from anssformats.channel import Channel, ChannelProperties
from anssformats.source import Source
from anssformats.quality import Quality


class Pick(FormatBaseModel):
    """A conversion class used to create, parse, and validate pick detection data.

    type: string identifying this message as a pick

    id: string containing a unique identifier for this pick

    channel: Channel object containing the station where the pick was made

    source: Source object containing the source of the pick

    time: datetime containing the arrival time of the phase that was picked

    phase: optional string containing the seismic phase that was picked

    polarity: optional string containing the phase polarity; allowed strings are "up"
        and "down"

    onset: optional string containing the phase onset; allowed strings are "impulsive",
        "emergent", and "questionable"

    pickerType: optional string containing the type of picker; allowed strings are "manual",
        "raypicker", "filterpicker", "earthworm", and "other"

    filterInfo: optional list of Filter objects containing the filter frequencies when the
        pick was made

    amplitude: optional Amplitude object containing the amplitude associated with the
        pick

    beamInfo: optional Beam object containing the waveform beam information associated with
        the pick

    associationInfo: optional Association object containing the association information
        if this pick is used as data in a Detection

    machineLearningInfo: optional machineLearning object containing the machineLearning
        information of this pick

    qualityInfo: optional quality object containing the quality
        information of this pick
    """

    type: Literal["Pick"]
    id: str

    channel: Channel
    source: Source
    time: CustomDT

    phase: Optional[str] = Field(None, pattern=r"^[A-Za-z]+$")
    polarity: Optional[Literal["up", "down"]] = None
    onset: Optional[Literal["impulsive", "emergent", "questionable"]] = None
    pickerType: Optional[
        Literal["manual", "raypicker", "filterpicker", "earthworm", "other"]
    ] = None

    filterInfo: Optional[List[Filter]] = None
    amplitudeInfo: Optional[Amplitude] = None
    beamInfo: Optional[Beam] = None

    associationInfo: Optional[Association] = None
    machineLearningInfo: Optional[MachineLearning] = None
    qualityInfo: Optional[List[Quality]] = None
