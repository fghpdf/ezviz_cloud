"""The Ezviz Cloud integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EzvizAPIClient
from .coordinator import EzvizDataUpdateCoordinator
from .const import (
    CONF_APP_KEY,
    CONF_APP_SECRET,
    CONF_SCAN_INTERVAL,
    CONF_VERIFICATION_CODE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CAMERA,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ezviz Cloud from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    app_key = entry.data[CONF_APP_KEY]
    app_secret = entry.data[CONF_APP_SECRET]
    verification_code = entry.data.get(CONF_VERIFICATION_CODE) or entry.options.get(CONF_VERIFICATION_CODE)

    scan_interval_sec = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    session = async_get_clientsession(hass)
    api = EzvizAPIClient(
        session=session,
        app_key=app_key,
        app_secret=app_secret,
        verification_code=verification_code,
    )

    coordinator = EzvizDataUpdateCoordinator(
        hass=hass,
        api=api,
        update_interval=timedelta(seconds=scan_interval_sec),
    )

    # 首次刷新数据与设备列表
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 注册自定义服务
    await async_setup_services(hass)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
