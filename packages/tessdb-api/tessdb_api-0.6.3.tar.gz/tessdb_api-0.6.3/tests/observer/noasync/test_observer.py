import pytest
import logging
from argparse import Namespace

from pydantic import ValidationError

from lica.sqlalchemy import sqa_logging

from tessdbdao import ObserverType, ValidState
from tessdbapi.model import ObserverInfo

from tessdbapi.noasync.observer import (
    observer_lookup_current,
    observer_lookup_history,
    observer_create,
    observer_update,
)

from . import engine, Session
from ... import DbSize, copy_file

log = logging.getLogger(__name__.split(".")[-1])


@pytest.fixture(scope="function", params=[DbSize.MEDIUM])
def database(request):
    args = Namespace(verbose=False)
    sqa_logging(args)
    copy_file(f"tess.{request.param}.db", "tess.db")
    yield Session()
    log.info("Teardown code empty so far")
    engine.dispose()


def test_observer_1(database, ucm):
    with database.begin():
        observer_create(session=database, candidate=ucm)
        observer = observer_lookup_current(session=database, candidate=ucm)
        assert observer.type == ucm.type
        assert observer.name == ucm.name
        assert observer.valid_state == ValidState.CURRENT

    with database.begin():
        observer_create(session=database, candidate=ucm)
        observer = observer_lookup_history(session=database, candidate=ucm)
        assert len(observer) == 1

def test_observer_1b(database, ucm):
    with database.begin():
        observer = observer_create(session=database, candidate=ucm)
    with database.begin():
        database.refresh(observer)
        assert observer.type == ucm.type
        assert observer.name == ucm.name
        assert observer.valid_state == ValidState.CURRENT
    with database.begin():
        observer_create(session=database, candidate=ucm)
        observer = observer_lookup_history(session=database, candidate=ucm)
        assert len(observer) == 1



def test_observer_2(database, ucm):
    with database.begin():
        observer_create(session=database, candidate=ucm)
        observer_update(session=database, candidate=ucm, fix_current=False)
        observer = observer_lookup_history(session=database, candidate=ucm)
        assert len(observer) == 2
        assert observer[0].valid_state == ValidState.EXPIRED
        assert observer[1].valid_state == ValidState.CURRENT
        assert observer[0].valid_until == observer[1].valid_since


def test_observer_3(database, ucm_full):
    with database.begin():
        observer_create(session=database, candidate=ucm_full)
        observer_update(session=database, candidate=ucm_full, fix_current=False)
        observer_update(session=database, candidate=ucm_full, fix_current=True)
        observer = observer_lookup_history(session=database, candidate=ucm_full)
        assert len(observer) == 2
        assert observer[-1].valid_state == ValidState.CURRENT
        assert observer[-1].website_url == str(ucm_full.website_url)
        assert observer[-1].acronym == ucm_full.acronym


def test_observer_excp():
    with pytest.raises(ValidationError) as excinfo:
        _ = ObserverInfo(type=ObserverType.ORG)
    log.info(excinfo.type)
