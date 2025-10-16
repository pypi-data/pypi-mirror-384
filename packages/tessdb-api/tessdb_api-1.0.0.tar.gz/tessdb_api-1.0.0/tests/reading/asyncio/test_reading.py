import pytest
import pytest_asyncio
import logging
from argparse import Namespace
from typing import List
from datetime import datetime, timezone

from sqlalchemy import select
from pydantic import ValidationError

from lica.sqlalchemy import sqa_logging

from tessdbdao import ReadingSource
from tessdbdao.asyncio import TessReadings, Tess4cReadings

from tessdbapi.model import ReadingInfo1c
from tessdbapi.asyncio.photometer.reading import (
    resolve_references,
    tess_new,
    tess4c_new,
    photometer_batch_write,
)

from . import engine, Session
from ... import DbSize, copy_file

log = logging.getLogger(__name__.split(".")[-1])


# -------------------------------
# helper functions for test cases
# -------------------------------


async def fetch_readings(session: Session) -> List[TessReadings]:
    query = select(TessReadings).order_by(TessReadings.date_id.asc(), TessReadings.time_id.asc())
    return (await session.scalars(query)).all()


async def fetch_readings4c(session: Session) -> List[Tess4cReadings]:
    query = select(Tess4cReadings).order_by(
        Tess4cReadings.date_id.asc(), Tess4cReadings.time_id.asc()
    )
    return (await session.scalars(query)).all()


# ------------------
# Convenient fixtures
# -------------------


@pytest_asyncio.fixture(params=[DbSize.MEDIUM])
async def database(request):
    args = Namespace(verbose=True)
    sqa_logging(args)
    copy_file(f"tess.{request.param}.db", "tess.db")
    yield Session()
    log.info("Teardown code disposes the engine")
    await engine.dispose()


@pytest.mark.asyncio
async def test_reading_nonexists(database, stars8000r1):
    async with database.begin():
        ref = await resolve_references(
            session=database,
            reading=stars8000r1,
            auth_filter=False,
            latest=False,
            source=ReadingSource.IMPORTED,
        )
        assert ref is None


@pytest.mark.asyncio
async def test_reading_wrong_hash(database, stars1r1_wrong_hash):
    async with database.begin():
        ref = await resolve_references(
            session=database,
            reading=stars1r1_wrong_hash,
            auth_filter=False,
            latest=False,
            source=ReadingSource.IMPORTED,
        )
        assert ref is None


@pytest.mark.asyncio
async def test_reading_good_hash(database, stars1r1_good_hash):
    async with database.begin():
        ref = await resolve_references(
            session=database,
            reading=stars1r1_good_hash,
            auth_filter=False,
            latest=False,
            source=ReadingSource.IMPORTED,
        )
        assert ref is not None


@pytest.mark.asyncio
async def test_reading_authorization(database, stars100r1, stars1r1):
    async with database.begin():
        ref = await resolve_references(
            session=database,
            reading=stars1r1,
            auth_filter=True,
            latest=False,
            source=ReadingSource.IMPORTED,
        )
        assert ref is not None
        ref = await resolve_references(
            session=database,
            reading=stars100r1,
            auth_filter=True,
            latest=False,
            source=ReadingSource.IMPORTED,
        )
        assert ref is None


@pytest.mark.asyncio
async def test_reading_write_1(database, stars1r1):
    async with database.begin():
        ref = await resolve_references(
            session=database,
            reading=stars1r1,
            auth_filter=False,
            latest=False,
            source=ReadingSource.IMPORTED,
        )
        if ref is not None:
            obj = tess_new(
                reading=stars1r1,
                reference=ref,
            )
            database.add(obj)
        await database.commit()
    async with database.begin():
        readings = await fetch_readings(database)
    assert len(readings) == 1
    assert readings[0].sequence_number == 1


@pytest.mark.asyncio
async def test_reading_write_4(database, stars1_sparse):
    await photometer_batch_write(database, stars1_sparse)
    async with database.begin():
        readings = await fetch_readings(database)
    assert len(readings) == 4


@pytest.mark.asyncio
async def test_reading_write_dup(database, stars1_sparse, stars1_dense):
    await photometer_batch_write(database, stars1_sparse)
    async with database.begin():
        readings = await fetch_readings(database)
    assert len(readings) == 4
    await photometer_batch_write(database, stars1_dense)
    async with database.begin():
        readings = await fetch_readings(database)
    assert len(readings) == 10


