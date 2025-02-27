import voluptuous as vol
from homeassistant import config_entries

from .assistant import assistant
from .utils import set_credentials, get_iot_info
import logging

_LOGGER = logging.getLogger(__name__)


class DNakeConfigFlow(config_entries.ConfigFlow, domain="dnake_home"):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input:
            return self.async_create_entry(title="Dnake Devices", data=user_input)
        else:
            default_values = {
                "gateway_ip": "192.168.1.2",
                "auth_username": "admin",
                "auth_password": "123456",
                "scan_interval": 30
            }
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("gateway_ip", default=default_values["gateway_ip"]): str,
                    vol.Required("auth_username", default=default_values["auth_username"]): str,
                    vol.Required("auth_password", default=default_values["auth_password"]): str,
                    vol.Optional("scan_interval", default=default_values["scan_interval"]): int,
                }),
                errors={},
            )
