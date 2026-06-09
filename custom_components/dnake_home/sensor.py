import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.assistant import assistant
from .core.constant import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


def load_sensors(device_list):
    air_device_list = [device for device in device_list if device.get("ty") == 18692]
    entities = []
    for air_device in air_device_list:
        entities.append(DnakeHumiditySensor(
            air_device['nm'],
            air_device['ch'],
            air_device.get('na', '传感器'),
            air_device.get('humi', 0)
        ))
        entities.append(DnakeTemperatureSensor(
            air_device['nm'],
            air_device['ch'],
            air_device.get('na', '传感器'),
            air_device.get('temp', 0)
        ))
        entities.append(DnakePM25Sensor(
            air_device['nm'],
            air_device['ch'],
            air_device.get('na', '传感器'),
            air_device.get('pm2.5', 0)
        ))
    _LOGGER.info(f"find sensor num: {len(entities)}")
    assistant.entries["sensor"] = entities


def update_sensors_state(states):
    sensors = assistant.entries["sensor"]
    for sensor in sensors:
        state = next((state for state in states if state.get('devType') == 18692 and sensor.is_hint_state(state)), None)
        if state:
            sensor.update_state(state)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
):
    sensor_list = assistant.entries["sensor"]
    if sensor_list:
        async_add_entities(sensor_list)


class DnakeHumiditySensor(SensorEntity):
    def __init__(self, dev_no, dev_ch, device_name, initial_humi):
        self._dev_no = dev_no
        self._dev_ch = dev_ch
        self._name = f"{device_name}(湿度)"
        self._native_value = int(initial_humi / 100)

    def is_hint_state(self, state):
        return (state.get("devNo") == self._dev_no and
                state.get("devCh") == self._dev_ch and
                state.get('humi') is not None)

    @property
    def unique_id(self):
        return f"dnake_humi_{self._dev_no}_{self._dev_ch}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"humi_{self._dev_no}_{self._dev_ch}")},
            name=self._name,
            manufacturer=MANUFACTURER,
            model="湿度传感器",
            via_device=(DOMAIN, "gateway"),
        )

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._native_value

    @property
    def native_unit_of_measurement(self):
        return "%"

    @property
    def device_class(self):
        return SensorDeviceClass.HUMIDITY

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    def update_state(self, state):
        humi_raw = state.get("humi", 0)
        self._native_value = int(humi_raw / 100)
        self.async_write_ha_state()


class DnakeTemperatureSensor(SensorEntity):
    def __init__(self, dev_no, dev_ch, device_name, initial_temp):
        self._dev_no = dev_no
        self._dev_ch = dev_ch
        self._name = f"{device_name}(温度)"
        self._native_value = int(initial_temp / 100)

    def is_hint_state(self, state):
        return (state.get("devNo") == self._dev_no and
                state.get("devCh") == self._dev_ch and
                state.get('temp') is not None)

    @property
    def unique_id(self):
        return f"dnake_temp_{self._dev_no}_{self._dev_ch}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"temp_{self._dev_no}_{self._dev_ch}")},
            name=self._name,
            manufacturer=MANUFACTURER,
            model="温度传感器",
            via_device=(DOMAIN, "gateway"),
        )

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._native_value

    @property
    def native_unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    def update_state(self, state):
        temp_raw = state.get("temp", 0)
        self._native_value = int(temp_raw / 100)
        self.async_write_ha_state()


class DnakePM25Sensor(SensorEntity):
    def __init__(self, dev_no, dev_ch, device_name, initial_pm25):
        self._dev_no = dev_no
        self._dev_ch = dev_ch
        self._name = f"{device_name}(PM2.5)"
        self._native_value = initial_pm25

    def is_hint_state(self, state):
        return (state.get("devNo") == self._dev_no and
                state.get("devCh") == self._dev_ch and
                state.get('pm2.5') is not None)

    @property
    def unique_id(self):
        return f"dnake_pm25_{self._dev_no}_{self._dev_ch}"

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"pm25_{self._dev_no}_{self._dev_ch}")},
            name=self._name,
            manufacturer=MANUFACTURER,
            model="PM2.5传感器",
            via_device=(DOMAIN, "gateway"),
        )

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._native_value

    @property
    def native_unit_of_measurement(self):
        return "μg/m³"

    @property
    def device_class(self):
        return SensorDeviceClass.PM25

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    def update_state(self, state):
        self._native_value = state.get("pm2.5", 0)
        self.async_write_ha_state()
