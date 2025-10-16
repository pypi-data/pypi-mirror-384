import pytest
import pytest_asyncio
import logging
from argparse import Namespace
from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import func, select

from lica.sqlalchemy import sqa_logging

from tessdbdao import ObserverType, ValidState, RegisterState
from tessdbdao.asyncio import Tess

from tessdbapi.model import PhotometerInfo

from . import engine, Session
from ... import DbSize, copy_file

from tessdbapi.asyncio.photometer.register import (
    observer_id_lookup,
    location_id_lookup,
    photometer_register,
    photometer_assign,
)

from tessdbapi.asyncio.observer import observer_create
from tessdbapi.asyncio.location import location_create

log = logging.getLogger(__name__.split(".")[-1])


# -------------------------------
# helper functions for test cases
# -------------------------------


async def photometer_lookup_current(session: Session, candidate: PhotometerInfo) -> Optional[Tess]:
    query = select(Tess).where(
        func.lower(Tess.mac_address) == candidate.mac_address.lower(),
        Tess.valid_state == ValidState.CURRENT,
    )
    return (await session.scalars(query)).one_or_none()


async def photometer_lookup_history(
    session: Session, candidate: PhotometerInfo
) -> Optional[Sequence[Tess]]:
    query = (
        select(Tess)
        .where(
            func.lower(Tess.mac_address) == candidate.mac_address.lower(),
        )
        .order_by(Tess.valid_since.asc())
    )
    return (await session.scalars(query)).all()


async def photometer_lookup_history_current(
    session: Session, candidate: PhotometerInfo
) -> Sequence[Tess]:
    query = (
        select(Tess)
        .where(
            func.lower(Tess.mac_address) == candidate.mac_address.lower(),
            Tess.valid_state == ValidState.CURRENT,
        )
        .order_by(Tess.valid_since.asc())
    )
    return (await session.scalars(query)).all()


# ------------------
# Convenient fixtures
# -------------------


@pytest_asyncio.fixture(params=[DbSize.MEDIUM])
async def database(request):
    args = Namespace(verbose=False)
    sqa_logging(args)
    copy_file(f"tess.{request.param}.db", "tess.db")
    yield Session()
    log.info("Teardown code disposes the engine")
    await engine.dispose()


@pytest.mark.asyncio
async def test_register_timestamps_types(database, stars993):
    """
    Old tessdb database had timestamps in format YYYY-mm-DD HH:MM:SS+00:00
    and now timestamps are written in YYYY-mm-DD HH:MM:SS.ffffff
    We have to check if SQLAlchemy or SQLite driver handles both formats
    transpàrently
    """
    place = "Facultad de Físicas UCM"
    observer_type = ObserverType.PERSON
    observer_name = "Prof. Jaime Zamorano"
    async with database.begin():
        await photometer_register(
            session=database,
            candidate=stars993,
            place=place,
            observer_type=observer_type,
            observer_name=observer_name,
        )
        photometer = await photometer_lookup_history(session=database, candidate=stars993)
        log.info("This photometer has %d entries", len(photometer))
        for i in range(len(photometer)):
            assert isinstance(photometer[i].valid_since, datetime)
            assert isinstance(photometer[i].valid_until, datetime)


@pytest.mark.asyncio
async def test_register_tessw_single(database, stars8000):
    place = "Facultad de Físicas UCM"
    observer_type = ObserverType.PERSON
    observer_name = "Prof. Jaime Zamorano"
    async with database.begin():
        await photometer_register(
            session=database,
            candidate=stars8000,
            place=place,
            observer_type=observer_type,
            observer_name=observer_name,
        )
        photometer = await photometer_lookup_current(session=database, candidate=stars8000)
        observer_id = await observer_id_lookup(database, observer_type, observer_name)
        location_id = await location_id_lookup(database, place)
        assert photometer.model == stars8000.model
        assert photometer.mac_address == stars8000.mac_address
        assert photometer.valid_state == ValidState.CURRENT
        assert photometer.registered == RegisterState.MANUAL
        assert photometer.authorised is True
        assert photometer.nchannels == 1
        assert photometer.zp1 == stars8000.zp1
        assert photometer.filter1 == stars8000.filter1
        assert photometer.offset1 == stars8000.offset1
        assert photometer.observer_id == observer_id
        assert photometer.location_id == location_id


