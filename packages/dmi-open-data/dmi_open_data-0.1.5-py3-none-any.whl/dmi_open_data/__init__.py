"""Simple Python interface to the The Danish Meteorological Institute's (DMI) Open Data API."""

__version__ = "0.1.5"

from dmi_open_data.client import DMIOpenDataClient
from dmi_open_data.enums import (
    ClimateDataParameter,
    OceanographicDataParameter,
    Parameter,
)
from dmi_open_data.utils import date2microseconds, microseconds2date

__all__ = [
    "ClimateDataParameter",
    "date2microseconds",
    "DMIOpenDataClient",
    "microseconds2date",
    "OceanographicDataParameter",
    "Parameter",
]
