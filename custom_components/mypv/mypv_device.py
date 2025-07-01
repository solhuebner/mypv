"""myPV integration."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .binary_sensor import MpvBin1Sensor, MpvBin2Sensor, MpvBin3Sensor, MpvBinSensor
from .button import MpvBoostButton
from .const import DOMAIN, SENSOR_TYPES, SETUP_TYPES
from .number import MpvPidPowerControl, MpvPowerControl, MpvSetupControl, MpvToutControl
from .sensor import (
    MpvDevStatSensor,
    MpvEnergySensor,
    MpvOutStatSensor,
    MpvSensor,
    MpvUpdateSensor,
)
from .switch import MpvHttpSwitch, MpvSetupSwitch

_LOGGER = logging.getLogger(__name__)


class MpyDevice(CoordinatorEntity):
    """Class definition of an myPV device."""

    def __init__(self, comm, ip, info) -> None:
        """Initialize the device."""
        super().__init__(comm)
        self._hass: HomeAssistant = comm.hass
        self._entry = comm.config_entry
        self._info = info
        self._ip = ip
        self._id = info["number"]
        self.comm = comm
        self.serial_number = info["sn"]
        self.fw = info["fwversion"]
        self.model = info["device"]
        if "acthor9s" in info:
            self.model += " 9s"
        self._name = f"{self.model} {self._id}"
        self.state = 0
        self.setup = []
        self.data = []
        self.sensors = []
        self.binary_sensors = []
        self.controls = []
        self.buttons = []
        self.switches = []
        self.text_sensors = []
        self.state_dict = {}
        self.max_power = 3600
        self.pid_power = 0
        self.pid_power_set = 0
        self.logger = _LOGGER
        self.control_enabled = True
        self.energy_sensor = None

    async def initialize(self):
        """Get setup information, find sensors."""
        self.setup = await self.comm.setup_update(self)
        self.data = await self.comm.data_update(self)
        await self.comm.state_update(self)
        await self.init_entities()
        dr.async_get(self._hass).async_get_or_create(
            config_entry_id=self._entry.entry_id,
            identifiers={(DOMAIN, self.serial_number)},
            manufacturer="my-PV GmbH",
            name=self._name,
            model=self.model,
            sw_version=self.fw,
            hw_version=self.serial_number,
        )

    @property
    def unique_id(self):
        """Return unique id based on device serial."""
        return self.serial_number

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def ip(self):
        """Return the ip address of the device."""
        return self._ip

    async def init_entities(self):
        """Take sensors from data and init HA sensors."""

        def remove_data_key(key):
            """Safely remove key from data_keys."""
            if key in data_keys:
                data_keys.remove(key)

        data_keys = list(self.data.keys())  # type: ignore  # noqa: PGH003
        defined_data_keys = list(SENSOR_TYPES.keys())  # type: ignore  # noqa: PGH003
        setup_keys = list(self.setup.keys())  # type: ignore  # noqa: PGH003
        defined_setup_keys = list(SETUP_TYPES.keys())
        remove_data_key("device")
        remove_data_key("fwversionlatest")
        remove_data_key("psversionlatest")
        remove_data_key("p9sversionlatest")
        remove_data_key("fsetup")
        remove_data_key("date")
        remove_data_key("loctime")
        remove_data_key("unixtime")
        remove_data_key("wifi_list")
        remove_data_key("freq")
        self.sensors.append(
            MpvDevStatSensor(self, "control_state", ["Control state", None, "sensor"])
        )
        for key in defined_data_keys:
            # use only keys included in data with valid values
            if (
                SENSOR_TYPES[key][2]
                in [
                    "binary_sensor",
                    "sensor",
                    "version",
                    "ip_string",
                    "upd_stat",
                    "dev_stat",
                    "button",
                    "switch",
                    "control",
                    "text",
                ]
                and key in data_keys
                and self.data[key] is not None  # type: ignore  # noqa: PGH003
                and self.data[key] != "null"  # type: ignore  # noqa: PGH003
            ):
                self.logger.info(f"Sensor Key: {key}: {self.data[key]}")  # type: ignore  # noqa: G004, PGH003
                if SENSOR_TYPES[key][2] in ["sensor", "text", "ip_string", "version"]:
                    self.sensors.append(MpvSensor(self, key, SENSOR_TYPES[key]))
                elif SENSOR_TYPES[key][2] in ["dev_stat"]:
                    self.sensors.append(MpvDevStatSensor(self, key, SENSOR_TYPES[key]))
                elif SENSOR_TYPES[key][2] in ["upd_stat"]:
                    self.sensors.append(MpvUpdateSensor(self, key, SENSOR_TYPES[key]))
                elif SENSOR_TYPES[key][2] in ["binary_sensor"]:
                    if self.model == "AC-THOR 9s" and SENSOR_TYPES[key][0] == "Relais":
                        SENSOR_TYPES[key][0] = "Relais 1"
                        self.binary_sensors.append(
                            MpvBin1Sensor(self, key, SENSOR_TYPES[key])  # type: ignore  # noqa: PGH003
                        )
                        SENSOR_TYPES[key][0] = "Relais 3"
                        self.binary_sensors.append(
                            MpvBin2Sensor(self, key, SENSOR_TYPES[key])  # type: ignore  # noqa: PGH003
                        )
                        SENSOR_TYPES[key][0] = "Relais 2"
                        self.binary_sensors.append(
                            MpvBin3Sensor(self, key, SENSOR_TYPES[key])  # type: ignore  # noqa: PGH003
                        )
                        SENSOR_TYPES[key][0] = "Output status"
                        self.sensors.append(
                            MpvOutStatSensor(self, key, SENSOR_TYPES[key])
                        )
                    else:
                        self.binary_sensors.append(
                            MpvBinSensor(self, key, SENSOR_TYPES[key])  # type: ignore  # noqa: PGH003
                        )
                elif SENSOR_TYPES[key][2] in ["button"] and self.control_enabled:
                    self.buttons.append(MpvBoostButton(self, key, SENSOR_TYPES[key]))
                elif SENSOR_TYPES[key][2] in ["control"]:
                    if self.control_enabled:
                        self.controls.append(
                            MpvPowerControl(self, key, SENSOR_TYPES[key])
                        )
                        self.controls.append(
                            MpvPidPowerControl(self, key, SENSOR_TYPES[key])
                        )
                    # Setup as sensor, too
                    self.sensors.append(
                        MpvSensor(self, key, SENSOR_TYPES[key])
                    )  # power
                    self.sensors.append(
                        MpvEnergySensor(
                            self,
                            f"int_{key}",
                            SENSOR_TYPES[f"int_{key}"],
                            SENSOR_TYPES[key],
                        )
                    )  # energy
                    self.energy_sensor = self.sensors[-1]
            if SENSOR_TYPES[key][2] in ["sensor_always"]:
                # Sensor value might not be available at statrtup
                self.sensors.append(MpvSensor(self, key, SENSOR_TYPES[key]))
        for key in defined_setup_keys:
            # use only keys included in setup with valid values
            if (
                SETUP_TYPES[key][2]
                in [
                    "binary_sensor",
                    "button",
                    "number",
                    "sensor",
                    "switch",
                    "control",
                ]
                and key in setup_keys
                and self.setup[key] is not None  # type: ignore  # noqa: PGH003
                and self.setup[key] != "null"  # type: ignore  # noqa: PGH003
            ):
                self.logger.info(f"Setup Key: {key}: {self.setup[key]}")  # type: ignore  # noqa: G004, PGH003
                if SETUP_TYPES[key][2] in ["sensor", "text", "ip_string"]:
                    self.sensors.append(MpvSensor(self, key, SETUP_TYPES[key]))
                elif SETUP_TYPES[key][2] in ["binary_sensor"]:
                    self.binary_sensors.append(
                        MpvBinSensor(self, key, SETUP_TYPES[key])  # type: ignore  # noqa: PGH003
                    )
                elif SETUP_TYPES[key][2] in ["switch"]:
                    self.switches.append(MpvSetupSwitch(self, key, SETUP_TYPES[key]))
                elif SETUP_TYPES[key][2] in ["number"]:
                    self.controls.append(MpvSetupControl(self, key, SETUP_TYPES[key]))
        self.switches.append(MpvHttpSwitch(self, "ctrl"))
        self.controls.append(MpvToutControl(self, "tout"))
        await self.update()

    async def update(self):
        """Update all sensors."""
        if self.energy_sensor is not None:
            await self.energy_sensor.async_update()  # type: ignore  # noqa: PGH003
        resp = await self.comm.data_update(self)
        if resp:
            self.data = resp
        resp = await self.comm.setup_update(self)
        if resp:
            self.setup = resp
        if self.control_enabled:
            if await self.comm.state_update(self):
                if "State" in self.state_dict:
                    self.state = int(self.state_dict["State"])
                else:
                    self.state = -1
