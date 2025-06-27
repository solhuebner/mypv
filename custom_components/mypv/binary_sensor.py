"""Binary sensors of myPV integration."""

import logging
from typing import TYPE_CHECKING, Any, override

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMM_HUB, DOMAIN

if TYPE_CHECKING:
    from .communicate import MypvCommunicator
    from .mypv_device import MpyDevice

    CoordinatorEntity = CoordinatorEntity[MypvCommunicator]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add all myPV binary sensor entities."""
    comm = hass.data[DOMAIN][entry.entry_id][COMM_HUB]

    for device in comm.devices:
        async_add_entities(device.binary_sensors)


class MpvBinSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a MyPV binary sensor."""

    def __init__(
        self,
        device: "MpyDevice",
        key: str,
        info: tuple[str, Any, str],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(device.comm)
        self._device = device
        self.entity_description = BinarySensorEntityDescription(
            key=key,
            has_entity_name=True,
            name=info[0],
            device_class=None,
        )
        self._attr_unique_id = (
            f"{self._device.serial_number}_{self.entity_description.name}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device.serial_number)},
            name=self._device.name,
            manufacturer="myPV",
            model=self._device.model,
        )

    @override
    def _handle_coordinator_update(self) -> None:
        key = self.entity_description.key
        try:
            value = self._device.data[key]
        except (KeyError, TypeError):
            _LOGGER.warning(
                "Update for %s failed, key %s not found", self.entity_id, key
            )
        else:
            self._attr_is_on = _map_bool_value(value)
            super()._handle_coordinator_update()


def _map_bool_value(value: Any) -> bool:
    match value:
        case "1" | 1 | True:
            return True
        case "0" | 0 | False:
            return False
        case _:
            _LOGGER.warning("Unexpected value for binary sensor: %r", value)
            return bool(value)