@pytest.mark.asyncio
async def test_reading_write_dup2(database, stars1_sparse_dup):
    await photometer_batch_write(database, stars1_sparse_dup)
    async with database.begin():
        readings = await fetch_readings(database)
    assert len(readings) == 3


@pytest.mark.asyncio
async def test_reading_write_mixed(database, stars1_mixed):
    await photometer_batch_write(database, stars1_mixed)
    async with database.begin():
        readings = await fetch_readings(database)
    assert len(readings) == len(stars1_mixed) - 2


@pytest.mark.asyncio
async def test_reading4c_write_1(database, stars701):
    async with database.begin():
        ref = await resolve_references(
            session=database,
            reading=stars701,
            auth_filter=False,
            latest=False,
            source=ReadingSource.IMPORTED,
        )
        if ref is not None:
            obj = tess4c_new(
                reading=stars701,
                reference=ref,
            )
            database.add(obj)
        await database.commit()
    async with database.begin():
        readings = await fetch_readings4c(database)
    assert len(readings) == 1
    assert readings[0].sequence_number == 1


@pytest.mark.asyncio
async def test_reading4c_write_1b(database, stars701):
    await photometer_batch_write(
        database,
        [
            stars701,
        ],
    )
    async with database.begin():
        readings = await fetch_readings4c(database)
    assert len(readings) == 1
    assert readings[0].sequence_number == 1


@pytest.mark.asyncio
async def test_reading4c_write_5(database, stars701_seq):
    await photometer_batch_write(database, stars701_seq)
    async with database.begin():
        readings = await fetch_readings4c(database)
    assert len(readings) == 5


@pytest.mark.asyncio
async def test_reading4c_write_mixed(database, stars_mixed):
    await photometer_batch_write(database, stars_mixed)
    async with database.begin():
        readings_1 = await fetch_readings(database)
        readings_2 = await fetch_readings4c(database)
    assert len(readings_1) == 10
    assert len(readings_2) == 5


def test_valid_reading_1(database):
    with pytest.raises(ValidationError) as e:
        ReadingInfo1c(
            tstamp=datetime.now(timezone.utc).replace(microsecond=0),
            name=None,
            sequence_number=1,
            freq1=0,
            mag1=0,
            box_temperature=0,
            sky_temperature=-10,
            signal_strength=-70,
        )
    log.info(e.value.errors())
    excp = e.value.errors()[0]
    assert excp["type"] == "string_type"
    assert excp["loc"][0] == "name"
    with pytest.raises(ValidationError) as e:
        ReadingInfo1c(
            tstamp=datetime.now(timezone.utc).replace(microsecond=0),
            name="foo",
            sequence_number=1,
            freq1=0,
           mag1=0,
            box_temperature=0,
            sky_temperature=-10,
            signal_strength=-70,
        )
    log.info(e.value.errors())
    excp = e.value.errors()[0]
    assert excp["type"] == "value_error"
    assert excp["loc"][0] == "name"
    with pytest.raises(ValidationError) as e:
        ReadingInfo1c(
            tstamp=datetime.now(timezone.utc).replace(microsecond=0),
            name="stars1024",
            sequence_number=1,
            freq1=0,
           mag1=0,
            box_temperature=0,
            sky_temperature=-10,
            signal_strength=-70,
            hash="GAGA",
        )
    log.info(e.value.errors())
    excp = e.value.errors()[0]
    assert excp["type"] == "value_error"
    assert excp["loc"][0] == "hash"
    with pytest.raises(ValidationError) as e:
        ReadingInfo1c(
            tstamp=datetime.now(timezone.utc).replace(microsecond=0),
            name="foo",
            sequence_number=1,
            freq1=0,
           mag1=0,
            box_temperature=0,
            sky_temperature=-10,
            signal_strength=-70,
            hash="GAGA",
        )
    log.info(e.value.errors())
    excp = e.value.errors()
    assert excp[0]["type"] == "value_error"
    assert excp[0]["loc"][0] == "name"
    assert excp[1]["type"] == "value_error"
    assert excp[1]["loc"][0] == "hash"
