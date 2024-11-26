from __future__ import annotations

from datetime import timedelta
from typing import Optional
import logging
from datetime import datetime

from combustion_ble.devices.device import Device
from combustion_ble.devices.probe import Probe
from combustion_ble.devices.meat_net_node import MeatNetNode
from homeassistant import config_entries, core
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from .const import DOMAIN, EVENT_DISCOVERED, TempUnit, EVENT_REFRESH


_LOGGER = logging.getLogger(__name__)

# [ name, unit_of_measurement, device_class, state_id, options]
SENSOR_TYPES = {
    "prob_temp_t1": ["Probe T1","temp", "temperature", "t1"],
    "prob_temp_t2": ["Probe T2","temp", "temperature", "t2"],
    "prob_temp_t3": ["Probe T3","temp", "temperature", "t3"],
    "prob_temp_t4": ["Probe T4","temp", "temperature", "t4"],
    "prob_temp_t5": ["Probe T5","temp", "temperature", "t5"],
    "prob_temp_t6": ["Probe T6","temp", "temperature", "t6"],
    "prob_temp_t7": ["Probe T7","temp", "temperature", "t7"],
    "prob_temp_t8": ["Probe T8","temp", "temperature", "t8"],
    "prob_temp_instant": ["Instant Temperature","temp", "temperature", "instant"],
    "prob_temp_core": ["Core Temperature","temp", "temperature", "core"],
    "prob_temp_ambient": ["Ambient Temperature","temp", "temperature", "ambient"],
    "prob_temp_surface": ["Surface Temperature","temp", "temperature", "surface"],
    "rssi": ["RSSI","dBm", "signal_strength", "rssi"],
    "battery": ["Battery",None, SensorDeviceClass.ENUM, "battery", ["OK", "LOW"]],
    "prediction_mode": ["Prediction Mode",None, SensorDeviceClass.ENUM, "prediction_mode", ["NONE", "TIME_TO_REMOVAL", "REMOVAL_AND_RESTING"]],
    "prediction_state": ["Prediction State",None, SensorDeviceClass.ENUM, "prediction_state", ["PROBE_NOT_INSERTED", "PROBE_INSERTED", "COOKING", "PREDICTING", "REMOVAL_PREDICTION_DONE"]],
    "prediction_type": ["Prediction Type",None, SensorDeviceClass.ENUM, "prediction_type", ["NONE", "REMOVAL", "RESTING"]],
    "prediction_setpoint": ["Prediction Setpoint","temp", "temperature", "prediction_setpoint"],
    "prediction_through": ["Prediction % Done","%", "", "prediction_through"],
    "prediction_value": ["Prediction Remaining","s", "duration", "prediction_value"],
    "prediction_core": ["Prediction Core Temp","temp", "temperature", "prediction_core"],

}

def format_device_name(device: Device):
    if isinstance(device, Probe):
        device_name = f"Probe {device.serial_number_string}"
    elif isinstance(device, MeatNetNode):
        ble_address = device.ble_identifier[-5:] if device.ble_identifier else ""
        device_name = f"MeatNet Node {ble_address}"
    return device_name

def format_device_id(device: Device):
    if isinstance(device, Probe):
        device_name = f"probe_{device.serial_number_string}"
    elif isinstance(device, MeatNetNode):
        ble_address = device.ble_identifier[-5:] if device.ble_identifier else ""
        device_name = f"note_{ble_address}"
    return device_name


def convert_temp(temp: float, unit: TempUnit) -> float:
    if (temp is None): return None
    if unit == TempUnit.FAHRENHEIT:
        return (temp * 9/5) + 32
    return temp


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):

    config = hass.data[DOMAIN][config_entry.entry_id]

    @callback
    def event_create_entity(device: Device) -> None:
        if (isinstance(device, Probe)):
            _LOGGER.info(f"Discovered device: {device}")

            sensors = []
            for sensor_type in SENSOR_TYPES:
                name = f"Combustion {SENSOR_TYPES[sensor_type][0]} {device.serial_number_string}"
                sensors.append(CombustionProbeEntity(hass, device,config, SENSOR_TYPES[sensor_type], name))

            async_add_entities(sensors, update_before_add=True)
    
    config_entry.async_on_unload(async_dispatcher_connect(hass, EVENT_DISCOVERED, event_create_entity))


