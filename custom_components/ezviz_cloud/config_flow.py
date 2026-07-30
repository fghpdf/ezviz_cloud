"""Config flow for Ezviz Cloud integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import EzvizAPIClient, EzvizAuthError, EzvizAPIError
from .const import (
    CONF_APP_KEY,
    CONF_APP_SECRET,
    CONF_SCAN_INTERVAL,
    CONF_VERIFICATION_CODE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class EzvizCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ezviz Cloud."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        """Handle the initial user setup step."""
        errors: Dict[str, str] = {}
        error_detail: str = ""

        if user_input is not None:
            app_key = user_input[CONF_APP_KEY].strip()
            app_secret = user_input[CONF_APP_SECRET].strip()
            verification_code = user_input.get(CONF_VERIFICATION_CODE, "").strip() or None
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            await self.async_set_unique_id(app_key)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = EzvizAPIClient(
                session=session,
                app_key=app_key,
                app_secret=app_secret,
                verification_code=verification_code,
            )

            try:
                valid = await client.validate_credentials()
                if valid:
                    return self.async_create_entry(
                        title=f"萤石云 ({app_key[:6]}...)",
                        data={
                            CONF_APP_KEY: app_key,
                            CONF_APP_SECRET: app_secret,
                            CONF_VERIFICATION_CODE: verification_code,
                            CONF_SCAN_INTERVAL: scan_interval,
                        },
                    )
                else:
                    errors["base"] = "invalid_auth"
                    error_detail = "凭据无法签发 Token"
            except EzvizAuthError as err:
                _LOGGER.error("Ezviz Authentication failed: %s", err)
                errors["base"] = "invalid_auth"
                error_detail = str(err)
            except EzvizAPIError as err:
                _LOGGER.error("Ezviz API connection failed: %s", err)
                errors["base"] = "cannot_connect"
                error_detail = str(err)
            except Exception as err:
                _LOGGER.exception("Unexpected error in config flow: %s", err)
                errors["base"] = "unknown"
                error_detail = str(err)

        schema = vol.Schema(
            {
                vol.Required(CONF_APP_KEY): str,
                vol.Required(CONF_APP_SECRET): str,
                vol.Optional(CONF_VERIFICATION_CODE): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    cv.positive_int, vol.Range(min=5, max=300)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"error_detail": error_detail},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return EzvizCloudOptionsFlowHandler(config_entry)


class EzvizCloudOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Ezviz Cloud."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        current_vcode = self.config_entry.options.get(
            CONF_VERIFICATION_CODE,
            self.config_entry.data.get(CONF_VERIFICATION_CODE, ""),
        )

        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    cv.positive_int, vol.Range(min=5, max=300)
                ),
                vol.Optional(CONF_VERIFICATION_CODE, default=current_vcode or ""): str,
            }
        )

        return self.show_form(step_id="init", data_schema=schema)
