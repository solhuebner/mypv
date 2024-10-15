"""Numbers of myPV integration."""

import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMM_HUB, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Add all myPV sensor entities."""
    comm = hass.data[DOMAIN][entry.entry_id][COMM_HUB]

    for device in comm.devices:
        async_add_entities(device.controls)


class MpvPowerControl3500(CoordinatorEntity, NumberEntity):
    """Representation of myPV power control."""

    _attr_has_entity_name = True
    _attr_device_class = NumberDeviceClass.POWER
    _attr_native_max_value = 3500
    _attr_native_min_value = 0
    _attr_native_step = 500

    def __init__(self, device, key, info) -> None:
        """Initialize the switch."""
        super().__init__(device.comm)
        self.device = device
        self.comm = device.comm
        self._key = key
        self._name = info[0]
        self._type = info[2]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

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
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.device.data[self._key]
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set the new value."""
        self._attr_native_value = value
        await self.comm.set_power(self.device, int(value))


# class MpvPidPowerControl3500(MpvPowerControl3500):
#     """Representation of myPV pid power control."""

#     def __init__(self, device, key, info) -> None:
#         """Initialize the switch."""
#         super().__init__(device, key, info)
#         self._name = "PID " + info[0]

#     @callback
#     def _handle_coordinator_update(self) -> None:
#         """Handle updated data from the coordinator."""
#         if self.device.pid_power_set in [1, 2]:
#             # wait for update in power status
#             self.device.pid_power_set += 1
#         elif self.device.data[self._key] == 0:
#             # power is switched off
#             self._attr_native_value = 0
#             self.device.pid_power = 0
#             self.device.pid_power_set = 0
#         self.async_write_ha_state()

#     async def async_set_native_value(self, value: float) -> None:
#         """Set the new value."""
#         self._attr_native_value = value
#         self.device.pid_power = value
#         self.device.pid_power_set = 1
#         await self.comm.set_pid_power(self.device.ip, int(value))
