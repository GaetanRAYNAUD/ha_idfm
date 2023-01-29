import logging

import homeassistant.helpers.config_validation as cv
import voluptuous
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_START, CONF_API_KEY, CONF_NAME, CONF_MISSION, CONF_LINE

_LOGGER = logging.getLogger(DOMAIN)


class IDFMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is None:
            return self._show_setup_form(user_input, errors)

        name = user_input[CONF_NAME].strip()
        start = user_input[CONF_START].strip()
        api_key = user_input[CONF_API_KEY].strip()
        mission = user_input.get(CONF_MISSION)
        line = user_input.get(CONF_LINE)

        if mission is not None:
            mission = mission.split(',')

            for e in range(len(mission)):
                mission[e] = mission[e].strip()

        if line is not None:
            line = line.strip()

        # Todo add check api_key + start

        return self.async_create_entry(
            title=name,
            data={CONF_NAME: name, CONF_START: start, CONF_MISSION: mission, CONF_LINE: line, CONF_API_KEY: api_key},
        )

    @callback
    def _show_setup_form(self, user_input=None, errors=None):
        if user_input is None:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=voluptuous.Schema(
                {
                    voluptuous.Required(CONF_NAME, default=user_input.get(CONF_NAME, "")): cv.string,
                    voluptuous.Required(CONF_API_KEY, default=user_input.get(CONF_API_KEY, "")): cv.string,
                    voluptuous.Required(CONF_START, default=user_input.get(CONF_START, "")): cv.string,
                    voluptuous.Optional(CONF_MISSION): cv.string,
                    voluptuous.Optional(CONF_LINE): cv.string
                }
            ),
            errors=errors or {},
        )

    async def async_step_import(self, user_input):
        return await self.async_step_user(user_input)
