import logging
import asyncio
from bleak import BleakClient
from bleak_retry_connector import establish_connection, BleakNotFoundError

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.components.bluetooth import async_ble_device_from_address

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

# Таймаут встановлення з'єднання
CONNECT_TIMEOUT = 20.0  

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([YKDBleLight(entry.data["name"], entry.data["address"])])

class YKDBleLight(LightEntity):
    def __init__(self, name, address):
        self._name = name
        self._address = address
        self._state = False
        self._brightness = 255
        self._effect = EFFECT_NONE
        
        self._client = None
        self._lock = asyncio.Lock()
        self._disconnect_timer_handle = None
        
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

    def _reset_disconnect_timer(self):
        """Скидає таймер роз'єднання без утворення завислих тасків."""
        if self._disconnect_timer_handle:
            self._disconnect_timer_handle.cancel()
        
        loop = asyncio.get_running_loop()
        self._disconnect_timer_handle = loop.call_later(
            60, lambda: asyncio.create_task(self._async_disconnect_if_idle())
        )

    async def _async_disconnect_if_idle(self):
        """Авто-відключення при простої в 60 секунд."""
        if self._lock.locked():
            self._reset_disconnect_timer()
            return

        async with self._lock:
            if self._client:
                if self._client.is_connected:
                    _LOGGER.debug("Closing idle Bluetooth connection for %s", self._name)
                    try:
                        await self._client.disconnect()
                    except Exception as err:
                        _LOGGER.warning("Error disconnecting from %s: %s", self._address, err)
                self._client = None

    def _on_disconnected(self, client):
        """Обробник несподіваного розриву зв'язку."""
        _LOGGER.debug("Device %s disconnected unexpectedly", self._address)
        self._client = None

    async def _get_client(self):
        """Отримує клієнт або створює новий через establish_connection."""
        if self._client is not None and self._client.is_connected:
            self._reset_disconnect_timer()
            return self._client

        device = async_ble_device_from_address(self.hass, self._address, connectable=True)
        
        if not device:
            raise BleakNotFoundError(f"Пристрій {self._address} не знайдено в радіусі дії")

        # Передаємо саме клас BleakClient першим аргументом
        self._client = await establish_connection(
            BleakClient,
            device, 
            self._name, 
            max_attempts=3,
            disconnected_callback=self._on_disconnected,
            use_services_cache=True,
        )
        
        self._reset_disconnect_timer()
        return self._client

    async def _send_commands(self, commands):
        """Послідовна відправка команд контролеру."""
        async with self._lock:
            try:
                is_new_connection = self._client is None or not self._client.is_connected
                
                # Обгортаємо виклики підключення у таймаут
                client = await asyncio.wait_for(self._get_client(), timeout=CONNECT_TIMEOUT)
                
                # Пауза після підключення для стабілізації чіпа
                if is_new_connection:
                    await asyncio.sleep(0.5)
                
                for cmd in commands:
                    await client.write_gatt_char(
                        CHARACTERISTIC_UUID, 
                        bytearray.fromhex(cmd), 
                        response=False
                    )
                    await asyncio.sleep(0.15)
                    
                self._reset_disconnect_timer()
                return True

            except asyncio.TimeoutError:
                _LOGGER.error("Тайм-аут підключення до %s (%ds вийшли)", self._address, int(CONNECT_TIMEOUT))
                self._client = None
                return False
                
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
