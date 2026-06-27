"""Sound-processing toggle switches (Neural:X, DRC, Night mode, ...)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LGSoundbarConfigEntry
from .coordinator import LGSoundbarCoordinator
from .entity import LGSoundbarEntity
from .protocol import MSG_SETTING


@dataclass(frozen=True, kw_only=True)
class ToggleSpec:
    key: str
    translation_key: str
    icon: str | None = None


# Note: the bar uses ``b_night_time`` (the upstream library's wrong
# ``b_night_mode`` key is deliberately avoided here).
TOGGLE_SPECS: tuple[ToggleSpec, ...] = (
    ToggleSpec(key="b_neuralx", translation_key="neuralx", icon="mdi:surround-sound"),
    ToggleSpec(key="b_drc", translation_key="drc", icon="mdi:arrow-collapse-vertical"),
    ToggleSpec(
        key="b_night_time", translation_key="night_mode", icon="mdi:weather-night"
    ),
    ToggleSpec(
        key="b_auto_vol", translation_key="auto_volume", icon="mdi:volume-equal"
    ),
    ToggleSpec(
        key="b_auto_power", translation_key="auto_power", icon="mdi:power-sleep"
    ),
    ToggleSpec(
        key="b_voice_feedback",
        translation_key="voice_feedback",
        icon="mdi:account-voice",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LGSoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create a switch for each toggle the bar reports."""
    coordinator = entry.runtime_data
    data = coordinator.data or {}
    async_add_entities(
        LGSoundbarToggle(coordinator, spec) for spec in TOGGLE_SPECS if spec.key in data
    )


class LGSoundbarToggle(LGSoundbarEntity, SwitchEntity):
    """A boolean sound-processing setting."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: LGSoundbarCoordinator, spec: ToggleSpec) -> None:
        super().__init__(coordinator)
        self._spec = spec
        self._attr_translation_key = spec.translation_key
        self._attr_icon = spec.icon
        self._attr_unique_id = f"{coordinator.unique_id}_{spec.key}"

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        value = data.get(self._spec.key)
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_key(MSG_SETTING, self._spec.key, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_key(MSG_SETTING, self._spec.key, False)
