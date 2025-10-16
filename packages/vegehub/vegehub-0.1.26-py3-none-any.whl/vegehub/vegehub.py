"""VegeHub API access library."""

import logging
from typing import Any
import aiohttp

_LOGGER = logging.getLogger(__name__)


class VegeHub():
    """Vegehub class will contain all properties and methods necessary for contacting the Hub."""

    def __init__(self,
                 ip_address: str,
                 mac_address: str = "",
                 unique_id: str = "",
                 info: dict[Any, Any] | None = None,
                 session: aiohttp.ClientSession | None = None) -> None:
        self._ip_address: str = ip_address
        self._mac_address: str = mac_address
        self._unique_id: str = unique_id
        self._info = info
        self.entities: dict[Any, Any] = {}
        self._session: aiohttp.ClientSession | None = session
        self._owns_session: bool = False

    @property
    def ip_address(self) -> str:
        """Property to retrieve IP address."""
        return self._ip_address

    @property
    def mac_address(self) -> str | None:
        """Property to retrieve MAC address."""
        return self._mac_address

    @property
    def unique_id(self) -> str | None:
        """Property to retrieve unique id."""
        return self._unique_id

    @property
    def url(self) -> str | None:
        """Property to retrieve a URL to reach this hub."""
        return f"http://{self._ip_address}"

    @property
    def info(self) -> dict | None:
        """Property to retrieve hub info."""
        return self._info

    @property
    def num_sensors(self) -> int | None:
        """The number of sensors channels on this hub."""
        if self._info:
            return int(self._info["num_channels"] or 0)
        return None

    @property
    def num_actuators(self) -> int | None:
        """The number of actuator channels on this hub."""
        if self._info:
            return int(self._info["num_actuators"] or 0)
        return None

    @property
    def sw_version(self) -> str | None:
        """Property to retrieve the version of the software running on this hub."""
        if self._info:
            return self._info["version"]
        return None

    @property
    def is_ac(self) -> bool | None:
        """Property to return whether or not this is an AC powered hub."""
        if self._info:
            return bool(self._info["is_ac"])
        return None

    async def request_update(self) -> bool:
        """Request an update of data from the Hub."""
        return await self._request_update()

    async def retrieve_mac_address(self, retries: int = 0) -> bool:
        """Start the process of retrieving the MAC address from the Hub."""
        ret = False
        while True:
            try:
                ret = await self._get_device_mac()
            except (ConnectionError, TimeoutError):
                if retries <= 0:
                    raise
                retries -= 1
                continue

            if ret:
                break

            if retries <= 0:
                break
            retries -= 1
        return ret

    async def set_actuator(self,
                           state: int,
                           slot: int,
                           duration: int,
                           retries: int = 0) -> bool:
        """Set the target actuator to the target state for the intended duration."""
        while True:
            try:
                await self._set_actuator(state, slot, duration)
            except (ConnectionError, TimeoutError):
                if retries <= 0:
                    raise
                retries -= 1
                continue

            break  # If we reach this point without an exception, it has succeeded
        return True

    async def actuator_states(self, retries: int = 0) -> list:
        """Grab the states of all actuators on the Hub and return a list of JSON data on them."""
        ret = []
        while True:
            try:
                ret = await self._get_actuator_info()
            except (ConnectionError, TimeoutError):
                if retries <= 0:
                    raise
                retries -= 1
                continue

            break  # If we reach this point without an exception, it has succeeded
        return ret

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a client session.
        
        Returns the session provided in __init__, or creates a new one if needed.
        """
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close the client session if we own it."""
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None
            self._owns_session = False

    async def setup(self,
                    api_key: str,
                    server_address: str,
                    retries: int = 0) -> bool:
        """Set the API key and target server on the Hub."""
        config_data = await self._get_device_config_with_retries(retries)

        # Modify the config with the new API key and server address
        modified_config = self._modify_device_config(config_data, api_key,
                                                     server_address)
        ret = await self._set_device_config_with_retries(
            modified_config, retries)

        if ret is not None:
            await self._get_device_info_with_retries(retries)

        return ret

    async def _get_device_info(self) -> dict | None:
        """Fetch the current configuration from the device."""
        url = f"http://{self._ip_address}/api/info/get"

        payload: dict[Any, Any] = {"hub": [], "wifi": []}
        session = await self._get_session()
        try:
            response = await session.post(url, json=payload)
            if response.status != 200:
                _LOGGER.error("Failed to get config from %s: HTTP %s", url,
                              response.status)
                raise ConnectionError

            # Parse the response JSON
            info_data = await response.json()
            if info_data:
                if "wifi" in info_data and not self._mac_address:
                    self._mac_address = (info_data.get(
                        "wifi", {}).get("mac_addr").replace(":", "").upper())
                if "hub" in info_data:
                    _LOGGER.info("Received info from %s", self._ip_address)
                    return info_data["hub"]
            return None
        except (aiohttp.ClientConnectorError, Exception) as err:
            _LOGGER.error("Connection error getting info from %s: %s", url,
                          err)
            raise ConnectionError from err

    async def _get_device_config(self) -> dict | None:
        """Fetch the current configuration from the device."""
        url = f"http://{self._ip_address}/api/config/get"

        # Request both old and new config formats
        # Old format: {"hub": [], "api_key": []}
        # New format: {"endpoints": []}
        payload: dict[Any, Any] = {"hub": [], "api_key": [], "endpoints": []}

        session = await self._get_session()
        try:
            response = await session.post(url, json=payload)
            if response.status != 200:
                _LOGGER.error("Failed to get config from %s: HTTP %s", url,
                              response.status)
                raise ConnectionError

            # Parse the response JSON
            return await response.json()
        except (aiohttp.ClientConnectorError, Exception) as err:
            _LOGGER.error("Connection error getting config from %s: %s", url,
                          err)
            raise ConnectionError from err

    def _modify_device_config(self, config_data: dict | None, new_key: str,
                              server_url: str) -> dict | None:
        """Modify the device config by adding or updating the API key."""
        error = False

        if config_data is None:
            return None

        # Check if the new endpoints format is present and valid
        # endpoints must be a list (can be empty) for new firmware
        # If endpoints is None or not present, it's old firmware
        if ("endpoints" in config_data and 
            isinstance(config_data.get("endpoints"), list)):
            # New format: create a new endpoint and add it to the array
            new_endpoint = {
                "id": len(config_data["endpoints"]) + 1,
                "name": "HomeAssistant",
                "type": "custom",
                "enabled": True,
                "connection_method": "wifi",
                "config": {
                    "api_key": new_key,
                    "data_format": "json",
                    "url": server_url
                }
            }
            config_data["endpoints"].append(new_endpoint)
            return config_data

        # Old format: fall back to the previous behavior for older VegeHubs
        # Assuming the API key should be added to the 'hub' section, modify as necessary
        if "api_key" in config_data:
            config_data["api_key"] = new_key
        else:
            error = True

        # Modify the server_url in the returned JSON
        if "hub" in config_data:
            config_data["hub"]["server_url"] = server_url
            config_data["hub"]["server_type"] = 3
        else:
            error = True

        if error:
            return None
        return config_data

    async def _set_device_config(self, config_data: dict | None) -> bool:
        """Send the modified configuration back to the device."""
        url = f"http://{self._ip_address}/api/config/set"

        if config_data is None:
            return False

        session = await self._get_session()
        try:
            response = await session.post(url, json=config_data)
            if response.status != 200:
                _LOGGER.error("Failed to set config at %s: HTTP %s", url,
                              response.status)
                raise ConnectionError
        except (aiohttp.ClientConnectorError, Exception) as err:
            _LOGGER.error("Connection error setting config on %s: %s", url,
                          err)
            raise ConnectionError from err
        return True

    async def _get_device_config_with_retries(self,
                                              retries: int = 0) -> dict | None:
        """Run the _get_device_config function, but retry on failures if retries > 0."""
        while True:
            try:
                # Fetch current config from the device
                config_data = await self._get_device_config()
            except (ConnectionError, TimeoutError):
                if retries <= 0:
                    raise
                retries -= 1
                continue

            if config_data:
                return config_data

            if retries <= 0:
                break
            retries -= 1
        return None

    async def _set_device_config_with_retries(self,
                                              modified_config,
                                              retries: int = 0) -> bool:
        """Run the _set_device_config function, but retry on failures if retries > 0."""
        ret = False
        while True:
            try:
                # Send the modified config back to the device
                ret = await self._set_device_config(modified_config)
            except (ConnectionError, TimeoutError):
                if retries <= 0:
                    raise
                retries -= 1
                continue

            if ret:
                return ret

            if retries <= 0:
                break
            retries -= 1
        return ret

    async def _get_device_info_with_retries(self, retries: int = 0) -> bool:
        """Run the _get_device_info function, but retry on failures if retries > 0."""
        while True:
            try:
                self._info = await self._get_device_info()
            except (ConnectionError, TimeoutError):
                if retries <= 0:
                    raise
                retries -= 1
                continue

            if self._info:
                return True

            if retries <= 0:
                break
            retries -= 1
        return False

    async def _request_update(self) -> bool:
        """Ask the device to send in a full update of data to Home Assistant."""
        url = f"http://{self._ip_address}/api/update/send"
        session = await self._get_session()
        try:
            response = await session.get(url)
            if response.status != 200:
                _LOGGER.error("Failed to ask for update from %s: HTTP %s", url,
                              response.status)
                raise ConnectionError
        except (aiohttp.ClientConnectorError, Exception) as err:
            _LOGGER.error(
                "Connection error while requesting update from %s: %s", url,
                err)
            raise ConnectionError from err

        return True

    async def _get_device_mac(self) -> bool:
        """Fetch the MAC address by sending a POST request to the device's /api/config_get."""
        url = f"http://{self._ip_address}/api/info/get"

        # Prepare the JSON payload for the POST request
        payload: dict[Any, Any] = {"wifi": []}
        session = await self._get_session()
        # Use aiohttp to send the POST request with the JSON body
        try:
            response = await session.post(url, json=payload)
            if response.status != 200:
                _LOGGER.error("Failed to get config from %s: HTTP %s", url,
                              response.status)
                raise ConnectionError
            # Parse the JSON response
            config_data = await response.json()
            mac_address = config_data.get("wifi", {}).get("mac_addr")
            if not mac_address:
                _LOGGER.error(
                    "MAC address not found in the config response from %s",
                    self._ip_address)
                return False
            _LOGGER.info("%s MAC address: %s", self._ip_address, mac_address)
            self._mac_address = mac_address.replace(":", "").upper()
        except (aiohttp.ClientConnectorError, Exception) as err:
            _LOGGER.error("Connection error getting mac address from %s: %s",
                          url, err)
            raise ConnectionError from err
        return True

    async def _set_actuator(self, state: int, slot: int,
                            duration: int) -> bool:
        url = f"http://{self._ip_address}/api/actuators/set"
        _LOGGER.info("Setting actuator %s on %s", slot, self._ip_address)

        # Prepare the JSON payload for the POST request
        payload = {
            "target": slot,
            "duration": duration,
            "state": state,
        }

        session = await self._get_session()
        # Use aiohttp to send the POST request with the JSON body
        try:
            response = await session.post(url, json=payload)
            if response.status != 200:
                _LOGGER.error(
                    "Failed to set actuator state on %s: HTTP %s",
                    url,
                    response.status,
                )
                raise ConnectionError
            return True
        except (aiohttp.ClientConnectorError, Exception) as err:
            _LOGGER.error("Connection error setting actuator on %s: %s", url,
                          err)
            raise ConnectionError from err

    async def _get_actuator_info(self) -> list:
        """Fetch the current status of the actuators."""
        url = f"http://{self._ip_address}/api/actuators/status"
        _LOGGER.info("Retrieving actuator status from %s", self._ip_address)
        session = await self._get_session()
        # Use aiohttp to send the POST request with the JSON body
        try:
            response = await session.get(url)
            if response.status != 200:
                _LOGGER.error("Failed to get status from %s: HTTP %s", url,
                              response.status)
                raise ConnectionError

            # Parse the JSON response
            config_data = await response.json()
            actuators = config_data.get("actuators", [])
            if not actuators:
                _LOGGER.error(
                    "Actuator information not found in response from %s",
                    self._ip_address)
                raise AttributeError
            return actuators
        except AttributeError:
            raise
        except (aiohttp.ClientConnectorError, Exception) as err:
            _LOGGER.error("Connection error getting actuator info from %s: %s",
                          url, err)
            raise ConnectionError from err
