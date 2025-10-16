import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock
from aiohttp import ClientSession, ClientTimeout, ClientResponse
from solarman_opendata.utils import get_config, validate_response
from solarman_opendata.errors import DeviceConnectionError, DeviceResponseError

# Test constants
TEST_HOST = "test-host"
TEST_PORT = 8080
TEST_TIMEOUT = 5

@pytest.mark.asyncio
async def test_get_config_success():
    """Tests successful device configuration retrieval"""
    # Mock session and response
    mock_session = AsyncMock(spec=ClientSession)
    mock_resp = AsyncMock(spec=ClientResponse)

    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"device": "config"})
    mock_session.get.return_value.__aenter__.return_value = mock_resp

    # Call function
    data = await get_config(
        session=mock_session,
        host=TEST_HOST,
        port=TEST_PORT,
        timeout=ClientTimeout(total=TEST_TIMEOUT)
    )
    
    # Validate results
    assert data == {"device": "config"}
    mock_session.get.assert_called_once_with(
        f"http://{TEST_HOST}:{TEST_PORT}/rpc/Sys.GetConfig",
        headers={"name": "opend", "pass": "opend"},
        raise_for_status=True,
        timeout=ClientTimeout(total=5)
    )

@pytest.mark.asyncio
async def test_get_config_timeout_error():
    """Tests timeout error during configuration retrieval"""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.get.side_effect = asyncio.TimeoutError("Timeout")
    
    # Verify exception
    with pytest.raises(DeviceConnectionError) as exc_info:
        await get_config(mock_session, TEST_HOST, TEST_PORT)
    
    assert f"Timeout connecting to {TEST_HOST}:{TEST_PORT}" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_config_client_error():
    """Tests client connection errors during configuration retrieval"""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.get.side_effect = aiohttp.ClientError("Connection failed")
    
    # Verify exception
    with pytest.raises(DeviceConnectionError) as exc_info:
        await get_config(mock_session, TEST_HOST, TEST_PORT)
    
    assert f"Connection error to {TEST_HOST}:{TEST_PORT}" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_config_unexpected_error():
    """Tests unexpected exceptions during configuration retrieval"""
    mock_session = AsyncMock(spec=ClientSession)
    mock_session.get.side_effect = Exception("Critical failure")
    
    # Verify exception
    with pytest.raises(DeviceResponseError) as exc_info:
        await get_config(mock_session, TEST_HOST, TEST_PORT)
    
    assert "Unexpected error: Critical failure" in str(exc_info.value)

def test_validate_response_success():
    """Tests successful response validation (200 status)"""
    # Should not raise exception
    assert validate_response(200) is True

def test_validate_response_failure():
    """Tests failure response validation (non-200 status)"""
    with pytest.raises(DeviceResponseError) as exc_info:
        validate_response(404)
    
    assert "Unexpected status: 404." in str(exc_info.value)