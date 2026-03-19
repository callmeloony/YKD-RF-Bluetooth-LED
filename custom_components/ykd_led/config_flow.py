import voluptuous as vol
import re
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_NAME

# Регулярний вираз для перевірки MAC-адреси (XX:XX:XX:XX:XX:XX)
MAC_REGEX = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"

class YKDLEDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Обробка процесу налаштування для YKD-RF LED."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Перший крок при додаванні інтеграції через UI."""
        errors = {}

        if user_input is not None:
            # Валідація MAC-адреси
            if not re.match(MAC_REGEX, user_input["address"]):
                errors["address"] = "invalid_mac"
            else:
                # Перевіряємо, чи цей пристрій вже доданий
                await self.async_set_unique_id(user_input["address"].lower())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input.get("name", DEFAULT_NAME),
                    data=user_input
                )

        # Схема форми
        data_schema = vol.Schema({
            vol.Required("name", default=DEFAULT_NAME): str,
            vol.Required("address"): str,
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Якщо захочете додати можливість змінювати налаштування пізніше."""
        return YKDLEDOptionsFlowHandler(config_entry)


class YKDLEDOptionsFlowHandler(config_entries.OptionsFlow):
    """Клас для редагування налаштувань вже створеного пристрою."""
    
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "name", 
                    default=self.config_entry.data.get("name")
                ): str,
            })
        )