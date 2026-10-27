"""Config flow: ask for gateway IP."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_HOST, DOMAIN
from .coordinator import async_fetch_livedata


class GatewayConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()
            try:
                data = await async_fetch_livedata(self.hass, host)
                if "common_list" not in data:
                    errors["base"] = "invalid_response"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_response"
            if not errors:
                return self.async_create_entry(
                    title=f"Weather Gateway {host}", data={CONF_HOST: host}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, ""),
                    ): str
                }
            ),
            errors=errors,
        )
