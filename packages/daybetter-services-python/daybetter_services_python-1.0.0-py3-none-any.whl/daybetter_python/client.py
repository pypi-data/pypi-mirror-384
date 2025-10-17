"""DayBetter API client."""

import aiohttp
import logging
from typing import Any, Dict, List, Optional, Tuple

from .exceptions import DayBetterError, AuthenticationError, APIError

_LOGGER = logging.getLogger(__name__)


class DayBetterClient:
    """DayBetter API client."""
    
    def __init__(
        self, 
        token: str, 
        base_url: str = "https://a.dbiot.org/daybetter/hass/api/v1.0/"
    ):
        """Initialize the client.
        
        Args:
            token: Authentication token
            base_url: Base URL for the API
        """
        self.token = token
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_valid = True
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session:
            self._session = aiohttp.ClientSession()
        return self._session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {"Authorization": f"Bearer {self.token}"}
    
    async def fetch_devices(self) -> List[Dict[str, Any]]:
        """Fetch devices from API.
        
        Returns:
            List of device dictionaries
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        try:
            session = self._get_session()
            url = f"{self.base_url}hass/devices"
            headers = self._get_headers()
            
            async with session.post(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    devices = data.get("data", [])
                    _LOGGER.debug("Fetched devices: %s", devices)
                    self._auth_valid = True
                    return devices
                elif resp.status == 401:
                    _LOGGER.error("Authentication failed - token may be expired")
                    self._auth_valid = False
                    raise AuthenticationError("Authentication failed - token may be expired")
                else:
                    error_text = await resp.text()
                    _LOGGER.error("Failed to fetch devices: %s", error_text)
                    raise APIError(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.exception("Client error while fetching devices: %s", e)
            raise APIError(f"Client error: {e}")
        except Exception as e:
            _LOGGER.exception("Exception while fetching devices: %s", e)
            raise DayBetterError(f"Unexpected error: {e}")
    
    async def fetch_pids(self) -> Dict[str, Any]:
        """Fetch device type PIDs.
        
        Returns:
            Dictionary of device type PIDs
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        try:
            session = self._get_session()
            url = f"{self.base_url}hass/pids"
            headers = self._get_headers()
            
            async with session.post(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._auth_valid = True
                    return data.get("data", {})
                elif resp.status == 401:
                    _LOGGER.error("Authentication failed - token may be expired")
                    self._auth_valid = False
                    raise AuthenticationError("Authentication failed - token may be expired")
                else:
                    error_text = await resp.text()
                    _LOGGER.error("Failed to fetch PIDs: %s", error_text)
                    raise APIError(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.exception("Client error while fetching PIDs: %s", e)
            raise APIError(f"Client error: {e}")
        except Exception as e:
            _LOGGER.exception("Exception while fetching PIDs: %s", e)
            raise DayBetterError(f"Unexpected error: {e}")
    
    async def control_device(
        self,
        device_name: str,
        action: bool,
        brightness: Optional[int] = None,
        hs_color: Optional[Tuple[float, float]] = None,
        color_temp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Control a device.
        
        Args:
            device_name: Name of the device to control
            action: Switch action (True/False)
            brightness: Brightness value (0-255)
            hs_color: Hue and saturation tuple (hue, saturation)
            color_temp: Color temperature in mireds
            
        Returns:
            Control result dictionary
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        session = self._get_session()
        url = f"{self.base_url}hass/control"
        headers = self._get_headers()
        
        # Priority: color temperature > color > brightness > switch
        if color_temp is not None:
            # Convert mireds to Kelvin
            kelvin = int(1000000 / color_temp)
            payload = {
                "deviceName": device_name,
                "type": 4,  # Type 4 is color temperature control
                "kelvin": kelvin,
            }
        elif hs_color is not None:
            h, s = hs_color
            v = (brightness / 255) if brightness is not None else 1.0
            payload = {
                "deviceName": device_name,
                "type": 3,
                "hue": h,
                "saturation": s / 100,
                "brightness": v,
            }
        elif brightness is not None:
            payload = {
                "deviceName": device_name, 
                "type": 2, 
                "brightness": brightness
            }
        else:
            # Type 1 control switch is used by default
            payload = {
                "deviceName": device_name, 
                "type": 1, 
                "on": action
            }
        
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    self._auth_valid = True
                    return await resp.json()
                elif resp.status == 401:
                    _LOGGER.error("Authentication failed - token may be expired")
                    self._auth_valid = False
                    raise AuthenticationError("Authentication failed - token may be expired")
                else:
                    error_text = await resp.text()
                    _LOGGER.error(
                        "Failed to control device %s: HTTP %d - %s", 
                        device_name, resp.status, error_text
                    )
                    raise APIError(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.exception(
                "Client error while controlling device %s: %s", device_name, e
            )
            raise APIError(f"Client error: {e}")
        except Exception as e:
            _LOGGER.exception(
                "Exception while controlling device %s: %s", device_name, e
            )
            raise DayBetterError(f"Unexpected error: {e}")
    
    async def fetch_mqtt_config(self) -> Dict[str, Any]:
        """Fetch MQTT connection configuration.
        
        Returns:
            MQTT configuration dictionary
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        session = self._get_session()
        url = f"{self.base_url}hass/cert"
        headers = self._get_headers()
        _LOGGER.debug("Requesting MQTT configuration URL: %s", url)
        
        try:
            async with session.post(url, headers=headers) as resp:
                _LOGGER.debug("MQTT configuration API response status: %d", resp.status)
                
                if resp.status == 200:
                    data = await resp.json()
                    _LOGGER.debug("MQTT configuration API raw response: %s", data)
                    self._auth_valid = True
                    return data.get("data", {})
                elif resp.status == 401:
                    _LOGGER.error("Authentication failed - token may be expired")
                    self._auth_valid = False
                    raise AuthenticationError("Authentication failed - token may be expired")
                else:
                    error_text = await resp.text()
                    _LOGGER.error("Failed to fetch MQTT config: %s", error_text)
                    raise APIError(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            _LOGGER.exception("Client error while fetching MQTT config: %s", e)
            raise APIError(f"Client error: {e}")
        except Exception as e:
            _LOGGER.exception("Exception while fetching MQTT config: %s", e)
            raise DayBetterError(f"Unexpected error: {e}")
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the API client is authenticated."""
        return self._auth_valid
    
    async def close(self):
        """Close the client session."""
        if self._session:
            await self._session.close()
            self._session = None
