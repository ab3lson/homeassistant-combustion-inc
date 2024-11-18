from __future__ import annotations
from enum import Enum
import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries, core
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_TIMEOUT, TempUnit

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema({vol.Required("unit_type", default=TempUnit.CELSIUS): vol.In(TempUnit)})

class CombustionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    data: Optional[Dict[str, Any]]
    async def async_step_user(self, user_input: dict[str, Any] | None = None):

        errors: Dict[str,str] = {}
        if user_input is not None:
            self.data = user_input
            return self.async_create_entry(title="Combustion Inc", data=self.data)

        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA, errors=errors,)
    