@pytest.mark.asyncio
async def test_register_tess4c_single(database, stars8010):
    place = "Facultad de Físicas UCM"
    observer_type = ObserverType.PERSON
    observer_name = "Prof. Jaime Zamorano"
    async with database.begin():
        await photometer_register(
            session=database,
            candidate=stars8010,
            place=place,
            observer_type=observer_type,
            observer_name=observer_name,
        )
        photometer = await photometer_lookup_current(session=database, candidate=stars8010)
        observer_id = await observer_id_lookup(database, observer_type, observer_name)
        location_id = await location_id_lookup(database, place)
        assert photometer.model == stars8010.model
        assert photometer.mac_address == stars8010.mac_address
        assert photometer.valid_state == ValidState.CURRENT
        assert photometer.registered == RegisterState.MANUAL
        assert photometer.authorised is True
        assert photometer.nchannels == 4
        assert photometer.zp1 == stars8010.zp1
        assert photometer.filter1 == stars8010.filter1
        assert photometer.offset1 == stars8010.offset1
        assert photometer.zp2 == stars8010.zp2
        assert photometer.filter2 == stars8010.filter2
        assert photometer.offset2 == stars8010.offset2
        assert photometer.zp3 == stars8010.zp3
        assert photometer.filter3 == stars8010.filter3
        assert photometer.offset3 == stars8010.offset3
        assert photometer.zp4 == stars8010.zp4
        assert photometer.filter4 == stars8010.filter4
        assert photometer.offset4 == stars8010.offset4
        assert photometer.observer_id == observer_id
        assert photometer.location_id == location_id


@pytest.mark.asyncio
async def test_register_tessw_nometa(database, stars8000):
    async with database.begin():
        await photometer_register(
            session=database,
            candidate=stars8000,
        )
        photometer = await photometer_lookup_current(session=database, candidate=stars8000)
        observer_id = await observer_id_lookup(database, obs_type=None, obs_name=None)
        location_id = await location_id_lookup(database, place=None)
        assert photometer.model == stars8000.model
        assert photometer.mac_address == stars8000.mac_address
        assert photometer.valid_state == ValidState.CURRENT
        assert photometer.nchannels == 1
        assert photometer.observer_id == observer_id
        assert photometer.location_id == location_id


@pytest.mark.asyncio
async def test_register_tessw_duplicated(database, stars8001):
    place = "Facultad de Físicas UCM"
    observer_type = ObserverType.PERSON
    observer_name = "Prof. Jaime Zamorano"
    async with database.begin():
        for photinfo in [stars8001, stars8001]:
            await photometer_register(
                session=database,
                candidate=photinfo,
                place=place,
                observer_type=observer_type,
                observer_name=observer_name,
            )
        photometer = await photometer_lookup_current(session=database, candidate=stars8001)
        observer_id = await observer_id_lookup(database, observer_type, observer_name)
        location_id = await location_id_lookup(database, place)
        assert photometer.model == stars8001.model
        assert photometer.mac_address == stars8001.mac_address
        assert photometer.valid_state == ValidState.CURRENT
        assert photometer.nchannels == 1
        assert photometer.observer_id == observer_id
        assert photometer.location_id == location_id


@pytest.mark.asyncio
async def test_register_tess4c_duplicated(database, stars8010):
    place = "Facultad de Físicas UCM"
    observer_type = ObserverType.PERSON
    observer_name = "Prof. Jaime Zamorano"
    async with database.begin():
        for photinfo in [stars8010, stars8010]:
            await photometer_register(
                session=database,
                candidate=photinfo,
                place=place,
                observer_type=observer_type,
                observer_name=observer_name,
            )
        photometer = await photometer_lookup_current(session=database, candidate=stars8010)
        observer_id = await observer_id_lookup(database, observer_type, observer_name)
        location_id = await location_id_lookup(database, place)
        assert photometer.model == stars8010.model
        assert photometer.mac_address == stars8010.mac_address
        assert photometer.valid_state == ValidState.CURRENT
        assert photometer.nchannels == 4
        assert photometer.observer_id == observer_id
        assert photometer.location_id == location_id


