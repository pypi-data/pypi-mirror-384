from http import HTTPStatus

from aiohttp import ClientSession, ClientTimeout, ClientError

from .const import DEFAULT_PORT, DEFAULT_TIMEOUT
from .errors import DeviceConnectionError, DeviceResponseError

async def get_config(session: ClientSession, host: str, port: int = DEFAULT_PORT, timeout = ClientTimeout(total=DEFAULT_TIMEOUT)) -> dict:
    """Get device configuration."""
    url = f"http://{host}:{port}/rpc/Sys.GetConfig"

    headers = {"name": "opend", "pass": "opend"}
    
    try:
        async with session.get(
            url,
            headers=headers,
            raise_for_status=True,
            timeout=timeout,
        ) as resp:
            data = await resp.json()
            validate_response(HTTPStatus(resp.status))
            return data
            
    except TimeoutError as err:
        raise DeviceConnectionError(f"Timeout connecting to {host}:{port}") from err
    except ClientError as err:
        raise DeviceConnectionError(f"Connection error to {host}:{port} {err}") from err
    except Exception as err:
        raise DeviceResponseError(f"Unexpected error: {err}") from err
    

def validate_response(status: HTTPStatus) -> bool:
    """Validate API response status and content."""
    if status != HTTPStatus.OK:
        raise DeviceResponseError(f"Unexpected status: {status}.")
    
    return True