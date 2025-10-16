import pytest
import pytest_asyncio

import logging
from argparse import Namespace

from pydantic import ValidationError

from lica.sqlalchemy import sqa_logging

from tessdbdao import ObserverType, ValidState
from tessdbapi.model import ObserverInfo

from tessdbapi.asyncio.observer import (
    observer_lookup_current,
    observer_lookup_history,
    observer_create,
    observer_update,
)

from . import engine, Session
from ... import DbSize, copy_file

log = logging.getLogger(__name__.split(".")[-1])


@pytest_asyncio.fixture(params=[DbSize.MEDIUM])
async def database(request):
    args = Namespace(verbose=False)
    sqa_logging(args)
    copy_file(f"tess.{request.param}.db", "tess.db")
    yield Session()
    log.info("Teardown code disposes the engine")
    await engine.dispose()


@pytest.mark.asyncio
async def test_observer_1(database, ucm):
    async with database.begin():
        await observer_create(session=database, candidate=ucm)
        observer = await observer_lookup_current(session=database, candidate=ucm)
        assert observer.type == ucm.type
        assert observer.name == ucm.name
        assert observer.valid_state == ValidState.CURRENT

    async with database.begin():
        await observer_create(session=database, candidate=ucm)
        observer = await observer_lookup_history(session=database, candidate=ucm)
        assert len(observer) == 1

@pytest.mark.asyncio
async def test_observer_1b(database, ucm):
    async with database.begin():
        observer = await observer_create(session=database, candidate=ucm)
    async with database.begin():
        await database.refresh(observer)
        assert observer.type == ucm.type
        assert observer.name == ucm.name
        assert observer.valid_state == ValidState.CURRENT

    async with database.begin():
        await observer_create(session=database, candidate=ucm)
        observer = await observer_lookup_history(session=database, candidate=ucm)
        assert len(observer) == 1


@pytest.mark.asyncio
async def test_observer_2(database, ucm):
    async with database.begin():
        await observer_create(session=database, candidate=ucm)
        await observer_update(session=database, candidate=ucm, fix_current=False)
        observer = await observer_lookup_history(session=database, candidate=ucm)
        assert len(observer) == 2
        assert observer[0].valid_state == ValidState.EXPIRED
        assert observer[1].valid_state == ValidState.CURRENT
        assert observer[0].valid_until == observer[1].valid_since

@pytest.mark.asyncio
async def test_observer_3(database, ucm_full):
    async with database.begin():
        await observer_create(session=database, candidate=ucm_full)
        await observer_update(session=database, candidate=ucm_full, fix_current=False)
        await observer_update(session=database, candidate=ucm_full, fix_current=True)
        observer = await observer_lookup_history(session=database, candidate=ucm_full)
        assert len(observer) == 2
        assert observer[-1].valid_state == ValidState.CURRENT
        assert observer[-1].website_url == str(ucm_full.website_url)
        assert observer[-1].acronym == ucm_full.acronym


def test_observer_excp():
    with pytest.raises(ValidationError) as excinfo:
        _ = ObserverInfo(type=ObserverType.ORG)
    log.info(excinfo.type)
