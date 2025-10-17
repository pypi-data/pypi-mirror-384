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

# Amplitude Object Specification

## Description

The Amplitude object is an object designed to encode the amplitude information
that may or may not be part of the [Pick](Pick.md) Format.  Amplitude uses the
[JSON standard](http://www.json.org).

## Usage

The Amplitude object is intended for use as part of the [Pick](Pick.md) Format
in seismic data messaging between seismic applications and organizations.

## Output

```json
    {
       "amplitude" : Number,
       "period"    : Number,
       "snr"       : Number
    }
```

## Glossary

**Optional Values:**

The following are values that **may or may not** be provided as part of an
amplitude.

* amplitude - A decimal number containing the amplitude.
* period - A decimal number containing the amplitude period.
* snr - A decimal number containing the signal to noise ratio, capped at 1E9.

# Association Object Specification

## Description

The Association object is an object designed to encode information provided when
a [Pick](Pick.md).  Association uses the [JSON standard](http://www.json.org).

## Usage

Association is intended for use as part of the [Pick](Pick.md) Format in seismic data messaging between seismic applications and organizations.

## Output

```json
    {
       "phase"    : String,
       "distance" : Number,
       "azimuth"  : Number,
       "residual" : Number,
       "sigma"    : Number
    }
```

## Glossary

**Optional Values:**

The following are values that **may or may not** be provided as part of
association.

* phase - A string that identifies the seismic phase for this data if Association.
* distance - A decimal number containing the distance in degrees between the detection's and data's locations if Association.
* azimuth - A decimal number containing the azimuth in degrees between the detection's and data's locations if Association.
* residual - A decimal number containing residual in seconds of the data if Association.
* sigma - A decimal number reflecting the number of standard deviations of the data from the calculated value if Association.

# Beam Object Specification

## Description

The Beam object is an object designed to encode waveform beam information
that may or may not be part of the [Pick](Pick.md) Format.  Beam uses the
[JSON standard](http://www.json.org).

## Usage

The Beam object is intended for use as part of the [Pick](Pick.md) Format
in seismic data messaging between seismic applications and organizations.

## Output

```json
    {
      "backAzimuth"      : Number,
      "backAzimuthError" : Number,
      "slowness"         : Number,
      "slownessError"    : Number,
      "powerRatio"       : Number,
      "powerRatioError"  : Number
    }
```

## Glossary

**Required Values:**

These are the values **required** to define a beam.

* backAzimuth - A decimal number containing the back azimuth.
* slowness - A decimal number containing the horizontal slowness.

**Optional Values:**

The following are supplementary values that **may or may not** be provided by
various algorithms.

* backAzimuthError - A decimal number containing the back azimuth error.
* slownessError - A decimal number containing the horizontal slowness error.
* powerRatio - A decimal number containing the power ratio.
* powerRatioError - A decimal number containing the power ratio error.

# Site Object Specification

## Description

The Site object is an object designed to define the seismic station used to
produce a [Pick](Pick.md) message.  Site uses the [JSON](https://www.json.org) and [GeoJSON](https://geojson.org/) standards.

## Usage

Site is intended for use as part of the [Pick](Pick.md) Format in seismic data
messaging between seismic applications and organizations.

## Output

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [125.6, 10.1]
  },
  "properties": {
    "Station"   : String,
    "Channel"   : String,
    "Network"   : String,
    "Location"  : String
  }
}
```

## Glossary

**Required Values:**

These are the properties **required** to define a Site.

* type - A string indicating the geojson feature type
* geometry - A geojson point containing the station coordinates in the form [Latitude, Longitude, Elevation (in meters)]
* station - A string the station code.
* network - A string containing network code.

**Optional Values:**

The following are supplementary properties that **may or may not** be provided as
part of a Site.

* channel - A string containing the channel code.
* location - A string containing the location code.

# EventType Object Specification

## Description

The EventType object is an object designed to define the originating seismic
organization that produced a [MachineLearning](MachineLearning.md) object.
Site uses the [JSON standard](http://www.json.org).

## Usage

EventType is intended for use as part of the [PicMachineLearningk](MachineLearning.md) Oject in seismic data
messaging between seismic applications and organizations.

## Output

```json
    {
      "type"  : String,
      "certainty"    : String
    }
```

## Glossary

**Required Values:**

These are the values **required** to define a EventType

* type - A string containing the event type, allowed type strings are: "Earthquake", "MineCollapse", "NuclearExplosion", "QuarryBlast", "InducedOrTriggered", "RockBurst", "FluidInjection", "IceQuake", and "VolcanicEruption"

**Optional Values:**

The following are values that **may or may not** be provided as part of EventType.

* certainty - A string containing the certainty of the event type; allowed strings are "Suspected" and "Confirmed"

# Filter Object Specification

## Description

The Filter object is an object designed to encode a single set of filter
frequencies that may or may not be part of the filter list in the [Pick](Pick.md)
Format. Filter uses the [JSON standard](http://www.json.org) .

## Usage

The Filter object is intended for use as part of the [Pick](Pick.md) Format
in seismic data messaging between seismic applications and organizations.

## Output

```json
   {
      "type"     : String,
      "highPass" : Number,
      "lowPass"  : Number,
      "units"    : String
   }
```

## Glossary

**Optional Values:**

The following are values that **may or may not** be provided as part of a filter.

* type - A string containing the type of filter
* highPass - A decimal number containing the high pass frequency in Hz.
* lowPass - A decimal number containing the low pass frequency in Hz.
* units - A string containing the filter frequency units.

Note: The Type of filter is assumed to be "BandPass", and the Units are assumed
to be "Hertz"

# MachineLearning Object Specification

## Description

The MachineLearning object is an object designed to encode value added
information available for a [Pick](Pick.md) from advanced algorithms such as
machine learning. MachineLearning uses the [JSON standard](http://www.json.org).

## Usage

MachineLearning is intended for use as part of the [Pick](Pick.md) Format in
seismic data messaging between seismic
applications and organizations.

## Output

```json
    {
        "phase"                : String,
        "phaseProbability"     : Number,
        "distance"             : Number,
        "distanceProbability"  : Number,
        "distanceRangeHalfWidth"   : Number,
        "distanceRangeSigma"       : Number,
        "backAzimuth"              : Number,
        "backAzimuthProbability"   : Number,
        "magnitude"            : Number,
        "magnitudeType"        : String,
        "magnitudeProbability" : Number,
        "depth"                : Number,
        "depthProbability"     : Number,
        "eventType" :
        {
            "type"      : String,
            "certainty" : String
        },
        "eventTypeProbability" : Number,
        "repickShift" : Number,
        "repickSTD" : Number,
        "repickCredibleIntervalLower" : Number,
        "repickCredibleIntervalUpper" : Number,
        "source" :
        {
            "agencyID" : String,
            "author"   : String
        }
    }
```

## Glossary

**Optional Values:**

The following are values that **may or may not** be provided as part of MachineLearning.

* phase - A string that identifies the seismic phase for this data
* phaseProbability - A decimal number containing the probability of the phase identification
* distance - A decimal number containing a distance estimation in degrees
* distanceProbability - A decimal number containing the probability of the distance estimation
* distanceRangeHalfWidth - A decimal number containing the half-width of a distance range centered at Distance  (e.g. Distance is 15 deg +/- 10 deg)
* distanceRangeSigma - A decimal number containing the standard deviation for a probability PDF curve for Distance (e.g. Distance is 15 deg +/- 3 * DistanceRangeSigma where DistanceProbability is modified by the PDF probability, lowering as it gets further from Distance ).  DistanceRangeSigma is mutually exclusive of DistanceRangeHalfWidth, and if both are provided DistanceRangeSigma should be used. 
* backAzimuth - A decimal number containing a backazimuth estimation in degrees
* backAzimuthProbability - A decimal number containing the probability of the backazimuth estimation
* magnitude - A decimal number containing the magnitude estimation
* magnitudeType - A string that identifies the magnitude type
* magnitudeProbability - A decimal number containing the probability of the magnitude estimation
* depth - A decimal number containing a depth estimation in kilometers
* depthProbability - A decimal number containing the probability of the depth estimation
* eventType - An object containing the event type, see [EventType](EventType.md).
* eventTypeProbability - A decimal number containing the probability of the event type estimation
* repickShift - A decimal number containing the repick shift in seconds (to regenerate the initial Pick.Time, subtract this value from the current Pick.Time)
* repickSTD - A decimal number containing the repick shift standard deviation
* repickCredibleIntervalLower - A decimal number containing the repick shift credible interval lower
* repickCredibleIntervalUpper - A decimal number containing the repick shift credible interval upper
* source - An object containing the source of the MachineLearning, see [Source](Source.md).

# Pick Format Specification

## Description

Pick is a format designed to encode the basic information of an unassociated
waveform arrival time pick.  Pick uses the
[JSON standard](http://www.json.org).

## Usage
Pick is intended for use in seismic data messaging between seismic
applications and organizations.

## Output

```json
    {
      "type"      : "Pick",
      "id"        : String,
      "channel"      :
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [125.6, 10.1, 1589.0]
        },
        "properties": {
          "station"   : String,
          "channel"   : String,
          "network"   : String,
          "location"  : String
        }
      },
      "time"      : ISO8601,
      "source"    :
      {
         "agencyID"  : String,
         "author"    : String
      },
      "phase"     : String,
      "polarity"  : ("up" | "down"),
      "onset"     : ("impulsive" | "emergent" | "questionable"),
      "pickerType"    : ("manual" | "raypicker" | "filterpicker" | "earthworm" | "other"),
      "filterInfo"    : [ {
        "type"     : String,
        "highPass" : Number,
        "lowPass"  : Number,
        "units"    : String
        }, ...],
      "amplitudeInfo" :
      {
         "value" : Number,
         "period"    : Number,
         "snr"       : Number
      },
      "beamInfo" :
      {
        "backAzimuth"      : Number,
        "backAzimuthError" : Number,
        "slowness"         : Number,
        "slownessError"    : Number,
        "powerRatio"       : Number,
        "powerRatioError"  : Number,
      },
      "associationInfo" :
      {
         "phase"    : String,
         "distance" : Number,
         "azimuth"  : Number,
         "residual" : Number,
         "sigma"    : Number
      },
      "qualityInfo" : [ {
        "standard": String,
        "value": Number
        }, ...],
      "machineLearningInfo" :
      {
        "phase"                : String,
        "phaseProbability"     : Number,
        "distance"             : Number,
        "distanceProbability"  : Number,
        "distanceRangeHalfWidth"   : Number,
        "distanceRangeSigma"       : Number,
        "backAzimuth"              : Number,
        "backAzimuthProbability"   : Number,
        "magnitude"            : Number,
        "magnitudeType"        : String,
        "magnitudeProbability" : Number,
        "depth"                : Number,
        "depthProbability"     : Number,
        "eventType" : {
          "type"      : String,
          "certainty" : String
        },
        "eventTypeProbability" : Number,
        "repickShift" : Number,
        "repickSTD" : Number,
        "repickCredibleIntervalLower" : Number,
        "repickCredibleIntervalUpper" : Number,
        "source" : {
            "agencyID" : String,
            "author"   : String
        }
      }
    }
