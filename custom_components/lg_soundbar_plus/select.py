"""Multi-option settings exposed as selects (display brightness)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LGSoundbarConfigEntry
from .coordinator import LGSoundbarCoordinator
from .entity import LGSoundbarEntity
from .protocol import MSG_SETTING

# Front-panel display brightness (i_back_light). Confirmed by app capture: the
# field is 0 at rest ("Auto brightness") and the app cycled it to 1 then 2.
DISPLAY_BRIGHTNESS_KEY = "i_back_light"
DISPLAY_BRIGHTNESS_OPTIONS: dict[int, str] = {
    0: "auto_brightness",
    1: "auto_off",
    2: "always_on",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LGSoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create selects for the multi-option settings the bar reports."""
    coordinator = entry.runtime_data
    data = coordinator.data or {}
    if DISPLAY_BRIGHTNESS_KEY in data:
        async_add_entities([LGSoundbarDisplayBrightness(coordinator)])


class LGSoundbarDisplayBrightness(LGSoundbarEntity, SelectEntity):
    """Front-panel display brightness mode."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "display_brightness"
    _attr_options = list(DISPLAY_BRIGHTNESS_OPTIONS.values())

    def __init__(self, coordinator: LGSoundbarCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_id}_{DISPLAY_BRIGHTNESS_KEY}"

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data or {}
        value = data.get(DISPLAY_BRIGHTNESS_KEY)
        return DISPLAY_BRIGHTNESS_OPTIONS.get(value) if value is not None else None

    async def async_select_option(self, option: str) -> None:
        for value, name in DISPLAY_BRIGHTNESS_OPTIONS.items():
            if name == option:
                await self.coordinator.async_set_key(
                    MSG_SETTING, DISPLAY_BRIGHTNESS_KEY, value
                )
                return
