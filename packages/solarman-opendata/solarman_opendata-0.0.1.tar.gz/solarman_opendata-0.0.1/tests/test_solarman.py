import pytest
import asyncio
import aiohttp
from unittest.mock import patch, AsyncMock
from aiohttp import ClientSession, ClientResponse
from http import HTTPStatus
from solarman_opendata.solarman import Solarman, DeviceConnectionError

# Test constants
TEST_HOST = "test-host"
TEST_PORT = 8080
TEST_TIMEOUT = 5
TEST_DEVICE_TYPE = "SP-2W-EU"

# Mock response data
MOCK_CONFIG_RESPONSE = {"type": TEST_DEVICE_TYPE}
MOCK_DATA_RESPONSE = {"power": 100}
MOCK_STATUS_RESPONSE = {"status": "on"}

@pytest.fixture
async def mock_session():
    """Creates an aiohttp session with mocked request method"""
    session = AsyncMock(spec=ClientSession)
    session.request = AsyncMock()
    return session

@pytest.fixture
def api_client(mock_session):
    """Initializes Solarman client for testing"""
    return Solarman(
        session=mock_session,
        host=TEST_HOST,
        port=TEST_PORT,
        timeout=TEST_TIMEOUT
    )

@pytest.mark.asyncio
async def test_initialization(api_client, mock_session):
    """Tests API client initialization parameters"""
    assert api_client.host == TEST_HOST
    assert api_client.port == TEST_PORT
    assert api_client.timeout.total == TEST_TIMEOUT
    assert api_client.base_url == f"http://{TEST_HOST}:{TEST_PORT}/rpc"
    assert api_client.device_type is None

@pytest.fixture
async def mock_session():
    """Creates an aiohttp session with mocked request method"""
    session = AsyncMock(spec=ClientSession)
    
    mock_context_manager = AsyncMock()
    session.request.return_value = mock_context_manager
    
    return session


@pytest.mark.asyncio
async def test_request_success(api_client, mock_session):
    """Tests successful API request handling"""
    # Mock successful response
    mock_resp = AsyncMock(spec=ClientResponse)
    mock_resp.status = HTTPStatus.OK
    mock_resp.json.return_value = MOCK_DATA_RESPONSE
    
    mock_context_manager = mock_session.request.return_value
    mock_context_manager.__aenter__.return_value = mock_resp

    status, data = await api_client.request("GET", "test_api")
    
    assert status == HTTPStatus.OK
    assert data == MOCK_DATA_RESPONSE
    mock_session.request.assert_called_once_with(
        method="GET",
        url=f"{api_client.base_url}/test_api",
        params=None,
        headers=api_client.headers,
        raise_for_status=True,
        timeout=api_client.timeout
    )

@pytest.mark.asyncio
async def test_request_timeout_error(api_client, mock_session):
    """Tests timeout error handling in request method"""
    mock_session.request.side_effect = asyncio.TimeoutError("Timeout")
    
    with pytest.raises(DeviceConnectionError) as exc_info:
        await api_client.request("GET", "test_api")
    
    assert f"Timeout connecting to {TEST_HOST}:{TEST_PORT}" in str(exc_info.value)

@pytest.mark.asyncio
async def test_request_client_error(api_client, mock_session):
    """Tests connection error handling in request method"""
    mock_session.request.side_effect = aiohttp.ClientError("Connection failed")
    
    with pytest.raises(DeviceConnectionError) as exc_info:
        await api_client.request("GET", "test_api")
    
    assert f"Connection error to {TEST_HOST}:{TEST_PORT}" in str(exc_info.value)

@pytest.mark.asyncio
async def test_fetch_data(api_client):
    """Tests data fetching with device type detection"""
    mock_config_resp = AsyncMock(spec=ClientResponse)
    mock_config_resp.status = 200
    mock_config_resp.json = AsyncMock(return_value=MOCK_CONFIG_RESPONSE)
    
    with patch.object(api_client.session, 'get') as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_config_resp
        
        api_client.request = AsyncMock(return_value=(HTTPStatus.OK, MOCK_DATA_RESPONSE))
        api_client.get_status = AsyncMock(return_value=MOCK_STATUS_RESPONSE)
        
        result = await api_client.fetch_data()
    
    data = {}
    data.update(MOCK_STATUS_RESPONSE)
    data.update(MOCK_DATA_RESPONSE)
    assert result == data

@pytest.mark.asyncio
@patch.object(Solarman, "request", AsyncMock(return_value=(HTTPStatus.OK, MOCK_STATUS_RESPONSE)))
async def test_get_status_supported_device(api_client):
    """Tests status retrieval for supported device type"""
    api_client.device_type = TEST_DEVICE_TYPE
    status = await api_client.get_status()
    assert status == MOCK_STATUS_RESPONSE

@pytest.mark.asyncio
async def test_get_status_unsupported_device(api_client):
    """Tests status retrieval for unsupported device type"""
    api_client.device_type = "UNSUPPORTED_DEVICE"
    status = await api_client.get_status()
    assert status == {}

@pytest.mark.asyncio
@patch.object(Solarman, "request", AsyncMock(return_value=(HTTPStatus.OK, {"result": True})))
async def test_set_status_success(api_client):
    """Tests successful plug control (on/off)"""
    api_client.device_type = TEST_DEVICE_TYPE
    
    # Test turn on
    await api_client.set_status(True)
    Solarman.request.assert_called_with(
        "POST",
        "Plug.SetStatus",
        {"config": '{"switch_status":"on"}'}  # Note: No spaces in JSON
    )
    
    # Test turn off
    await api_client.set_status(False)
    Solarman.request.assert_called_with(
        "POST",
        "Plug.SetStatus",
        {"config": '{"switch_status":"off"}'}
    )

@pytest.mark.asyncio
@patch.object(Solarman, "request", AsyncMock(return_value=(HTTPStatus.OK, {"result": False})))
async def test_set_status_failure(api_client, caplog):
    """Tests failed plug control operation"""
    api_client.device_type = TEST_DEVICE_TYPE
    await api_client.set_status(True)
    
    # Verify error logging
    assert "Failed to set switch state" in caplog.text