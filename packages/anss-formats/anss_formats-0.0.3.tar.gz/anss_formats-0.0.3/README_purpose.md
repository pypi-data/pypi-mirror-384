# ANSS Data Formats
The US Geological Survey (USGS) Advanced National Seismic System (ANSS) defines a number of data exchange formats to communicate seismic event detection information between processing systems. These formats are defined using objects as defined in the [JSON standard](http://www.json.org).

The purpose of this project is to:

1. Define formats to hold data representing the estimates of various types of
seismic event detections.
2. Store the format definitions in a source controlled manner.
3. Host libraries used to generate, parse, and validate the formats

## Defined formats:

* [Pick](format-docs/Pick.md) Format - A format for unassociated picks from a waveform arrival time picking algorithm.

## Supporting format objects:

* [Amplitude](format-docs/Amplitude.md) Object - An object that contains information about an amplitude as part of a pick.
* [Beam](format-docs/Beam.md) Object  - An object that contains information about a waveform beam as part of a pick.
* [Associated](format-docs/Associated.md) Object - An object that contains associated information if a pick is included in a detection.
* [Filter](format-docs/Filter.md) Object - An object that contains filter information as part of a pick.
* [Site](format-docs/Site.md) Object - An object that defines the station used to create a pick.
* [Source](format-docs/Source.md) Object - An object that defines the creator/source of a pick.
* [Quality](format-docs/Quality.md) Object - An object that defines the data quality of a pick.
* [MachineLearning](format-docs/MachineLearning.md) Object - An object that defines the machine learning information for a pick.
* [EventType](format-docs/EventType.md) Object - An object that defines the event type for MachineLearning info.
