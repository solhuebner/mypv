"""Text sensors of myPV integration."""

import logging

from homeassistant.components.sensor import SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMM_HUB, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Add all myPV binary sensor entities."""
    comm = hass.data[DOMAIN][entry.entry_id][COMM_HUB]

    for device in comm.devices:
        async_add_entities(device.text_sensors)


class MpvTxtSensor(CoordinatorEntity):
    """Representation of a myPV text sensors."""

    def __init__(self, device, key, info) -> None:
        """Initialize the sensor."""
        super().__init__(device.comm)
        self.device = device
        self.comm = device.comm
        self._key = key
        self._name = info[0]
        self._type = info[2]
        self._last_value = None

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
        return state

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
