import pytest
from datetime import datetime, timezone
from tessdbdao import PhotometerModel, RegisterState, ObserverType
from tessdbapi.model import PhotometerInfo, LocationInfo, ObserverInfo

 
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
        tstamp=datetime(2025,9, 10, 12, 00, 00, tzinfo=timezone.utc).replace(microsecond=0),
    )


@pytest.fixture()
def stars8000zp():
    return PhotometerInfo(
        name="stars8000",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        firmware="0.1.0",
        authorised=True,
        registered=RegisterState.MANUAL,
        zp1=20.33,
        filter1="UV/IR-740",
        offset1=0.001,
        tstamp=None,
    )


@pytest.fixture()
def stars8001():
    return PhotometerInfo(
        name="stars8001",
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


@pytest.fixture()
def stars8000rep():
    return PhotometerInfo(
        name="stars8000",
        mac_address="FF:EE:DD:CC:BB:AA",
        model=PhotometerModel.TESSW,
        firmware="0.1.0",
        authorised=True,
        registered=RegisterState.MANUAL,
        zp1=20.48,
        filter1="UV/IR-740",
        offset1=0.0,
        tstamp=datetime(2025,9, 10, 12, 5, 00, tzinfo=timezone.utc).replace(microsecond=0),
    )

@pytest.fixture()
def stars8000rep2():
    return PhotometerInfo(
        name="stars8000",
        mac_address="AA:BB:CC:DD:EE:FF",
        model=PhotometerModel.TESSW,
        firmware="0.1.0",
        authorised=True,
        registered=RegisterState.MANUAL,
        zp1=20.48,
        filter1="UV/IR-740",
        offset1=0.0,
        tstamp=datetime(2025,9, 10, 12, 10, 00, tzinfo=timezone.utc).replace(microsecond=0),
    )



@pytest.fixture()
def stars8002():
    return PhotometerInfo(
        name="stars8002",
        mac_address="CC:AA:CC:AA:DD:AA",
        model=PhotometerModel.TESSW,
        firmware="0.1.0",
        authorised=True,
        registered=RegisterState.MANUAL,
        zp1=20.50,
        filter1="UV/IR-740",
        offset1=0.0,
        tstamp=None,
    )


@pytest.fixture()
def stars8002ex():
    return PhotometerInfo(
        name="stars8000",
        mac_address="CC:AA:CC:AA:DD:AA",
        model=PhotometerModel.TESSW,
        firmware="0.1.0",
        authorised=True,
        registered=RegisterState.MANUAL,
        zp1=20.50,
        filter1="UV/IR-740",
        offset1=0.0,
        tstamp=None,
    )


@pytest.fixture()
def stars8010():
    return PhotometerInfo(
        name="stars8010",
        mac_address="AA:CC:BB:DD:AA:DD",
        model=PhotometerModel.TESS4C,
        firmware="0.1.0",
        authorised=True,
        registered=RegisterState.MANUAL,
        zp1=20.30,
        filter1="Johnson-V",
        offset1=0.0,
        zp2=20.35,
        filter2="Johnson-R",
        offset2=0.0,
        zp3=20.40,
        filter3="Johnson-B",
        offset3=0.0,
        zp4=20.50,
        filter4="UV/IR-740",
        offset4=0.0,
        tstamp=None,
    )


@pytest.fixture()
def stars8010zp():
    return PhotometerInfo(
        name="stars8010",
        mac_address="AA:CC:BB:DD:AA:DD",
        model=PhotometerModel.TESS4C,
        firmware="0.1.0",
        authorised=True,
        registered=RegisterState.MANUAL,
        zp1=20.31,
        filter1="Johnson-V",
        offset1=0.0,
        zp2=20.30,
        filter2="Johnson-R",
        offset2=0.0,
        zp3=20.40,
        filter3="Johnson-B",
        offset3=0.0,
        zp4=20.51,
        filter4="UV/IR-750",
        offset4=0.0,
        tstamp=None,
    )


@pytest.fixture()
def stars993():
    return PhotometerInfo(
        name="stars993",
        mac_address="4C:75:25:27:7E:A2",  # Latest entry
        model=PhotometerModel.TESSW,
        firmware="0.1.0",
        authorised=True,
        registered=RegisterState.MANUAL,
        zp1=20.99,
        filter1="UV/IR-740",
        offset1=0.0,
        tstamp=None,
    )


@pytest.fixture()
def melrose(request) -> LocationInfo:
    return LocationInfo(
        longitude=-3.6124434,
        latitude=40.4208393,
        height=900,
        place="Melrose Place",
    )


@pytest.fixture()
def ucm_full(request) -> ObserverInfo:
    return ObserverInfo(
        type=ObserverType.ORG,
        name="Universidad Complutense de Madrid",
        website_url="https://www.ucm.es",
        acronym="UCM",
    )
