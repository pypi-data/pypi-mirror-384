"""HTTP connection of Epson projector module."""
import logging

import aiohttp
import asyncio

from .const import (
    ACCEPT_ENCODING,
    ACCEPT_HEADER,
    BUSY,
    EPSON_KEY_COMMANDS,
    DIRECT_SEND,
    HTTP_OK,
    STATE_UNAVAILABLE,
    POWER,
    EPSON_CODES,
    TCP_SERIAL_PORT,
    SERIAL_BYTE,
    JSON_QUERY,
)
from .error import ProjectorUnavailableError
from .timeout import get_timeout
from .base_connection import BaseProjectorConnection

_LOGGER = logging.getLogger(__name__)


class ProjectorHttp(BaseProjectorConnection):
    """
    Epson projector class.

    Control your projector with Python.
    """

    def __init__(self, host, websession, port=80):
        """
        Epson Projector controller.

        :param str host:        IP address or hostname of Projector
        :param obj websession:  AioHttpWebsession for HTTP protocol
        :param int port:        Port to connect to. Default 80.
        """
        self._host = host
        self._http_url = f"http://{self._host}:{port}/cgi-bin/"
        self._headers = {
            "Accept-Encoding": ACCEPT_ENCODING,
            "Accept": ACCEPT_HEADER,
            "Referer": f"http://{self._host}:{port}/cgi-bin/webconf",
        }
        self._serial = None
        self.websession = websession

    def close(self):
        return

    async def get_property(self, command, timeout):
        """Get property state from device."""
        response = await self.send_request(
            timeout=timeout, params=EPSON_KEY_COMMANDS[command], type=JSON_QUERY
        )
        if not response:
            return False
        try:
            if response == STATE_UNAVAILABLE:
                return STATE_UNAVAILABLE
            return response["projector"]["feature"]["reply"]
        except KeyError:
            return BUSY

    async def send_command(self, command, timeout):
        """Send command to Epson."""
        response = await self.send_request(
            timeout=timeout, params=EPSON_KEY_COMMANDS[command], type=DIRECT_SEND
        )
        return response

    async def send_request(self, params, timeout, type=JSON_QUERY):
        """Send request to Epson."""
        try:
            async with asyncio.timeout(timeout):
                url = "{url}{type}".format(url=self._http_url, type=type)
                async with self.websession.get(
                    url=url, params=params, headers=self._headers
                ) as response:
                    if response.status != HTTP_OK:
                        _LOGGER.warning("Error message %d from Epson.", response.status)
                        return False
                    if type == JSON_QUERY:
                        return await response.json()
                    return response
        except (
            aiohttp.ClientError,
            aiohttp.ClientConnectionError,
            TimeoutError,
            asyncio.exceptions.TimeoutError,
        ):
            raise ProjectorUnavailableError(STATE_UNAVAILABLE)

    async def get_serial_number(self):
        """Send TCP request for serial number to Epson."""
        if not self._serial:
            try:
                async with asyncio.timeout(10):
                    power_on = await self.get_property(POWER, get_timeout(POWER))
                    if power_on == EPSON_CODES[POWER]:
                        reader, writer = await asyncio.open_connection(
                            host=self._host,
                            port=TCP_SERIAL_PORT,
                        )
                        _LOGGER.debug("Asking for serial number.")
                        writer.write(SERIAL_BYTE)
                        response = await reader.read(32)
                        self._serial = response[24:].decode()
                        writer.close()
                    else:
                        _LOGGER.error("Is projector turned on?")
            except asyncio.TimeoutError:
                _LOGGER.error(
                    "Timeout error receiving SERIAL of projector. Is projector turned on?"
                )
        return self._serial
