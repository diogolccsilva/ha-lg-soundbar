"""Coordinator that owns the soundbar connection and merged state."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .protocol import LGSoundbarClient

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

# How long to wait after requesting state for the bar's responses to arrive.
RESPONSE_GRACE = 1.5


class LGSoundbarCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Maintains one connection per soundbar and a merged field cache.

    The soundbar both answers ``get`` requests and *pushes* updates whenever
    something changes (app, remote, front panel), so state stays live between
    polls. The periodic poll is only a safety-net resync.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        host: str,
        name: str,
        unique_id: str,
    ) -> None:
        scan = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=timedelta(seconds=scan),
        )
        self.host = host
        self.device_name = name
        self.unique_id = unique_id
        self._client: LGSoundbarClient | None = None
        self._cache: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        if self._client is None:
            self._client = LGSoundbarClient(
                self.host,
                on_message=self._on_message_threadsafe,
                on_availability=self._on_availability_threadsafe,
            )
            # Give the background socket a moment to come up so the first poll
            # returns data instead of waiting a whole interval.
            for _ in range(20):
                if self._client.available:
                    break
                await asyncio.sleep(0.25)

        try:
            await self.hass.async_add_executor_job(self._client.request_all)
        except ConnectionError as err:
            raise UpdateFailed(f"Soundbar {self.host} unreachable: {err}") from err

        # Let the push callback merge the responses that come back.
        await asyncio.sleep(RESPONSE_GRACE)

        if not self._cache:
            raise UpdateFailed(f"No response from soundbar {self.host}")
        return dict(self._cache)

    # -- thread-safe bridges from the client's listener thread ---------------

    def _on_message_threadsafe(self, message: dict) -> None:
        self.hass.loop.call_soon_threadsafe(self._handle_message, message)

    def _on_availability_threadsafe(self, available: bool) -> None:
        self.hass.loop.call_soon_threadsafe(self._handle_availability, available)

    @callback
    def _handle_message(self, message: dict) -> None:
        data = message.get("data")
        if not isinstance(data, dict):
            return
        self._cache.update(data)
        self.async_set_updated_data(dict(self._cache))

    @callback
    def _handle_availability(self, available: bool) -> None:
        if not available:
            return
        # On (re)connect, ask for a fresh snapshot.
        if self._client is not None:
            self.hass.async_add_executor_job(self._client.request_all)

    # -- control -------------------------------------------------------------

    async def async_set_key(self, message: str, key: str, value: Any) -> None:
        """Write a single field and optimistically reflect it.

        The bar echoes the real value back via a push shortly after, so any
        device-side clamping/scaling self-corrects.
        """
        if self._client is None:
            raise UpdateFailed("Soundbar not connected")
        await self.hass.async_add_executor_job(self._client.set, message, {key: value})
        self._cache[key] = value
        self.async_set_updated_data(dict(self._cache))

    async def async_shutdown(self) -> None:
        await super().async_shutdown()
        if self._client is not None:
            await self.hass.async_add_executor_job(self._client.close)
            self._client = None
