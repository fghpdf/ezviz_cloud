"""Support for Ezviz Cloud Sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import EzvizDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ezviz Cloud sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: EzvizDataUpdateCoordinator = data["coordinator"]

    async_add_entities([EzvizTodayAlarmCountSensor(coordinator, entry.entry_id)])


class EzvizTodayAlarmCountSensor(CoordinatorEntity[EzvizDataUpdateCoordinator], SensorEntity):
    """Sensor tracking today's total alarm count."""

    def __init__(
        self,
        coordinator: EzvizDataUpdateCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize Sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"ezviz_today_alarm_count_{entry_id}"
        self._attr_name = "萤石云 今日告警次数"
        self._attr_icon = "mdi:shield-alert-outline"
        self._attr_native_unit_of_measurement = "次"

    @property
    def native_value(self) -> int:
        """Return the total number of alarms today."""
        return len(self.coordinator.today_alarms)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return full list of today's alarms for dashboard rendering."""
        return {
            "alarms": self.coordinator.today_alarms,
            "device_count": len(self.coordinator.devices),
        }
