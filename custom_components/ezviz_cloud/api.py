"""API client for Ezviz Open Platform (open.ys7.com)."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
import os
from typing import Any, Dict, List, Optional
import aiohttp

from .const import (
    ALARM_LIST_URL,
    CAPTURE_URL,
    DEVICE_LIST_URL,
    TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
}


class EzvizAPIError(Exception):
    """General Ezviz API Exception."""


class EzvizAuthError(EzvizAPIError):
    """Authentication Exception."""


class EzvizAPIClient:
    """Ezviz Open API Client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        app_key: str,
        app_secret: str,
        verification_code: Optional[str] = None,
    ) -> None:
        """Initialize Ezviz API client."""
        self._session = session
        self.app_key = app_key
        self.app_secret = app_secret
        self.verification_code = verification_code
        self._access_token: Optional[str] = None
        self._token_expire_time: Optional[datetime] = None

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """Get or refresh valid AccessToken from open.ys7.com."""
        now = datetime.now()
        if (
            not force_refresh
            and self._access_token
            and self._token_expire_time
            and now < self._token_expire_time - timedelta(minutes=10)
        ):
            return self._access_token

        data = {
            "appKey": self.app_key,
            "appSecret": self.app_secret,
        }

        try:
            _LOGGER.debug("Requesting Ezviz Token for AppKey: %s", self.app_key)
            async with self._session.post(TOKEN_URL, data=data, headers=DEFAULT_HEADERS, timeout=15) as resp:
                try:
                    result = await resp.json()
                except Exception:
                    text = await resp.text()
                    _LOGGER.error("Ezviz non-JSON response (HTTP %s): %s", resp.status, text[:200])
                    raise EzvizAPIError(f"HTTP {resp.status} 响应异常")

                _LOGGER.info("Ezviz get_token response: %s", result)

                code = str(result.get("code", ""))
                msg = result.get("msg", "未知错误")

                if code == "200" and "data" in result:
                    token_data = result["data"]
                    self._access_token = token_data.get("accessToken")
                    expire_ms = token_data.get("expireTime", 0)
                    if expire_ms:
                        self._token_expire_time = datetime.fromtimestamp(expire_ms / 1000.0)
                    else:
                        self._token_expire_time = now + timedelta(days=6)
                    _LOGGER.info("Ezviz AccessToken updated successfully.")
                    return self._access_token
                elif code in ("10001", "10002", "10005", "10014"):
                    _LOGGER.error("Ezviz Auth error (%s): %s", code, msg)
                    raise EzvizAuthError(f"{msg} ({code})")
                else:
                    _LOGGER.error("Ezviz API error (%s): %s", code, msg)
                    raise EzvizAPIError(f"{msg} ({code})")
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error when requesting Ezviz token: %s", err)
            raise EzvizAPIError(f"网络超时或无法连接: {err}") from err

    async def validate_credentials(self) -> bool:
        """Validate credentials by requesting token."""
        token = await self.get_access_token(force_refresh=True)
        return bool(token)

    async def get_device_list(self, page_start: int = 0, page_size: int = 50) -> List[Dict[str, Any]]:
        """Fetch bound devices list."""
        token = await self.get_access_token()
        data = {
            "accessToken": token,
            "pageStart": page_start,
            "pageSize": page_size,
        }

        try:
            async with self._session.post(DEVICE_LIST_URL, data=data, headers=DEFAULT_HEADERS, timeout=15) as resp:
                result = await resp.json()
                code = str(result.get("code"))
                if code == "200":
                    return result.get("data", [])
                elif code in ("10002", "10003"):
                    token = await self.get_access_token(force_refresh=True)
                    data["accessToken"] = token
                    async with self._session.post(DEVICE_LIST_URL, data=data, headers=DEFAULT_HEADERS, timeout=15) as retry_resp:
                        retry_res = await retry_resp.json()
                        return retry_res.get("data", [])
                else:
                    _LOGGER.warning("Get device list failed: %s", result.get("msg"))
                    return []
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error fetching device list: %s", err)
            return []

    async def capture_snapshot(self, device_serial: str, channel_no: int = 1) -> Optional[str]:
        """Request device snapshot capture and return image URL."""
        token = await self.get_access_token()
        data = {
            "accessToken": token,
            "deviceSerial": device_serial,
            "channelNo": channel_no,
        }

        try:
            async with self._session.post(CAPTURE_URL, data=data, headers=DEFAULT_HEADERS, timeout=15) as resp:
                result = await resp.json()
                code = str(result.get("code"))
                if code == "200" and "data" in result:
                    pic_url = result["data"].get("picUrl")
                    return pic_url
                else:
                    _LOGGER.warning(
                        "Capture snapshot failed for %s: %s (code: %s)",
                        device_serial,
                        result.get("msg"),
                        code,
                    )
                    return None
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error capturing snapshot: %s", err)
            return None

    async def get_alarm_list(
        self,
        device_serial: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page_start: int = 0,
        page_size: int = 30,
    ) -> List[Dict[str, Any]]:
        """Fetch alarm list for devices."""
        token = await self.get_access_token()
        data: Dict[str, Any] = {
            "accessToken": token,
            "pageStart": page_start,
            "pageSize": page_size,
        }
        if device_serial:
            data["deviceSerial"] = device_serial

        if start_time:
            data["startTime"] = start_time.strftime("%Y-%m-%d %H:%M:%S")
        if end_time:
            data["endTime"] = end_time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            async with self._session.post(ALARM_LIST_URL, data=data, headers=DEFAULT_HEADERS, timeout=15) as resp:
                result = await resp.json()
                code = str(result.get("code"))
                if code == "200":
                    return result.get("data", [])
                elif code in ("10002", "10003"):
                    token = await self.get_access_token(force_refresh=True)
                    data["accessToken"] = token
                    async with self._session.post(ALARM_LIST_URL, data=data, headers=DEFAULT_HEADERS, timeout=15) as retry_resp:
                        retry_res = await retry_resp.json()
                        return retry_res.get("data", [])
                else:
                    _LOGGER.warning("Fetch alarm list error: %s (code: %s)", result.get("msg"), code)
                    return []
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error fetching alarm list: %s", err)
            return []

    async def download_alarm_image(
        self,
        pic_url: str,
        save_dir: str,
        filename: str,
    ) -> Optional[str]:
        """Download alarm picture to local directory (e.g. /config/www/ezviz_alarms/)."""
        if not pic_url:
            return None

        try:
            os.makedirs(save_dir, exist_ok=True)
            target_path = os.path.join(save_dir, filename)

            async with self._session.get(pic_url, headers=DEFAULT_HEADERS, timeout=20) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self._write_file, target_path, content)
                    _LOGGER.info("Saved alarm image to %s", target_path)
                    return target_path
                else:
                    _LOGGER.warning("Failed to download image from %s (HTTP %s)", pic_url, resp.status)
                    return None
        except Exception as err:
            _LOGGER.error("Error downloading alarm image: %s", err)
            return None

    @staticmethod
    def _write_file(path: str, data: bytes) -> None:
        """Helper to write bytes to disk."""
        with open(path, "wb") as f:
            f.write(data)
