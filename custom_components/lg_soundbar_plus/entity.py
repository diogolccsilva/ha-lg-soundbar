"""Shared base entity tying everything to one soundbar device."""

from __future__ import annotations

from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
    format_mac,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import LGSoundbarCoordinator


class LGSoundbarEntity(CoordinatorEntity[LGSoundbarCoordinator]):
    """Base entity; all entities share a single HA device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: LGSoundbarCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.data or {}
        connections = set()
        mac = data.get("s_dev_mac")
        if mac:
            connections.add((CONNECTION_NETWORK_MAC, format_mac(mac)))
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.unique_id)},
            connections=connections,
            name=self.coordinator.device_name,
            manufacturer=MANUFACTURER,
            model=data.get("s_model_name") or "Soundbar",
        )
