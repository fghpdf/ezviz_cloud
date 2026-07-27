"""Services for Ezviz Cloud integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_GENERATE_DAILY_RECAP = "generate_daily_recap"

SERVICE_DAILY_RECAP_SCHEMA = vol.Schema(
    {
        vol.Optional("target_notify_service", default="notify"): cv.string,
        vol.Optional("title", default="📹 萤石摄像头每日回顾与概览"): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up Ezviz Cloud services."""

    async def handle_generate_daily_recap(call: ServiceCall) -> None:
        """Handle generating and sending daily recap report."""
        target_notify = call.data.get("target_notify_service", "notify")
        title = call.data.get("title", "📹 萤石摄像头每日回顾与概览")

        # 从 hass.data 中获取对应的 coordinator
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            _LOGGER.warning("No Ezviz Cloud integration entry found for daily recap.")
            return

        all_today_alarms = []
        all_devices = {}

        for entry in entries:
            data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
            if data and "coordinator" in data:
                coordinator = data["coordinator"]
                all_today_alarms.extend(coordinator.today_alarms)
                all_devices.update(coordinator.devices)

        date_str = datetime.now().strftime("%Y年%m月%d日")
        total_count = len(all_today_alarms)

        # 1. 统计各个设备的告警次数
        device_stats: Dict[str, int] = {}
        for alarm in all_today_alarms:
            dev_name = alarm.get("device_name", "未知摄像头")
            device_stats[dev_name] = device_stats.get(dev_name, 0) + 1

        stats_summary = []
        for dev, count in device_stats.items():
            stats_summary.append(f"• **{dev}**: {count} 次告警")

        stats_text = "\n".join(stats_summary) if stats_summary else "• 今日暂无异常告警"

        # 2. 选取最近或最新的告警精选
        recent_highlights = []
        latest_image_url = None
        for alarm in reversed(all_today_alarms[-5:]):
            dev = alarm.get("device_name")
            atype = alarm.get("alarm_type")
            atime = alarm.get("alarm_time", "")[11:16]  # 提取 HH:MM
            recent_highlights.append(f"• `[{atime}]` **{dev}** - {atype}")
            if not latest_image_url and alarm.get("relative_image_path"):
                latest_image_url = alarm.get("relative_image_path")

        highlights_text = "\n".join(recent_highlights) if recent_highlights else "• 今日无关键事件记录"

        # 3. 拼接 Markdown 报告
        message_body = (
            f"📅 **日期**: {date_str}\n"
            f"🔔 **全天告警总数**: {total_count} 次\n\n"
            f"📊 **设备统计**:\n{stats_text}\n\n"
            f"👀 **重点事件回顾**:\n{highlights_text}\n\n"
            f"✨ *由 萤石云 Home Assistant 集成自动生成*"
        )

        _LOGGER.info("Sending daily recap via service %s", target_notify)

        # 准备派发通知
        notify_domain, _, notify_service = target_notify.partition(".")
        if not notify_service:
            notify_service = notify_domain
            notify_domain = "notify"

        service_data: Dict[str, Any] = {
            "title": title,
            "message": message_body,
        }

        # 如果有相对路径快照，尝试添加 data 附带图片路径
        if latest_image_url:
            service_data["data"] = {
                "image": latest_image_url,
                "photo": [{"url": latest_image_url}],
            }

        try:
            await hass.services.async_call(
                notify_domain,
                notify_service,
                service_data,
                blocking=True,
            )
            _LOGGER.info("Daily recap report sent successfully.")
        except Exception as err:
            _LOGGER.error("Failed to call notification service %s: %s", target_notify, err)

    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE_DAILY_RECAP,
        handle_generate_daily_recap,
        schema=SERVICE_DAILY_RECAP_SCHEMA,
    )
