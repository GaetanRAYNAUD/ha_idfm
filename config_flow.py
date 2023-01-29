import logging
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_START, CONF_API_KEY, CONF_NAME, CONF_MISSION, CONF_LINE, call_api

_LOGGER = logging.getLogger(DOMAIN)


def get_schema(user_input: dict[str, Any] | None = None) -> voluptuous.Schema:
    return voluptuous.Schema(
        {
            voluptuous.Required(CONF_NAME, default=user_input.get(CONF_NAME, "")): cv.string,
            voluptuous.Required(CONF_API_KEY, default=user_input.get(CONF_API_KEY, "")): cv.string,
            voluptuous.Required(CONF_START, default=user_input.get(CONF_START, "")): cv.string,
            voluptuous.Optional(CONF_MISSION): cv.string,
            voluptuous.Optional(CONF_LINE): cv.string
        }
    )


class IDFMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors = {}

        if user_input is None:
            return self.show_setup_form(user_input, errors)

        name: str = user_input[CONF_NAME].strip()
        start: str = user_input[CONF_START].strip()
        api_key: str = user_input[CONF_API_KEY].strip()
        mission: str = user_input.get(CONF_MISSION)
        line: str = user_input.get(CONF_LINE)
        missions: [str] = None

        if mission is not None:
            missions = mission.split(',')

            for e in range(len(missions)):
                missions[e] = missions[e].strip()

        if line is not None:
            line = line.strip()

        response = await self.hass.async_add_executor_job(call_api, api_key, start)

        if response.status_code == 401:
            errors[CONF_API_KEY] = "unauthorized"
            return self.show_setup_form(user_input, errors)

        if response.status_code != 200:
            errors[CONF_NAME] = "unknown"
            return self.show_setup_form(user_input, errors)

        return self.async_create_entry(
            title=name,
            data={CONF_NAME: name, CONF_START: start, CONF_MISSION: missions, CONF_LINE: line, CONF_API_KEY: api_key},
        )

    @callback
    def show_setup_form(self, user_input: dict[str, Any] | None = None, errors: dict[str, Any] | None = None):
        if user_input is None:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=get_schema(user_input),
            errors=errors or {},
        )

    async def async_step_import(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_user(user_input)