```

## Glossary

**Required Values:**

These are the values **required** to define a pick.

* type - A string that identifies this message as a pick.
* id - A string containing an unique identifier for this pick.
* channel - A GeoJSON object containing the channel the pick was made at, see [Channel](Channel.md).
* source - An object containing the source of the pick, see [Source](Source.md).
* time - A string containing the UTC arrival time of the phase that was picked, in the ISO8601 format `YYYY-MM-DDTHH:MM:SS.SSSZ`.

**Optional Values:**

The following are supplementary values that **may or may not** be provided by
various picking algorithms.

* phase - A string that identifies the seismic phase that was picked.
* polarity - A string containing the phase polarity; "up" or "down".
* onset - A string containing the phase onset; "impulsive", "emergent", or "questionable" .
* pickerType - A string describing the type of picker; "manual", "raypicker", "filterpicker", "earthworm", or "other".
* filter - An array of objects containing the filter frequencies when the pick was made, see [Filter](Filter.md).
* amplitude - An object containing the amplitude associated with the pick, see [Amplitude](Amplitude.md).
* beam - An object containing the waveform beam information associated with the pick, see [Beam](Beam.md).
* associationInfo - An object containing the association information if this pick is used as data in a Detection, see [Associated](Associated.md).
* machineLearningInfo - An object containing the machine learning  information of this pick, see [MachineLearning](MachineLearning.md).
* qualityInfo - An array of objects containing the containing the quality metric information for this pick, see [Quality](Quality.md).

# Quality Object Specification

## Description

The Quality object is an object designed to hold data quality for a [Pick](Pick.md) message.
Site uses the [JSON standard](http://www.json.org).

## Usage

Quality is intended for use as part of the [Pick](Pick.md) Format in seismic data
messaging between seismic applications and organizations.

## Output

```json
    {
        "standard": String,
        "value": Number
    }
```

## Glossary

**Required Values:**

These are the values **required** to define a Quality

* standard - A string containing the name of the quality standard.
* value - A string containing numarical value of the quality standard.

# Source Object Specification

## Description

The Source object is an object designed to define the originating seismic
organization that produced a [Pick](Pick.md) message.
Site uses the [JSON standard](http://www.json.org).

## Usage

Source is intended for use as part of the [Pick](Pick.md) Format in seismic data
messaging between seismic applications and organizations.

## Output

```json
    {
      "agencyID"  : String,
      "author"    : String
    }
```

## Glossary

**Required Values:**

These are the values **required** to define a Source

* agencyID - A string containing the originating agency FDSN ID.
* author - A string containing the source author.
