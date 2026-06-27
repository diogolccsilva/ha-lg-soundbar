"""The LG Soundbar Plus integration (local control over TCP 9741)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_HOST, DEFAULT_NAME
from .coordinator import LGSoundbarCoordinator

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SWITCH,
]

type LGSoundbarConfigEntry = ConfigEntry[LGSoundbarCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: LGSoundbarConfigEntry) -> bool:
    """Set up a soundbar from a config entry."""
    host: str = entry.data[CONF_HOST]
    name: str = entry.data.get(CONF_NAME, DEFAULT_NAME)
    unique_id = entry.unique_id or host

    coordinator = LGSoundbarCoordinator(hass, entry, host, name, unique_id)

    # Populate the cache (levels, bounds, sources) before creating entities so
    # they come up with correct ranges; tolerate a momentarily-busy bar.
    await coordinator.async_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LGSoundbarConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_shutdown()
    return unloaded


async def _async_reload_entry(
    hass: HomeAssistant, entry: LGSoundbarConfigEntry
) -> None:
    """Reload when options (e.g. scan interval) change."""
    await hass.config_entries.async_reload(entry.entry_id)