@pytest.mark.asyncio
async def test_register_tessw_changezp(database, stars8000, stars8000zp):
    place = "Facultad de Físicas UCM"
    observer_type = ObserverType.PERSON
    observer_name = "Prof. Jaime Zamorano"
    async with database.begin():
        for photinfo in [stars8000, stars8000zp]:
            await photometer_register(
                session=database,
                candidate=photinfo,
                place=place,
                observer_type=observer_type,
                observer_name=observer_name,
            )
        photometer = await photometer_lookup_history(session=database, candidate=stars8000)
        observer_id = await observer_id_lookup(database, observer_type, observer_name)
        location_id = await location_id_lookup(database, place)
        assert len(photometer) == 2
        for i, photinfo in enumerate([stars8000, stars8000zp]):
            assert photometer[i].model == photinfo.model
            assert photometer[i].mac_address == photinfo.mac_address
            assert photometer[i].nchannels == 1
            assert photometer[i].filter1 == photinfo.filter1
            assert photometer[i].offset1 == photinfo.offset1
            assert photometer[i].observer_id == observer_id
            assert photometer[i].location_id == location_id
            assert photometer[i].zp1 == photinfo.zp1
        assert photometer[0].valid_state == ValidState.EXPIRED
        assert photometer[1].valid_state == ValidState.CURRENT
        assert photometer[0].valid_until == photometer[1].valid_since


@pytest.mark.asyncio
async def test_register_tess4c_changezp(database, stars8010, stars8010zp):
    place = "Facultad de Físicas UCM"
    observer_type = ObserverType.PERSON
    observer_name = "Prof. Jaime Zamorano"
    async with database.begin():
        for photinfo in [stars8010, stars8010zp]:
            await photometer_register(
                session=database,
                candidate=photinfo,
                place=place,
                observer_type=observer_type,
                observer_name=observer_name,
            )
        photometer = await photometer_lookup_history(session=database, candidate=stars8010)
        observer_id = await observer_id_lookup(database, observer_type, observer_name)
        location_id = await location_id_lookup(database, place)
        assert len(photometer) == 2
        for i, photinfo in enumerate([stars8010, stars8010zp]):
            assert photometer[i].model == photinfo.model
            assert photometer[i].mac_address == photinfo.mac_address
            assert photometer[i].nchannels == 4
            assert photometer[i].zp1 == photinfo.zp1
            assert photometer[i].filter1 == photinfo.filter1
            assert photometer[i].offset1 == photinfo.offset1
            assert photometer[i].observer_id == observer_id
            assert photometer[i].location_id == location_id
            assert photometer[i].zp2 == photinfo.zp2
            assert photometer[i].filter2 == photinfo.filter2
            assert photometer[i].offset2 == photinfo.offset2
            assert photometer[i].zp3 == photinfo.zp3
            assert photometer[i].filter3 == photinfo.filter3
            assert photometer[i].offset3 == photinfo.offset3
            assert photometer[i].zp4 == photinfo.zp4
            assert photometer[i].filter4 == photinfo.filter4
            assert photometer[i].offset4 == photinfo.offset4
        assert photometer[0].valid_state == ValidState.EXPIRED
        assert photometer[1].valid_state == ValidState.CURRENT
        assert photometer[0].valid_until == photometer[1].valid_since


@pytest.mark.asyncio
async def test_register_rename(database, stars8000, stars8001):
    place = "Facultad de Físicas UCM"
    observer_type = ObserverType.PERSON
    observer_name = "Prof. Jaime Zamorano"
    async with database.begin():
        for photinfo in [stars8000, stars8001]:
            await photometer_register(
                session=database,
                candidate=photinfo,
                place=place,
                observer_type=observer_type,
                observer_name=observer_name,
            )
        photometer = await photometer_lookup_current(session=database, candidate=stars8001)
        observer_id = await observer_id_lookup(database, observer_type, observer_name)
        location_id = await location_id_lookup(database, place)
        assert photometer.model == stars8001.model
        assert photometer.mac_address == stars8001.mac_address
        assert photometer.valid_state == ValidState.CURRENT
        assert photometer.nchannels == 1
        assert photometer.observer_id == observer_id
        assert photometer.location_id == location_id


