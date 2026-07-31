"""Support for Ezviz Cloud cameras."""
from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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
    """Set up Ezviz Cloud camera entities based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: EzvizDataUpdateCoordinator = data["coordinator"]

    entities = []
    for serial, dev_info in coordinator.devices.items():
        entities.append(EzvizCloudCamera(coordinator, serial, dev_info))

    async_add_entities(entities)


class EzvizCloudCamera(CoordinatorEntity[EzvizDataUpdateCoordinator], Camera):
    """Representation of an Ezviz Cloud Camera entity."""

    def __init__(
        self,
        coordinator: EzvizDataUpdateCoordinator,
        device_serial: str,
        device_info: dict[str, Any],
    ) -> None:
        """Initialize Ezviz Camera."""
        super().__init__(coordinator)
        Camera.__init__(self)
        self._device_serial = device_serial
        self._device_name = device_info.get("deviceName", f"Ezviz {device_serial}")
        self._attr_unique_id = f"ezviz_camera_{device_serial}"
        self._attr_name = self._device_name
        self._last_image: Optional[bytes] = None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device registry information."""
        return {
            "identifiers": {(DOMAIN, self._device_serial)},
            "name": self._device_name,
            "manufacturer": "Ezviz (萤石)",
            "model": self.coordinator.devices.get(self._device_serial, {}).get("deviceType", "IPC"),
        }

    @property
    def is_on(self) -> bool:
        """Return true if camera is online."""
        dev = self.coordinator.devices.get(self._device_serial, {})
        return dev.get("status") == 1

    async def async_camera_image(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> Optional[bytes]:
        """Fetch real-time camera snapshot from Ezviz Cloud API."""
        session = async_get_clientsession(self.hass)
        pic_url = await self.coordinator.api.capture_snapshot(self._device_serial)

        if not pic_url:
            _LOGGER.debug("Snapshot not available for %s, using cached image", self._device_serial)
            return self._last_image

        try:
            async with session.get(pic_url, timeout=10) as resp:
                if resp.status == 200:
                    self._last_image = await resp.read()
                    return self._last_image
        except Exception as err:
            _LOGGER.debug("Error fetching camera image from %s: %s", pic_url, err)

        return self._last_image
