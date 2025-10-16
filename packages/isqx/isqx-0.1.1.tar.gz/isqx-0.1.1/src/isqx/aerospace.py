"""
Units and quantities common in aerospace engineering.

See: [isqx._citations.ICAO][]
"""
# TODO: ISO 2533:1975 (standard atmosphere)
# TODO: ISO 1151

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated, Literal

from ._core import (
    DELTA,
    Dimensionless,
    OriginAt,
    QtyKind,
    Quantity,
    ratio,
    slots,
)
from ._iso80000 import (
    ALTITUDE,
    DISTANCE,
    DRAG,
    DYNAMIC_PRESSURE,
    HOUR,
    KG,
    LIFT,
    M_PERS,
    MASS,
    MASS_FLOW_RATE,
    MIN,
    PA,
    POWER,
    PRESSURE,
    RAD,
    TEMPERATURE,
    K,
    L,
    M,
    N,
    S,
)
from .usc import FT

#
# aircraft performance: state
#

# heading: [0, 360) degrees
HEADING = QtyKind(RAD, ("heading",))
HEADING_TRUE = HEADING["true"]
HEADING_MAG = HEADING["magnetic"]
HEADING_TRUE_WIND = HEADING_TRUE["wind"]
HEADING_MAG_WIND = HEADING_MAG["wind"]

PRESSURE_ALTITUDE = ALTITUDE["pressure"]
"""Pressure altitude, as measured by the altimeter."""
DENSITY_ALTITUDE = ALTITUDE["density"]
"""Density altitude, as measured by the altimeter."""
GEOPOTENTIAL_ALTITUDE = ALTITUDE["geopotential"]
"""Geopotential altitude, as measured from mean sea level."""
GEOMETRIC_ALTITUDE = ALTITUDE["geometric"]
"""Geometric altitude, as measured from mean sea level."""
# height: measured from *specific* datum
ELEVATION = QtyKind(M, ("elevation",))  # ICAO 1.5
HEIGHT_GEODETIC = QtyKind(M, ("height", "geodetic"))
"""Geodetic height. See https://en.wikipedia.org/wiki/Geodetic_coordinates."""
HEIGHT_AGL = QtyKind(M, ("height", "above_ground_level"))
"""Height above ground level. Not to be confused with altitude."""  # ICAO 1.7
L_OVER_D = ratio(LIFT(N), DRAG(N))

K_PERM = K * M**-1
"""Kelvin per meter, a unit of temperature gradient. For use in ISA."""

#
# aircraft design
#

_AC = "aircraft"
_ENGINE = "engine"
_MAX = "maximum"
# mass: ICAO 2.8
AIRCRAFT_MASS = MASS[_AC]
GROSS = AIRCRAFT_MASS["gross"]
CARGO_CAPACITY = AIRCRAFT_MASS["cargo_capacity"]
FUEL_CAPACITY = AIRCRAFT_MASS["fuel_capacity"]
TAKEOFF_MASS = AIRCRAFT_MASS["takeoff"]
LANDING_MASS = AIRCRAFT_MASS["landing"]
MTOW = TAKEOFF_MASS[_MAX]
ZFW = AIRCRAFT_MASS["zero_fuel_weight"]
MZFW = ZFW[_MAX]
PAYLOAD = AIRCRAFT_MASS["payload"]
MLW = LANDING_MASS[_MAX]

TANK_CAPACITY = QtyKind(L, (_AC, "tank_capacity"))  # ICAO 1.14

ENDURANCE = QtyKind(HOUR, (_AC, "endurance"))  # ICAO 1.6

#
# aircraft performance: state vector
#

# temperature 6.7
STATIC_TEMPERATURE = TEMPERATURE["static"]
TOTAL_TEMPERATURE = TEMPERATURE["total"]
"""Also known as stagnation temperature."""
CONST_TEMPERATURE_ISA: Annotated[Decimal, STATIC_TEMPERATURE(K)] = Decimal(
    "288.15"
)
TEMPERATURE_DEVIATION_ISA = STATIC_TEMPERATURE[
    DELTA, OriginAt(Quantity(CONST_TEMPERATURE_ISA, K))
]
"""Deviation from the [ISA temperature at sea level][isqx.aerospace.CONST_TEMPERATURE_ISA]."""

TOTAL_PRESSURE = PRESSURE["total"]
IMPACT_PRESSURE = DYNAMIC_PRESSURE["impact"]

# linear velocity
AIRSPEED = QtyKind(M_PERS, ("airspeed",))
IAS = AIRSPEED["indicated"]
"""Indicated airspeed, as measured directly from the airspeed indicator."""
CAS = AIRSPEED["calibrated"]
"""Calibrated airspeed, [IAS][isqx.aerospace.IAS] corrected for instrument and position errors."""
EAS = AIRSPEED["equivalent"]
"""Equivalent airspeed."""
TAS = AIRSPEED["true"]
"""True airspeed."""
GS = AIRSPEED["ground"]
"""Ground speed."""
WIND_SPEED = QtyKind(M_PERS, ("wind",))
"""Wind speed."""
SPEED_OF_SOUND = QtyKind(M_PERS, ("sound",))
"""Speed of sound."""

FT_PER_MIN = FT * MIN**-1
VS = QtyKind(M_PERS, ("vertical_speed",))  # ICAO 4.15
"""Vertical speed, rate of climb or descent.
Commonly expressed in [feet per minute][isqx.aerospace.FT_PER_MIN]."""

SPECIFIC_IMPULSE = QtyKind(S, ("specific_impulse",))
RANGE = DISTANCE["range"]

#
# propulsion
#
ENGINE_POWER = POWER[_ENGINE]
SHAFT_POWER = ENGINE_POWER["shaft"]
ENGINE_MASS_FLOW_RATE = MASS_FLOW_RATE[_ENGINE]
KG_PERS = KG * S**-1
TSFC = QtyKind(KG_PERS * N**-1, (_ENGINE,))  # ICAO 5.3
BPR = Dimensionless("bypass_ratio")
#
# aeroacoustics
#
# TODO: dBA, EPNdB etc.

#
# navigation
#


@dataclass(frozen=True, **slots)
class Aerodrome:
    """An airport, airstrip, airport, altiport, heliport, STOLport, or water
    aerodrome."""

    ident: str
    ident_kind: Literal["icao", "iata"] | str


PRESSURE_ALTIMETER = QtyKind(PA, ("altimeter",))
"""Altimeter setting."""
RUNWAY_LENGTH = QtyKind(M, ("runway", "length"))  # ICAO 1.12
RVR = QtyKind(M, ("runway", "visual_range"))  # ICAO 1.13
VISIBILITY = QtyKind(M, ("meteo", "visibility"))  # ICAO 1.15
