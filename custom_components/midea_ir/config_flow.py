import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.helpers import selector

from .const import DOMAIN


class MideaIrConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input["name"], data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="Midea AC"): str,
                    vol.Required("emitter"): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="infrared")
                    ),
                }
            ),
        )
