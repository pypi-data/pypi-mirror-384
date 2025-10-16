import pytest
import pytest_asyncio
import logging
from argparse import Namespace

from lica.sqlalchemy import sqa_logging


from tessdbapi.asyncio.location import location_lookup, location_create, location_update

from . import engine, Session
from ... import DbSize, copy_file

log = logging.getLogger(__name__.split(".")[-1])


@pytest_asyncio.fixture(params=[DbSize.MEDIUM])
async def database(request):
    args = Namespace(verbose=True)
    sqa_logging(args)
    copy_file(f"tess.{request.param}.db", "tess.db")
    yield Session()
    log.info("Teardown code disposes the engine")
    await engine.dispose()


@pytest.mark.asyncio
async def test_location_create_1(database, melorse):
    async with database.begin():
        await location_create(session=database, candidate=melorse)
        location = await location_lookup(session=database, candidate=melorse)
        assert location.longitude == melorse.longitude
        assert location.latitude == melorse.latitude
        assert location.elevation == melorse.height
        assert location.country == "Spain"
        assert location.timezone == "Europe/Paris"


@pytest.mark.asyncio
async def test_location_create_1b(database, melorse):
    async with database.begin():
        location = await location_create(session=database, candidate=melorse)
    async with database.begin():
        await database.refresh(location)
        log.info(location.location_id)
        assert location.longitude == melorse.longitude
        assert location.latitude == melorse.latitude
        assert location.elevation == melorse.height
        assert location.country == "Spain"
        assert location.timezone == "Europe/Paris"


@pytest.mark.asyncio
async def test_location_create_2(database, melorse):
    async with database.begin():
        await location_create(session=database, candidate=melorse)
        await location_create(session=database, candidate=melorse)

@pytest.mark.asyncio
async def test_location_update_1(database, melorse):
    async with database.begin():
        await location_create(session=database, candidate=melorse)
    log.info("Updating Location")
    melorse.height = 880
    melorse.timezone = "Europe/Madrid"
    async with database.begin():
        await location_update(session=database, candidate=melorse)
        location = await location_lookup(session=database, candidate=melorse)
    async with database.begin():
        await database.refresh(location)
        assert location.longitude == melorse.longitude
        assert location.latitude == melorse.latitude
        assert location.elevation == melorse.height
        assert location.timezone == melorse.timezone
