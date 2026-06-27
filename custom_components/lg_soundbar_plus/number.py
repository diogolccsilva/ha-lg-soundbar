"""Per-channel speaker level and EQ tone controls."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import LGSoundbarConfigEntry
from .coordinator import LGSoundbarCoordinator
from .entity import LGSoundbarEntity
from .protocol import MSG_EQ, MSG_SETTING

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class LevelSpec:
    """Describes one numeric control backed by a soundbar field."""

    key: str  # e.g. "i_woofer_level"
    translation_key: str  # entity translation key
    message: str  # which view-info message the field lives in
    fallback_min: float = -6
    fallback_max: float = 6

    @property
    def base(self) -> str:
        """Field prefix used for the _min/_max bound keys."""
        return self.key[:-6] if self.key.endswith("_level") else self.key


# Speaker channel levels (SETTING_VIEW_INFO). Bounds are read live from the bar.
LEVEL_SPECS: tuple[LevelSpec, ...] = (
    LevelSpec(
        key="i_woofer_level", translation_key="woofer_level", message=MSG_SETTING
    ),
    LevelSpec(
        key="i_center_level", translation_key="center_level", message=MSG_SETTING
    ),
    LevelSpec(key="i_side_level", translation_key="side_level", message=MSG_SETTING),
    LevelSpec(key="i_top_level", translation_key="top_level", message=MSG_SETTING),
    LevelSpec(key="i_rear_level", translation_key="rear_level", message=MSG_SETTING),
    LevelSpec(
        key="i_rear_side_level",
        translation_key="rear_side_level",
        message=MSG_SETTING,
    ),
    LevelSpec(
        key="i_rear_top_level",
        translation_key="rear_top_level",
        message=MSG_SETTING,
    ),
    LevelSpec(
        key="i_dialog_level", translation_key="dialog_level", message=MSG_SETTING
    ),
)

# EQ tone (EQ_VIEW_INFO).
TONE_SPECS: tuple[LevelSpec, ...] = (
    LevelSpec(key="i_bass", translation_key="bass", message=MSG_EQ),
    LevelSpec(key="i_middle", translation_key="middle", message=MSG_EQ),
    LevelSpec(key="i_treble", translation_key="treble", message=MSG_EQ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LGSoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create a control for each level/tone field the bar actually reports."""
    coordinator = entry.runtime_data
    data = coordinator.data or {}
    entities = [
        LGSoundbarLevel(coordinator, spec)
        for spec in (*LEVEL_SPECS, *TONE_SPECS)
        if spec.key in data
    ]
    async_add_entities(entities)


class LGSoundbarLevel(LGSoundbarEntity, NumberEntity):
    """A single adjustable level/tone value, bounded by the bar's own limits."""

    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: LGSoundbarCoordinator, spec: LevelSpec) -> None:
        super().__init__(coordinator)
        self._spec = spec
        self._attr_translation_key = spec.translation_key
        self._attr_unique_id = f"{coordinator.unique_id}_{spec.key}"

    @property
    def native_min_value(self) -> float:
        data = self.coordinator.data or {}
        return float(data.get(f"{self._spec.base}_min", self._spec.fallback_min))

    @property
    def native_max_value(self) -> float:
        data = self.coordinator.data or {}
        return float(data.get(f"{self._spec.base}_max", self._spec.fallback_max))

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        raw = data.get(self._spec.key)
        if raw is None:
            return None
        # Woofer/bass have been observed to report values outside their stated
        # min/max (a different scale); clamp so the slider stays valid and log
        # the raw value so the mapping can be confirmed against hardware.
        low, high = self.native_min_value, self.native_max_value
        value = max(low, min(high, float(raw)))
        if value != float(raw):
            _LOGGER.debug(
                "%s reported %s (outside %s..%s); clamped to %s",
                self._spec.key,
                raw,
                low,
                high,
                value,
            )
        return value

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_key(
            self._spec.message, self._spec.key, int(value)
        )
