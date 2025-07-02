"""Sensors of myPV integration."""

import logging
from typing import Any

from homeassistant.components.integration.sensor import IntegrationSensor, UnitOfTime
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMM_HUB, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Add all myPV sensor entities."""
    comm = hass.data[DOMAIN][entry.entry_id][COMM_HUB]

    for device in comm.devices:
        async_add_entities(device.sensors)


class MpvSensor(CoordinatorEntity, SensorEntity):
    """Representation of myPV sensors."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = True

    def __init__(self, device, key: str, info: list[Any]) -> None:
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
        return self._last_value

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
        if self._unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR:
            return SensorDeviceClass.ENERGY
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
        if self._name.split()[-1] == "Version":
            return "mdi:numeric"
        if self._name.split()[-1] == "Surplus":
            return "mdi:octagram-plus-outline"
        if self._name in ["Screen mode", "Power supply state"]:
            return "mdi:state-machine"
        if self._name in ["Fan speed"]:
            return "mdi:fan"
        if self._name in ["Control type"]:
            return "mdi:format-list-bulleted-type"
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

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        try:
            state = self.device.data[self._key]
            if self._type == "power_act":
                relOut = int(self.comm.data["rel1_out"])
                loadNom = int(self.comm.data["load_nom"])
                state = (relOut * loadNom) + int(state)
        except Exception:  # noqa: BLE001
            state = self._last_value
        if state is None:
            return state
        if self._unit_of_measurement == UnitOfFrequency.HERTZ:
            state = state / 1000
        if self._unit_of_measurement == UnitOfTemperature.CELSIUS:
            state = state / 10
        if self._unit_of_measurement == UnitOfElectricCurrent.AMPERE:
            state = state / 10
        self._last_value = state
        self._attr_native_value = state
        self.async_write_ha_state()
        return None


class MpvOutStatSensor(MpvSensor):
    """Return output state from last digit for AC-Thor 9s."""

    @callback
    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        value = self.device.data[self._key]
        if isinstance(value, int):
            str_number = str(value).zfill(4)
        elif isinstance(value, str):
            str_number = value
        else:
            _LOGGER.warning("Unexpected type for output status sensor value: %r", value)
            str_number = "0000"
        state = int(str_number[-1])  # Get the last digit
        self._last_value = state
        self._attr_native_value = state
        self.async_write_ha_state()

    @property
    def icon(self):
        """Return icon."""
        return "mdi:format-list-numbered"


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
        except Exception:  # noqa: BLE001
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
            0: "State not available",
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
        except Exception:  # noqa: BLE001
            pass
        return DEVICE_STATE[self._last_value]


class MpvEnergySensor(IntegrationSensor, MpvSensor):
    """Return energy state by integrating power consumption."""

    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, device, key, info, source) -> None:
        """Initialize the sensor."""
        self._last_value = 0
        # Explicitly initialize both superclasses
        IntegrationSensor.__init__(
            self,
            source_entity=f"sensor.{source[0].replace(' ', '_').replace('-', '_').lower()}",
            name=info[0],
            round_digits=1,
            integration_method="trapezoidal",
            unit_prefix="k",
            unit_time=UnitOfTime.HOURS,
            unique_id=f"{device.serial_number}_{info[0]}",
            max_sub_interval=None,
        )
        self._name = info[0]
        MpvSensor.__init__(self, device, key, info)

    @property
    def icon(self):
        """Return icon."""
        return "mdi:meter-electric"

    @property
    def state(self):
        """Return the state of the device."""
        return self._last_value

    @property
    def device_class(self):
        """Return device class of sensor."""
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self):
        """Return state class of sensor."""
        return SensorStateClass.TOTAL

    @property
    def last_reset(self):
        """Return last reset of sensor."""
        return None

    async def async_update(self):
        """Update the sensor state."""
        await self.async_get_last_sensor_data()
        if self._state is None:
            return
        try:
            self._last_value = float(self._state)
        except ValueError:
            _LOGGER.error("Failed to convert state to float: %s", self._state)
            self._last_value = 0.0
