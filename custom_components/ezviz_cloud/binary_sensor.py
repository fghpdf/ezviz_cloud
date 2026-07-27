"""Support for Ezviz Cloud Binary Sensors."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up Ezviz Cloud binary sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: EzvizDataUpdateCoordinator = data["coordinator"]

    entities = []
    for serial, dev_info in coordinator.devices.items():
        entities.append(EzvizAlarmBinarySensor(coordinator, serial, dev_info))

    async_add_entities(entities)


class EzvizAlarmBinarySensor(CoordinatorEntity[EzvizDataUpdateCoordinator], BinarySensorEntity):
    """Binary Sensor for Ezviz Camera Alarms."""

    def __init__(
        self,
        coordinator: EzvizDataUpdateCoordinator,
        device_serial: str,
        device_info: dict[str, Any],
    ) -> None:
        """Initialize Binary Sensor."""
        super().__init__(coordinator)
        self._device_serial = device_serial
        self._device_name = device_info.get("deviceName", f"Ezviz {device_serial}")
        self._attr_unique_id = f"ezviz_binary_sensor_alarm_{device_serial}"
        self._attr_name = f"{self._device_name} 动态告警"
        self._attr_device_class = BinarySensorDeviceClass.MOTION
        self._last_alarm_time: Optional[datetime] = None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device registry info."""
        return {
            "identifiers": {(DOMAIN, self._device_serial)},
            "name": self._device_name,
            "manufacturer": "Ezviz (萤石)",
        }

    @property
    def is_on(self) -> bool:
        """Return True if an alarm occurred within recent 60 seconds."""
        for alarm in reversed(self.coordinator.today_alarms):
            if alarm.get("device_id") == self._device_serial:
                alarm_time_str = alarm.get("alarm_time")
                try:
                    alarm_dt = datetime.strptime(alarm_time_str, "%Y-%m-%d %H:%M:%S")
                    if datetime.now() - alarm_dt < timedelta(seconds=60):
                        return True
                except Exception:
                    pass
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes of latest alarm."""
        attrs = {}
        for alarm in reversed(self.coordinator.today_alarms):
            if alarm.get("device_id") == self._device_serial:
                attrs["last_alarm_type"] = alarm.get("alarm_type")
                attrs["last_alarm_time"] = alarm.get("alarm_time")
                attrs["last_image_url"] = alarm.get("image_url")
                attrs["last_local_image_path"] = alarm.get("relative_image_path")
                break
        return attrs
