from __future__ import annotations

from typing import Literal, Union

from typing_extensions import TypedDict

from . import IntTimestampS


class Model(TypedDict):
    Name: str
    Code: str


class AircraftFamilyRow(TypedDict):
    description: str
    models: list[Model]


class AircraftFamily(TypedDict):
    version: int
    rows: list[AircraftFamilyRow]


##


class Airline(TypedDict):
    Name: str
    Code: str
    ICAO: str


class Airlines(TypedDict):
    version: int
    rows: list[Airline]


##


class Timezone(TypedDict):
    name: str
    offset: int | None
    offsetHours: str
    abbr: str
    abbrName: str | None
    isDst: bool


class Airport(TypedDict):
    id: int
    name: str
    iata: str
    icao: str
    city: str
    lat: float
    lon: float
    country: str
    alt: int | Literal["-1"]
    size: int
    timezone: Timezone
    countryId: int


class Airports(TypedDict):
    version: str
    rows: list[Airport]


##


class CountryName(TypedDict):
    default: str
    full: str


class CountryCode(TypedDict):
    alpha2: str
    alpha3: str


class Country(TypedDict):
    id: int
    name: CountryName
    code: CountryCode


class Metadata(TypedDict):
    timestamp: IntTimestampS
    count: int


class Countries(TypedDict):
    metadata: Metadata
    data: list[Country]


##

StaticData = Union[AircraftFamily, Airlines, Airports, Countries]
