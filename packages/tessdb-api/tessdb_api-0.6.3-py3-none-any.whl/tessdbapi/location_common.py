# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import math
import logging

from typing import Tuple, Dict, Optional, Any

# -------------------
# Third party imports
# -------------------

from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# --------------
# local imports
# -------------

from .model import EARTH_RADIUS, LogSpace

# ----------------
# Global variables
# ----------------

log = logging.getLogger(LogSpace.DBASE)
geolocator = Nominatim(user_agent="STARS4ALL project")
tf = TimezoneFinder()


def geolocate(longitude: float, latitude: float) -> Dict[str, Any]:
    row = dict()
    row["longitude"] = longitude
    row["latitude"] = latitude
    log.info(f"Geolocating Latitude {row['latitude']}, Longitude {row['longitude']}")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)  # noqa: F841
    location = geolocator.reverse(f"{row['latitude']}, {row['longitude']}", language="en")
    address = location.raw["address"]
    for location_type in ("village", "town", "city", "municipality"):
        try:
            row["town"] = address[location_type]
        except KeyError:
            row["town"] = None
            continue
        else:
            break
    for sub_region in ("province", "state", "state_district"):
        try:
            row["sub_region"] = address[sub_region]
        except KeyError:
            row["sub_region"] = None
            continue
        else:
            break
    for region in ("state", "state_district"):
        try:
            row["region"] = address[region]
        except KeyError:
            row["region"] = None
            continue
        else:
            break
    row["zipcode"] = address.get("postcode", None)
    row["country"] = address.get("country", None)
    row["timezone"] = tf.timezone_at(lng=row["longitude"], lat=row["latitude"])
    log.debug(row)
    return row

def geolocate_raw(longitude: float, latitude: float) -> Dict[str, Any]:
    row = dict()
    row["longitude"] = longitude
    row["latitude"] = latitude
    log.info(f"Geolocating Latitude {row['latitude']}, Longitude {row['longitude']}")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2)  # noqa: F841
    location = geolocator.reverse(f"{row['latitude']}, {row['longitude']}", language="en")
    row.update(location.raw["address"])
    row["timezone"] = tf.timezone_at(lng=row["longitude"], lat=row["latitude"])
    return row

def distance(coords_A: Tuple[float, float], coords_B: Tuple[float, float]) -> Optional[float]:
    """
    Compute approximate geographical distance (arc) [meters] between two points on Earth
    Coods_A and Coords_B are tuples (longitude, latitude)
    Accurate for small distances only
    """
    longitude_A = coords_A[0]
    longitude_B = coords_B[0]
    latitude_A = coords_A[1]
    latitude_B = coords_B[1]
    try:
        delta_long = math.radians(longitude_A - longitude_B)
        delta_lat = math.radians(latitude_A - latitude_B)
        mean_lat = math.radians((latitude_A + latitude_B) / 2)
        result = round(
            EARTH_RADIUS * math.sqrt(delta_lat**2 + (math.cos(mean_lat) * delta_long) ** 2), 0
        )
    except TypeError:
        result = None
    return result