@pytest.mark.asyncio
async def test_register_repair(database, stars8000, stars8000rep):
    place = "Facultad de Físicas UCM"
    observer_type = ObserverType.PERSON
    observer_name = "Prof. Jaime Zamorano"
    async with database.begin():
        for photinfo in [stars8000, stars8000rep]:
            await photometer_register(
                session=database,
                candidate=photinfo,
                place=place,
                observer_type=observer_type,
                observer_name=observer_name,
            )
        photometer = await photometer_lookup_current(session=database, candidate=stars8000rep)
        observer_id = await observer_id_lookup(database, observer_type, observer_name)
        location_id = await location_id_lookup(database, place)
        assert photometer.model == stars8000rep.model
        assert photometer.mac_address == stars8000rep.mac_address
        assert photometer.valid_state == ValidState.CURRENT
        assert photometer.nchannels == 1
        assert photometer.observer_id == observer_id
        assert photometer.location_id == location_id


@pytest.mark.asyncio
async def test_register_extinct(database, stars8000, stars8002, stars8002ex):
    place = "Facultad de Físicas UCM"
    observer_type = ObserverType.PERSON
    observer_name = "Prof. Jaime Zamorano"
    async with database.begin():
        for photinfo in [stars8000, stars8002]:
            await photometer_register(
                session=database,
                candidate=photinfo,
                place=place,
                observer_type=observer_type,
                observer_name=observer_name,
            )
        await photometer_register(
            session=database,
            candidate=stars8002ex,
            place=place,
            observer_type=observer_type,
            observer_name=observer_name,
        )
        photometer = await photometer_lookup_current(session=database, candidate=stars8000)
        assert photometer.mac_address == stars8000.mac_address
        assert photometer.valid_state == ValidState.CURRENT
        photometer = await photometer_lookup_current(session=database, candidate=stars8002)
        assert photometer.mac_address == stars8002.mac_address
        assert photometer.valid_state == ValidState.CURRENT


# ------------------------------------
# Replace an photometer back and forth
# ------------------------------------


@pytest.mark.asyncio
async def test_register_tessw_complex(database, stars8000, stars8000rep, stars8000rep2):
    assert stars8000.tstamp is not None
    async with database.begin():
        await photometer_register(
            session=database,
            candidate=stars8000,
        )
        log.info("registered the first one")
        await photometer_register(
            session=database,
            candidate=stars8000rep,
        )
        log.info("replaced photometer")
        await photometer_register(
            session=database,
            candidate=stars8000rep2,
        )
        log.info("replaced photometer back")
        photometers = await photometer_lookup_history(database, candidate=stars8000)
        assert len(photometers) == 2
        photometers = await photometer_lookup_history_current(database, candidate=stars8000)
        assert len(photometers) == 1


@pytest.mark.asyncio
async def test_assign(database, stars8000, melrose, ucm_full):
    assert stars8000.tstamp is not None

    async with database.begin():
        await location_create(session=database, candidate=melrose)
        await observer_create(session=database, candidate=ucm_full)
        await photometer_register(
            session=database,
            candidate=stars8000,
        )
    async with database.begin():
        await photometer_assign(
            database,
            phot_name=stars8000.name,
            place=melrose.place,
            observer_name=ucm_full.name,
            observer_type=ucm_full.type,
            update_readings=True,
        )
    async with database.begin():
        photometer = await photometer_lookup_current(session=database, candidate=stars8000)
        assert photometer.location_id != -1
        assert photometer.observer_id != -1


@pytest.mark.asyncio
async def test_assign_range(database, stars8000, melrose, ucm_full):
    assert stars8000.tstamp is not None

    async with database.begin():
        await location_create(session=database, candidate=melrose)
        await observer_create(session=database, candidate=ucm_full)
        await photometer_register(
            session=database,
            candidate=stars8000,
        )
    async with database.begin():
        await photometer_assign(
            database,
            phot_name=stars8000.name,
            place=melrose.place,
            observer_name=ucm_full.name,
            observer_type=ucm_full.type,
            update_readings=True,
            update_readings_since=datetime(year=2025, month=7, day=2),
            update_readings_until=datetime(year=2025, month=7, day=4),
        )
    async with database.begin():
        photometer = await photometer_lookup_current(session=database, candidate=stars8000)
        assert photometer.location_id != -1
        assert photometer.observer_id != -1
