import pytest
import logging
from argparse import Namespace

from lica.sqlalchemy import sqa_logging


from tessdbapi.noasync.location import location_lookup, location_create, location_update

from . import engine, Session
from ... import DbSize, copy_file

log = logging.getLogger(__name__.split(".")[-1])


@pytest.fixture(scope="function", params=[DbSize.MEDIUM])
def database(request):
    args = Namespace(verbose=True)
    sqa_logging(args)
    copy_file(f"tess.{request.param}.db", "tess.db")
    yield Session()
    log.info("Teardown code empty so far")
    engine.dispose()


def test_location_create_1(database, melorse):
    with database.begin():
        location_create(session=database, candidate=melorse)
        location = location_lookup(session=database, candidate=melorse)
        assert location.longitude == melorse.longitude
        assert location.latitude == melorse.latitude
        assert location.elevation == melorse.height
        assert location.country == "Spain"
        assert location.timezone == "Europe/Paris"

def test_location_create_1b(database, melorse):
    with database.begin():
        location = location_create(session=database, candidate=melorse)
    with database.begin():
        database.refresh(location)
        log.info(location.location_id)
        assert location.longitude == melorse.longitude
        assert location.latitude == melorse.latitude
        assert location.elevation == melorse.height
        assert location.country == "Spain"
        assert location.timezone == "Europe/Paris"


def test_location_create_2(database, melorse):
    with database.begin():
        location_create(session=database, candidate=melorse)
        location_create(session=database, candidate=melorse)


def test_location_update_1(database, melorse):
    with database.begin():
        location_create(session=database, candidate=melorse)
    log.info("Updating Location")
    melorse.height = 880
    melorse.timezone = "Europe/Madrid"
    with database.begin():
        location = location_update(session=database, candidate=melorse)
    with database.begin():
        database.refresh(location)
        assert location.longitude == melorse.longitude
        assert location.latitude == melorse.latitude
        assert location.elevation == melorse.height
        assert location.timezone == melorse.timezone
