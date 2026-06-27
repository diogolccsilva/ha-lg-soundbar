"""Config and options flow for LG Soundbar Plus."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .protocol import probe


class LGSoundbarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the soundbar's IP and verify it answers locally."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = str(user_input[CONF_HOST]).strip()
            try:
                info = await self.hass.async_add_executor_job(probe, host)
            except (ConnectionError, OSError):
                errors["base"] = "cannot_connect"
            else:
                uuid = info.get("s_uuid") or info.get("s_dev_mac") or host
                await self.async_set_unique_id(uuid)
                self._abort_if_unique_id_configured()
                name = (
                    user_input.get(CONF_NAME)
                    or info.get("s_model_name")
                    or (DEFAULT_NAME)
                )
                return self.async_create_entry(
                    title=name,
                    data={CONF_HOST: host, CONF_NAME: name},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return LGSoundbarOptionsFlow()


class LGSoundbarOptionsFlow(OptionsFlow):
    """Allow changing the safety-net poll interval after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
