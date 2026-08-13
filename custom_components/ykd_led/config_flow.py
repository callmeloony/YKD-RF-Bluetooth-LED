import re
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, DEFAULT_NAME

MAC_REGEX = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"

def normalize_mac(mac: str) -> str:
    """Приводить MAC-адресу до стандартного вигляду AA:BB:CC:DD:EE:FF."""
    clean_mac = mac.replace("-", ":").upper()
    return clean_mac

class YKDLEDConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Обробка процесу налаштування для YKD-RF LED."""

    VERSION = 1

    def __init__(self):
        """Ініціалізація змінних потоку."""
        self._discovered_device = None

    async def async_step_user(self, user_input=None):
        """Перший крок при додаванні інтеграції через UI."""
        errors = {}

        if user_input is not None:
            raw_address = user_input["address"]
            
            # Перевірка валідності
            if not re.match(MAC_REGEX, raw_address):
                errors["address"] = "invalid_mac"
            else:
                formatted_address = normalize_mac(raw_address)
                
                # Перевіряємо, чи цей пристрій вже доданий
                await self.async_set_unique_id(formatted_address.lower())
                self._abort_if_unique_id_configured()

                # Зберігаємо вже нормалізовану адресу
                user_input["address"] = formatted_address

                return self.async_create_entry(
                    title=user_input.get("name", DEFAULT_NAME),
                    data=user_input
                )

        # Скануємо Bluetooth-пристрої поблизу для випадаючого списку
        current_addresses = self._async_current_ids()
        discovered_devices = bluetooth.async_discovered_service_info(self.hass)
        
        # Формуємо список пристроїв для вибору
        device_options = {}
        for service_info in discovered_devices:
            formatted_mac = normalize_mac(service_info.address)
            if formatted_mac.lower() not in current_addresses:
                name = service_info.name or "Невідомий BLE пристрій"
                device_options[formatted_mac] = f"{name} ({formatted_mac})"

        # Схема форми з використанням Selectors від HA
        data_schema = vol.Schema({
            vol.Required("name", default=DEFAULT_NAME): str,
            vol.Required("address"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=mac, label=label)
                        for mac, label in device_options.items()
                    ],
                    custom_value=True,  # Дозволяє також ввести MAC вручну, якщо пристрою немає в списку
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors
        )

    async def async_step_bluetooth(self, discovery_info: bluetooth.BluetoothServiceInfoBleak):
        """Автоматичне виявлення пристрою системою Home Assistant."""
        formatted_address = normalize_mac(discovery_info.address)
        
        await self.async_set_unique_id(formatted_address.lower())
        self._abort_if_unique_id_configured()

        self._discovered_device = discovery_info
        
        # Назва пристрою за замовчуванням
        dev_name = discovery_info.name or DEFAULT_NAME
        self.context["title_placeholders"] = {"name": dev_name}

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(self, user_input=None):
        """Підтвердження додавання знайденого через Bluetooth пристрою."""
        if user_input is not None:
            formatted_address = normalize_mac(self._discovered_device.address)
            return self.async_create_entry(
                title=user_input.get("name", self._discovered_device.name or DEFAULT_NAME),
                data={
                    "name": user_input.get("name", self._discovered_device.name or DEFAULT_NAME),
                    "address": formatted_address,
                }
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": self._discovered_device.name or DEFAULT_NAME},
            data_schema=vol.Schema({
                vol.Required("name", default=self._discovered_device.name or DEFAULT_NAME): str,
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Створення потоку налаштувань."""
        return YKDLEDOptionsFlowHandler(config_entry)


class YKDLEDOptionsFlowHandler(config_entries.OptionsFlow):
    """Класичний обробник налаштувань опцій."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Крок ініціалізації редагування налаштувань."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "name", 
                    default=self.config_entry.data.get("name", DEFAULT_NAME)
                ): str,
            })
        )
