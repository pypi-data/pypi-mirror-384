import pytest
import logging
from datetime import datetime, timezone

from pydantic import ValidationError

from tessdbdao import PhotometerModel, RegisterState
from tessdbapi.model import PhotometerInfo


log = logging.getLogger(__name__.split(".")[-1])


 
@pytest.fixture()
def stars8000():
    return PhotometerInfo(
        name="stars8000",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        firmware="0.1.0",
        authorised=True,
        registered=RegisterState.MANUAL,
        zp1=20.50,
        filter1="UV/IR-740",
        offset1=0.0,
        tstamp=None,
    )

def test_valid_zp_missing():
    with pytest.raises(ValidationError) as excp:
        PhotometerInfo(
        name="stars1",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        filter1="UV/IR-740",
        offset1=0,
        tstamp=None,
    )
    log.info(excp.value)

def test_valid_zp_bad_string():
    with pytest.raises(ValidationError) as excp:
        PhotometerInfo(
        name="stars1",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        zp1="foo",
        filter1="UV/IR-740",
        offset1=0,
        tstamp=None,
    )
    log.info(excp.value)

def test_valid_zp_string():
    msg = PhotometerInfo(
        tstamp=None,
        name="stars1",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        zp1="20.50",
        filter1="UV/IR-740",
        offset1=0,
    )
    log.info("%s", msg.zp1)
    assert msg.zp1 == 20.50

def test_valid_tstamp_missing():
    with pytest.raises(ValidationError):
        PhotometerInfo(
        name="stars1",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        zp1=20.50,
        filter1="UV/IR-740",
        offset1=0,
    )


def test_valid_tstamp_none_1():
    msg = PhotometerInfo(
        tstamp=None,
        name="stars1",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        zp1=20.50,
        filter1="UV/IR-740",
        offset1=0,
    )
    log.info("%s", msg.tstamp)
    assert msg.tstamp is not None

def test_valid_tstamp_none_2(stars8000):
    assert stars8000.tstamp is not None



def test_valid_tstamp_datetime_obj():
    msg = PhotometerInfo(
        tstamp=datetime.now(timezone.utc),
        name="stars1",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        zp1=20.50,
        filter1="UV/IR-740",
        offset1=0,
    )
    assert msg.tstamp is not None
    log.info("%s", msg.tstamp)


def test_valid_tstamp_datetime_str():
    msg = PhotometerInfo(
        tstamp="2025-09-08 09:40:09",
        name="stars1",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        zp1=20.50,
        filter1="UV/IR-740",
        offset1=0,
    )
    assert msg.tstamp is not None
    log.info("%s", msg.tstamp)


def test_valid_tstamp_datetime_str_tzone():
    value = "2025-09-08 09:40:09:+02:00"
    msg = PhotometerInfo(
        tstamp=value,
        name="stars1",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        zp1=20.50,
        filter1="UV/IR-740",
        offset1=0,
    )
    assert msg.tstamp is not None
    expected = datetime.strptime(value, "%Y-%m-%d %H:%M:%S:%z").astimezone(timezone.utc)
    log.info("Before: %s", value)
    log.info("After: %s, tzinfo is %s", expected, expected.tzinfo)
    log.info("Msg: %s", msg.tstamp)
    assert msg.tstamp == expected
   
def test_valid_tstamp_datetime_str_z():
    value = "2025-09-08 09:40:09Z"
    msg = PhotometerInfo(
        tstamp=value,
        name="stars1",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        zp1=20.50,
        filter1="UV/IR-740",
        offset1=0,
    )
    assert msg.tstamp is not None
    expected = datetime.strptime(value, "%Y-%m-%d %H:%M:%SZ").replace(tzinfo=timezone.utc)
    log.info("Before: %s", value)
    log.info("After: %s, tzinfo is %s", expected, expected.tzinfo)
    log.info("Msg: %s", msg.tstamp)
    assert msg.tstamp == expected
  