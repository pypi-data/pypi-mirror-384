import pytest
import json
from .auth_mock import AuthMock
from homelink.provider import Provider
from homelink.settings import DISCOVER_URL, ENABLE_URL, STATE_URL


@pytest.fixture
def authorized_provider():
    with (
        open("tests/fixtures/discover_post.json") as discover_post_json,
        open("tests/fixtures/enable_post.json") as enable_post_json,
        open("tests/fixtures/state_get.json") as state_get_json,
    ):
        auth = AuthMock(
            {
                DISCOVER_URL: {
                    "POST": {
                        "DISCOVER": json.load(discover_post_json),
                        "ENABLE": json.load(enable_post_json),
                    }
                },
                STATE_URL: {"GET": json.load(state_get_json)},
            }
        )
    provider = Provider(auth)
    return provider


@pytest.mark.asyncio
async def test_discover(authorized_provider):
    devices = await authorized_provider.discover()
    assert len(devices) == 1
    assert devices[0].name == "PhiDevice"
    assert len(devices[0].buttons) == 3
    assert [b.name for b in devices[0].buttons] == ["Button 1", "Button 2", "Button 3"]


@pytest.mark.asyncio
async def test_enable(authorized_provider):
    enable_data = await authorized_provider.enable()
    assert enable_data["success"] == True


@pytest.mark.asyncio
async def test_get_state(authorized_provider):
    request_sync, state = await authorized_provider.get_state()
    assert request_sync
    assert request_sync["requestId"]
    assert request_sync["timestamp"]
    assert state
    assert state["9084ba1f-5f4c-4ccf-a168-13aabefc32a4"]
