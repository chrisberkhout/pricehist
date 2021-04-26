from collections import namedtuple

FormatInfo = namedtuple(
    "FormatInfo",
    ["time", "decimal", "thousands", "symbol", "datesep"],
    defaults=["00:00:00", ".", "", "rightspace", "-"],
)