class CombustionProbeEntity(SensorEntity):

    device: Probe
    sensor_type_data: list[str]
    config: any
    sensor_name: str

    unit_type: TempUnit = TempUnit.CELSIUS

    def __init__(self, hass: core.HomeAssistant, device: Probe, config: any, sensor_type_data: list[str], name: str = None):
        super().__init__()
        self.device = device
        self.config = config
        self.sensor_name = name
        self.sensor_type_data = sensor_type_data
        self.should_poll = False

        self.unit_type = TempUnit(self.config.get("unit_type", TempUnit.CELSIUS))

        _LOGGER.info(f"Creating entity for {self.sensor_name}")

    async def async_added_to_hass(self):
            """Register callbacks."""
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass, EVENT_REFRESH, self.sync
                )
            )        

    async def sync(self):
        self.async_schedule_update_ha_state(True)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.serial_number_string)},
            "name": format_device_name(self.device),
            "manufacturer": "Combustion Inc",
            "model": self.device.sku,
            "sw_version": self.device.firmware_version,
        }

    @property
    def name(self) -> str:
        return self.sensor_name
    
    @property
    def unique_id(self) -> str:
        return self.sensor_name
    
    @property
    def available(self) -> str:
        stale = (datetime.now() - self.device.last_update_time).total_seconds() > 15.0
        return not stale
    
    @property
    def unit_of_measurement(self) -> str:
        if self.sensor_type_data[1]  == "temp":
            return ("°F" if self.unit_type == TempUnit.FAHRENHEIT else "°C")
        else:
            return self.sensor_type_data[1]
        
    @property
    def device_class(self) -> str | None:
        return self.sensor_type_data[2]

    
    @property
    def state(self) -> Optional[str]:

        state_id = self.sensor_type_data[3]
        if state_id == "t1":
            return convert_temp(self.device.current_temperatures.values[0], self.unit_type) if self.device.current_temperatures else None
        elif state_id == "t2":
            return convert_temp(self.device.current_temperatures.values[1], self.unit_type) if self.device.current_temperatures else None
        elif state_id == "t3":
            return convert_temp(self.device.current_temperatures.values[2], self.unit_type) if self.device.current_temperatures else None
        elif state_id == "t4":
            return convert_temp(self.device.current_temperatures.values[3], self.unit_type) if self.device.current_temperatures else None
        elif state_id == "t5":
            return convert_temp(self.device.current_temperatures.values[4], self.unit_type) if self.device.current_temperatures else None
        elif state_id == "t6":
            return convert_temp(self.device.current_temperatures.values[5], self.unit_type) if self.device.current_temperatures else None
        elif state_id == "t7":
            return convert_temp(self.device.current_temperatures.values[6], self.unit_type) if self.device.current_temperatures else None
        elif state_id == "t8":
            return convert_temp(self.device.current_temperatures.values[7], self.unit_type) if self.device.current_temperatures else None
        elif state_id == "instant":
            return convert_temp(self.device._instant_read_celsius, self.unit_type)
        elif state_id == "core":
            return convert_temp(self.device._virtual_temperatures.value.core_temperature, self.unit_type)
        elif state_id == "ambient":
            return convert_temp(self.device._virtual_temperatures.value.ambient_temperature, self.unit_type)
        elif state_id == "surface":
            return convert_temp(self.device._virtual_temperatures.value.surface_temperature, self.unit_type)
        elif state_id == "rssi":
            return self.device.rssi
        elif state_id == "battery":
            return self.device.batery_status.name
        elif state_id == "prediction_mode":
            return self.device.prediction_info.prediction_mode.name if self.device.prediction_info else None
        elif state_id == "prediction_state":
            return self.device.prediction_info.prediction_state.name if self.device.prediction_info else None
        elif state_id == "prediction_type":
            return self.device.prediction_info.prediction_type.name if self.device.prediction_info else None
        elif state_id == "prediction_setpoint":
            return convert_temp(self.device.prediction_info.prediction_set_point_temperature, self.unit_type) if self.device.prediction_info else None
        elif state_id == "prediction_through":
            return self.device.prediction_info.percent_through_cook if self.device.prediction_info else None
        elif state_id == "prediction_value":
            return self.device.prediction_info.seconds_remaining if self.device.prediction_info else None
        elif state_id == "prediction_core":
            return convert_temp(self.device.prediction_info.estimated_core_temperature, self.unit_type) if self.device.prediction_info else None
        
        return None
    
    @property
    def extra_state_attributes(self) -> dict[str, str]:
        attribs = {
            "last_seen": self.device.last_update_time}
        
        if (self.sensor_type_data[2] != SensorDeviceClass.ENUM):
            attribs["state_class"] = "measurement"
        else:
            attribs["options"] = self.sensor_type_data[4]

        if self.sensor_type_data[0] == "RSSI":
            sorted_rssi = sorted(self.device.device_manager.devices.items(), key=lambda x: x[1].rssi, reverse=True)
            rssi = sorted_rssi[0][1].rssi
            attribs["best_rssi"] = rssi
            attribs["hops"] = self.device._last_normal_mode_hop_count.value if self.device._last_normal_mode_hop_count else self.device._last_instant_read_hop_count.value if self.device._last_instant_read_hop_count else None

        return attribs
    
    async def async_update(self) -> None:
        return None
