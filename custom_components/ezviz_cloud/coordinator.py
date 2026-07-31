"""DataUpdateCoordinator for Ezviz Cloud integration."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
import os
from typing import Any, Dict, List, Set
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EzvizAPIClient
from .const import ALARM_TYPES, DOMAIN, EVENT_EZVIZ_ALARM

_LOGGER = logging.getLogger(__name__)


class EzvizDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching Ezviz data and checking for alarm events."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: EzvizAPIClient,
        update_interval: timedelta,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.api = api
        self.processed_alarm_ids: Set[str] = set()
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.today_alarms: List[Dict[str, Any]] = []
        self._last_date_str: str = datetime.now().strftime("%Y-%m-%d")

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Ezviz API."""
        try:
            # 日期变动时自动重置当日告警缓存
            current_date_str = datetime.now().strftime("%Y-%m-%d")
            if current_date_str != self._last_date_str:
                self._last_date_str = current_date_str
                self.today_alarms.clear()

            # 1. 更新设备列表
            device_list = await self.api.get_device_list()
            devices_dict = {}
            for dev in device_list:
                serial = dev.get("deviceSerial")
                if serial:
                    devices_dict[serial] = dev

            self.devices = devices_dict

            # 2. 查询最近 10 分钟内的报警记录（防止漏掉）
            now = datetime.now()
            start_time = now - timedelta(minutes=10)
            alarm_list = await self.api.get_alarm_list(start_time=start_time, end_time=now)

            # 按时间从小到大处理
            alarm_list.sort(key=lambda x: x.get("alarmStartTime", 0))

            new_alarms = []
            for alarm in alarm_list:
                alarm_id = str(alarm.get("alarmId"))
                if not alarm_id or alarm_id in self.processed_alarm_ids:
                    continue

                self.processed_alarm_ids.add(alarm_id)
                # 防止集合无限增长，维持最近 1000 条
                if len(self.processed_alarm_ids) > 1000:
                    self.processed_alarm_ids = set(list(self.processed_alarm_ids)[-500:])

                device_serial = alarm.get("deviceSerial", "")
                dev_info = self.devices.get(device_serial, {})
                device_name = dev_info.get("deviceName", device_serial)
                alarm_type_code = alarm.get("alarmType", 10000)
                alarm_type_name = ALARM_TYPES.get(alarm_type_code, alarm.get("alarmName", "移动事件报警"))

                raw_time = alarm.get("alarmStartTime")
                if isinstance(raw_time, (int, float)):
                    alarm_time_str = datetime.fromtimestamp(raw_time / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
                    file_time_str = datetime.fromtimestamp(raw_time / 1000.0).strftime("%Y%m%d_%H%M%S")
                else:
                    alarm_time_str = str(raw_time or now.strftime("%Y-%m-%d %H:%M:%S"))
                    file_time_str = now.strftime("%Y%m%d_%H%M%S")

                pic_url = alarm.get("alarmPicUrl", "")
                local_image_path = None
                relative_image_path = None

                # 保存并自动解密告警截图到 HA 的 www 目录中
                if pic_url:
                    save_dir = self.hass.config.path("www", "ezviz_alarms")
                    filename = f"{file_time_str}_{device_serial}.jpg"
                    local_image_path = await self.api.download_alarm_image(
                        pic_url, save_dir, filename, device_serial=device_serial
                    )
                    if local_image_path:
                        relative_image_path = f"/local/ezviz_alarms/{filename}"

                alarm_event_payload = {
                    "alarm_id": alarm_id,
                    "device_id": device_serial,
                    "device_name": device_name,
                    "alarm_type": alarm_type_name,
                    "alarm_code": alarm_type_code,
                    "alarm_time": alarm_time_str,
                    "image_url": pic_url,
                    "local_image_path": local_image_path,
                    "relative_image_path": relative_image_path,
                }

                self.today_alarms.append(alarm_event_payload)
                new_alarms.append(alarm_event_payload)

                # 激发 Home Assistant 原生 Event !
                _LOGGER.info("Firing ezviz_cloud_alarm event: %s - %s", device_name, alarm_type_name)
                self.hass.bus.async_fire(EVENT_EZVIZ_ALARM, alarm_event_payload)

            return {
                "devices": self.devices,
                "today_alarms": self.today_alarms,
                "latest_new_alarms": new_alarms,
            }

        except Exception as err:
            _LOGGER.exception("Error fetching data from Ezviz API: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}") from err
