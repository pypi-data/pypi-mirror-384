# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import logging
from datetime import datetime, timezone

from typing import Sequence, Optional

# -------------------
# Third party imports
# -------------------º

from sqlalchemy import select, func

from tessdbdao import ValidState
from tessdbdao.asyncio import Observer

# --------------
# local imports
# -------------

from ..util import Session
from ..model import ObserverInfo, INFINITE_T, LogSpace

# ----------------
# Global variables
# ----------------

log = logging.getLogger(LogSpace.DBASE)


async def observers_list(session: Session) -> Sequence[Observer]:
    query = select(Observer).order_by(Observer.type, Observer.name, Observer.valid_since)
    return (await session.scalars(query)).all()


async def observer_lookup_current(session: Session, candidate: ObserverInfo) -> Observer:
    query = select(Observer).where(
        Observer.type == candidate.type,
        func.lower(Observer.name) == candidate.name.lower(),
        Observer.valid_state == ValidState.CURRENT,
    )
    return (await session.scalars(query)).one_or_none()


async def observer_lookup_history(session: Session, candidate: ObserverInfo) -> Sequence[Observer]:
    query = select(Observer).where(
        Observer.type == candidate.type,
        func.lower(Observer.name) == candidate.name.lower(),
    )
    return (await session.scalars(query)).all()


async def observer_create(
    session: Session,
    candidate: ObserverInfo,
    dry_run: bool = False,
) -> Optional[Observer]:
    observer = await observer_lookup_history(session, candidate)
    if observer:
        log.warning("Observer already exists")
        return
    website_url = str(candidate.website_url) if candidate.website_url else None
    observer = Observer(
        type=candidate.type,
        name=candidate.name,
        affiliation=candidate.affiliation,
        acronym=candidate.acronym,
        website_url=website_url,
        email=candidate.email,
        valid_since=datetime.now(timezone.utc).replace(microsecond=0),
        valid_until=INFINITE_T,
        valid_state=ValidState.CURRENT,
    )
    session.add(observer)
    if dry_run:
        log.warning("Dry run mode. Database not written")
        await session.rollback()
        return None
    return observer


async def observer_update(
    session: Session,
    candidate: ObserverInfo,
    fix_current: bool,
    dry_run: bool = False,
) -> Optional[Observer]:
    observer = await observer_lookup_current(session, candidate)
    if not observer:
        log.info(
            "Observer not found Type=%s, Name=%s",
            candidate.type,
            candidate.name,
        )
        return None
    website_url = str(candidate.website_url) if candidate.website_url else None
    if fix_current:
        observer.affiliation = candidate.affiliation or observer.affiliation
        observer.acronym = candidate.acronym or observer.acronym
        observer.website_url = website_url or observer.website_url
        observer.email = candidate.email or observer.email
        session.add(observer)
    else:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        observer.valid_until = now
        observer.valid_state = ValidState.EXPIRED
        session.add(observer)
        observer = Observer(
            type=candidate.type,
            name=candidate.name,
            affiliation=candidate.affiliation,
            acronym=candidate.acronym,
            website_url=website_url,
            email=candidate.email,
            valid_since=now,
            valid_until=INFINITE_T,
            valid_state=ValidState.CURRENT,
        )
        session.add(observer)
    if dry_run:
        log.warning("Dry run mode. Database not written")
        await session.rollback()
        return None
    return observer
