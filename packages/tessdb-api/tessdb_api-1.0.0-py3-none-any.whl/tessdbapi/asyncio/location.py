# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import asyncio
import logging

from typing import Optional, Sequence, List

# -------------------
# Third party imports
# -------------------


from sqlalchemy import select

from tessdbdao.asyncio import Location

# --------------
# local imports
# -------------

from ..util import Session
from ..model import LocationInfo, LogSpace, GEO_COORD_EPSILON as EPSILON
from ..location_common import geolocate, distance

# ----------------
# Global variables
# ----------------


log = logging.getLogger(LogSpace.DBASE)

# -------------
# API functions
# -------------


def location_distances_from(candidate: LocationInfo, locations: Sequence[Location]) -> List[float]:
    return [
        distance((candidate.longitude, candidate.latitude), (location.longitude, location.latitude))
        for location in locations
    ]


async def location_list(session: Session) -> Sequence[Location]:
    query = select(Location).where(Location.longitude != None, Location.longitude != None)  # noqa: E711
    return (await session.scalars(query)).all()


async def location_nearby(
    session: Session, candidate: LocationInfo, limit: float
) -> Sequence[Location]:
    locations = await location_list(session)
    distances = location_distances_from(candidate, locations)
    nearby = [0 < d <= limit for d in distances]
    zipped_loc = list(filter(lambda x: x[1], zip(locations, nearby)))
    if zipped_loc:
        locations, _ = zip(*zipped_loc)
    else:
        locations = list()
    return locations


async def location_lookup(session: Session, candidate: LocationInfo) -> Optional[Location]:
    query = select(Location).where(
        Location.longitude.between(candidate.longitude - EPSILON, candidate.longitude + EPSILON),
        Location.latitude.between(candidate.latitude - EPSILON, candidate.latitude + EPSILON),
    )
    return (await session.scalars(query)).one_or_none()


async def location_create(
    session: Session,
    candidate: LocationInfo,
    dry_run: bool = False,
) -> Optional[Location]:
    location = await location_lookup(session, candidate)
    if location:
        log.warning("Location already exists")
        return None
    geolocated = await asyncio.to_thread(geolocate, candidate.longitude, candidate.latitude)
    location = Location(
        longitude=candidate.longitude,
        latitude=candidate.latitude,
        elevation=candidate.height,
        place=candidate.place,
        town=candidate.town or geolocated["town"],
        sub_region=candidate.sub_region or geolocated["sub_region"],
        region=candidate.region or geolocated["region"],
        country=candidate.country or geolocated["country"],
        timezone=candidate.timezone or geolocated["timezone"],
    )
    session.add(location)
    if dry_run:
        log.warning("Dry run mode. Database not written")
        session.rollback()
        return None
    return location


async def location_update(
    session: Session,
    candidate: LocationInfo,
    dry_run: bool = False,
) -> Optional[Location]:
    location = await location_lookup(session, candidate)
    if not location:
        log.info(
            "Location not found using coodinates Long=%s, Lat=%s",
            candidate.longitude,
            candidate.latitude,
        )
        return
    location.elevation = candidate.height or location.elevation
    location.place = candidate.place or location.place
    location.town = candidate.town or location.town
    location.sub_region = candidate.sub_region or location.sub_region
    location.region = candidate.region or location.region
    location.country = candidate.country or location.country
    location.timezone = candidate.timezone or location.timezone
    session.add(location)
    if dry_run:
        log.warning("Dry run mode. Database not written")
        await session.rollback()
        return None
    return location
