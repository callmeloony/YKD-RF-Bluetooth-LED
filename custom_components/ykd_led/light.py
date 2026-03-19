import logging
import asyncio
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from bleak import BleakClient
from .const import (
    DOMAIN, 
    CHARACTERISTIC_UUID, 
    CMD_ON, 
    CMD_OFF, 
    CMD_PREFIX, 
    CMD_SUFFIX, 
    EFFECTS_MAP,
    EFFECT_NONE
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([YKDBleLight(entry.data["name"], entry.data["address"])])

class YKDBleLight(LightEntity):
    def __init__(self, name, address):
        self._name = name
        self._address = address
        self._state = False
        self._brightness = 255
        self._effect = EFFECT_NONE
        
        # Для підтримки постійного з'єднання
        self._client = None
        self._lock = asyncio.Lock()
        self._disconnect_timer = None
        
        self._attr_supported_features = LightEntityFeature.EFFECT
        self._attr_effect_list = [EFFECT_NONE] + list(EFFECTS_MAP.keys())
        self._attr_unique_id = f"ykd_{address.replace(':', '').lower()}"

    @property
    def name(self): return self._name
    @property
    def is_on(self): return self._state
    @property
    def brightness(self): return self._brightness
    @property
    def effect(self): return self._effect
    @property
    def supported_color_modes(self): return {ColorMode.BRIGHTNESS}
    @property
    def color_mode(self): return ColorMode.BRIGHTNESS

    async def _get_client(self):
        """Отримує існуючий клієнт або створює новий."""
        if self._client is not None and self._client.is_connected:
            self._reset_disconnect_timer()
            return self._client
        
        self._client = BleakClient(self._address, timeout=10.0)
        await self._client.connect()
        self._reset_disconnect_timer()
        return self._client

    def _reset_disconnect_timer(self):
        """Скидає таймер роз'єднання."""
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
        
        self._disconnect_timer = asyncio.get_event_loop().call_later(
            60, lambda: asyncio.create_task(self._async_disconnect())
        )

    async def _async_disconnect(self):
        """Роз'єднує клієнт по таймеру."""
        async with self._lock:
            if self._client and self._client.is_connected:
                _LOGGER.debug("Closing idle Bluetooth connection for %s", self._name)
                await self._client.disconnect()
            self._client = None

    async def _send_commands(self, commands):
        """Відправка списку команд в одній сесії."""
        async with self._lock:
            try:
                client = await self._get_client()
                for cmd in commands:
                    await client.write_gatt_char(CHARACTERISTIC_UUID, bytearray.fromhex(cmd))
                    await asyncio.sleep(0.1)
                return True
            except Exception as e:
                _LOGGER.error("BLE Error for %s: %s", self._address, e)
                self._client = None
                return False

    async def async_turn_on(self, **kwargs):
        commands = [CMD_ON]
        
        if ATTR_EFFECT in kwargs:
            self._effect = kwargs[ATTR_EFFECT]
            if self._effect == EFFECT_NONE:
                level = "{:02x}".format(self._brightness)
                commands.append(f"{CMD_PREFIX}{level}{level}{level}{CMD_SUFFIX}")
            else:
                commands.append(EFFECTS_MAP.get(self._effect))
        elif ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            self._effect = EFFECT_NONE
            level = "{:02x}".format(self._brightness)
            commands.append(f"{CMD_PREFIX}{level}{level}{level}{CMD_SUFFIX}")
        else:
            level = "{:02x}".format(self._brightness)
            commands.append(f"{CMD_PREFIX}{level}{level}{level}{CMD_SUFFIX}")

        if await self._send_commands(commands):
            self._state = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        if await self._send_commands([CMD_OFF]):
            self._state = False
            self.async_write_ha_state()