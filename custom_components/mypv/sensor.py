"""Sensors of myPV integration."""

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMM_HUB, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Add all myPV sensor entities."""
    comm = hass.data[DOMAIN][entry.entry_id][COMM_HUB]

    for device in comm.devices:
        async_add_entities(device.sensors)


class MpvSensor(CoordinatorEntity):
    """Representation of myPV sensors."""

    def __init__(self, device, key, info) -> None:
        """Initialize the sensor."""
        super().__init__(device.comm)
        self.device = device
        self.comm = device.comm
        self._key = key
        self._name = info[0]
        self._unit_of_measurement = info[1]
        self._type = info[2]
        self._last_value = None
        if key.split("_")[0] in ["power1", "power2", "power3"]:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_entity_registry_enabled_default = (
                False  # Entity will initally be disabled
            )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        try:
            state = self.device.data[self._key]
            if self._type == "power_act":
                relOut = int(self.comm.data["rel1_out"])
                loadNom = int(self.comm.data["load_nom"])
                state = (relOut * loadNom) + int(state)
            self._last_value = state
        except Exception as err_msg:
            state = self._last_value
        if state is None:
            return state
        if self._unit_of_measurement == UnitOfFrequency.HERTZ:
            return state / 1000
        if self._unit_of_measurement == UnitOfTemperature.CELSIUS:
            return state / 10
        if self._unit_of_measurement == UnitOfElectricCurrent.AMPERE:
            return state / 10
        return state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return device class of sensor."""
        if self._unit_of_measurement == UnitOfTemperature.CELSIUS:
            return SensorDeviceClass.TEMPERATURE
        if self._unit_of_measurement == UnitOfElectricCurrent.AMPERE:
            return SensorDeviceClass.CURRENT
        if self._unit_of_measurement == UnitOfElectricPotential.VOLT:
            return SensorDeviceClass.VOLTAGE
        if self._unit_of_measurement == UnitOfPower.WATT:
            return SensorDeviceClass.POWER
        if self._unit_of_measurement == UnitOfFrequency.HERTZ:
            return SensorDeviceClass.FREQUENCY
        return SensorDeviceClass.ENUM

    @property
    def state_class(self):
        """Return device state class of sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def icon(self):
        """Return icon."""
        if self._name in ["IP", "DNS", "Gateway", "Subnet mask"]:
            return "mdi:ip-network"
        if self._name.split()[-1] == "version":
            return "mdi:numeric"
        return None

    @property
    def unique_id(self):
        """Return unique id based on device serial and variable."""
        return f"{self.device.serial_number}_{self._name}"

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, self.device.serial_number)},
            "name": self.device.name,
            "manufacturer": "myPV",
            "model": self.device.model,
        }


class MpvUpdateSensor(MpvSensor):
    """Return update state from enum."""

    @property
    def icon(self):
        """Return icon."""
        match self._last_value:
            case 0:
                return "mdi:clock-check-outline"
            case 1:
                return "mdi:update"
            case 5:
                return "mdi:download-off"
            case 10:
                return "mdi:cellphone-arrow-down"
            case _:
                return "mdi:download"

    @property
    def state(self):
        """Return the state of the device."""

        UPDATE_STATUS = {
            0: "No new fw available",
            1: "New fw available",
            2: "Download started (ini)",
            3: "Download started (bin)",
            4: "Download started (other)",
            5: "Download interrupted",
            10: "Download finished, waiting for installation",
        }
        try:
            state = self.device.data[self._key]
            self._last_value = state
        except Exception as err_msg:
            state = self._last_value
        return UPDATE_STATUS[state]


class MpvDevStatSensor(MpvSensor):
    """Return device state from enum."""

    def __init__(self, device, key, info) -> None:
        """Initialize the sensor."""
        super().__init__(device, key, info)
        self._last_value = 1

    @property
    def icon(self):
        """Return icon."""
        if self._last_value == 1:
            return "mdi:water-boiler-off"
        if self._last_value == 3:
            return "mdi:water-boiler-auto"
        if self._last_value == 5:
            return "mdi:water-boiler-off"
        if self._last_value > 200:
            return "mdi:water-boiler-alert"
        return "mdi:water-boiler"

    @property
    def state(self):
        """Return the state of the device."""

        DEVICE_STATE = {
            1: "No control",
            2: "Heat",
            3: "Standby",
            4: "Boost heat",
            5: "Heat finished",
            20: "Legionella-Boost active",
            21: "Device disabled",
            22: "Device blocked",
            201: "STL triggered",
            202: "Power stage overtemp",
            203: "Power stage PCB temp probe fault",
            204: "Hardware fault",
            205: "ELWA Temp Sensor fault",
            209: "Mainboard Error",
        }
        try:
            state = self.device.state
            self._last_value = state + 1
        except Exception as err_msg:
            pass
        return DEVICE_STATE[self._last_value]
