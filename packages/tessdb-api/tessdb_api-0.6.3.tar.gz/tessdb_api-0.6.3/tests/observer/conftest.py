import pytest

from tessdbdao import ObserverType
from tessdbapi.model import ObserverInfo


@pytest.fixture()
def ucm(request) -> ObserverInfo:
    return ObserverInfo(
        type=ObserverType.ORG,
        name="Universidad Complutense de Madrid",
    )


@pytest.fixture()
def ucm_full(request) -> ObserverInfo:
    return ObserverInfo(
        type=ObserverType.ORG,
        name="Universidad Complutense de Madrid",
        website_url="https://www.ucm.es",
        acronym="UCM",
    )
