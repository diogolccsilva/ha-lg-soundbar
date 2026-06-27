"""Media player entity: volume, mute, source and sound mode."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LGSoundbarConfigEntry
from .coordinator import LGSoundbarCoordinator
from .entity import LGSoundbarEntity
from .protocol import MSG_EQ, MSG_FUNC, MSG_SPK

# Index -> name maps from the protocol. Unknown (newer) indices fall back to a
# stable generic label so selection still round-trips.
FUNCTIONS = [
    "Wi-Fi",
    "Bluetooth",
    "Portable",
    "Aux",
    "Optical",
    "CP",
    "HDMI",
    "ARC",
    "Spotify",
    "Optical 2",
    "HDMI 2",
    "HDMI 3",
    "LG TV",
    "Mic",
    "Chromecast",
    "Optical/HDMI ARC",
    "LG Optical",
    "FM",
    "USB",
    "USB 2",
]

EQUALISERS = [
    "Standard",
    "Bass",
    "Flat",
    "Boost",
    "Treble and Bass",
    "User",
    "Music",
    "Cinema",
    "Night",
    "News",
    "Voice",
    "ia_sound",
    "Adaptive Sound Control",
    "Movie",
    "Bass Blast",
    "Dolby Atmos",
    "DTS Virtual X",
    "Bass Boost Plus",
    "DTS X",
]


def _name(names: list[str], index: int, prefix: str) -> str:
    if 0 <= index < len(names):
        return names[index]
    return f"{prefix} {index}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LGSoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the soundbar media player."""
    async_add_entities([LGSoundbarMediaPlayer(entry.runtime_data)])


class LGSoundbarMediaPlayer(LGSoundbarEntity, MediaPlayerEntity):
    """The soundbar as a media player (the device's primary entity)."""

    _attr_name = None
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )

    def __init__(self, coordinator: LGSoundbarCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_id}_media_player"

    @property
    def _data(self) -> dict[str, Any]:
        return self.coordinator.data or {}

    @property
    def state(self) -> MediaPlayerState | None:
        if not self._data:
            return None
        return (
            MediaPlayerState.ON
            if self._data.get("b_powerstatus", True)
            else MediaPlayerState.OFF
        )

    # -- power ---------------------------------------------------------------
    # Power is driven via b_powerkey (b_powerstatus is read-only). Captured from
    # the app, b_powerkey is explicit, not a toggle: true powers on, false powers
    # off. The bar then reports the result via b_powerstatus.

    async def async_turn_on(self) -> None:
        await self.coordinator.async_set_key(MSG_SPK, "b_powerkey", True)

    async def async_turn_off(self) -> None:
        await self.coordinator.async_set_key(MSG_SPK, "b_powerkey", False)

    # -- volume --------------------------------------------------------------

    @property
    def volume_level(self) -> float | None:
        vol = self._data.get("i_vol")
        vol_max = self._data.get("i_vol_max") or 100
        return None if vol is None else vol / vol_max

    @property
    def is_volume_muted(self) -> bool | None:
        value = self._data.get("b_mute")
        return None if value is None else bool(value)

    async def async_set_volume_level(self, volume: float) -> None:
        vol_max = self._data.get("i_vol_max") or 100
        await self.coordinator.async_set_key(MSG_SPK, "i_vol", round(volume * vol_max))

    async def async_volume_up(self) -> None:
        await self._nudge_volume(1)

    async def async_volume_down(self) -> None:
        await self._nudge_volume(-1)

    async def _nudge_volume(self, delta: int) -> None:
        vol = self._data.get("i_vol")
        if vol is None:
            return
        vol_max = self._data.get("i_vol_max") or 100
        vol_min = self._data.get("i_vol_min") or 0
        await self.coordinator.async_set_key(
            MSG_SPK, "i_vol", max(vol_min, min(vol_max, vol + delta))
        )

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.async_set_key(MSG_SPK, "b_mute", mute)

    # -- source --------------------------------------------------------------

    @property
    def source_list(self) -> list[str]:
        return [
            _name(FUNCTIONS, idx, "Source")
            for idx in self._data.get("ai_func_list", [])
        ]

    @property
    def source(self) -> str | None:
        idx = self._data.get("i_curr_func")
        return None if idx is None else _name(FUNCTIONS, idx, "Source")

    async def async_select_source(self, source: str) -> None:
        for idx in self._data.get("ai_func_list", []):
            if _name(FUNCTIONS, idx, "Source") == source:
                await self.coordinator.async_set_key(MSG_FUNC, "i_curr_func", idx)
                return

    # -- sound mode (equaliser) ---------------------------------------------

    @property
    def sound_mode_list(self) -> list[str]:
        return [
            _name(EQUALISERS, idx, "Mode") for idx in self._data.get("ai_eq_list", [])
        ]

    @property
    def sound_mode(self) -> str | None:
        idx = self._data.get("i_curr_eq")
        return None if idx is None else _name(EQUALISERS, idx, "Mode")

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        for idx in self._data.get("ai_eq_list", []):
            if _name(EQUALISERS, idx, "Mode") == sound_mode:
                await self.coordinator.async_set_key(MSG_EQ, "i_curr_eq", idx)
                return
