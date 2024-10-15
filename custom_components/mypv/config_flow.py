"""Config flow for ELWA myPV integration."""
# import logging

import json
from json import JSONDecodeError
from typing import Any

import requests
from requests.exceptions import ConnectTimeout, HTTPError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_HOSTS, DOMAIN, MAX_IP, MIN_IP


@callback
def mypv_entries(hass: HomeAssistant):
    """Return the hosts for the domain."""
    try:
        return hass.config_entries.async_entries(DOMAIN)[0].data[CONF_HOSTS]
    except:  # noqa: E722
        return []


class MpvConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """ELWA myPV config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod  # type: ignore  # noqa: PGH003
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return MpvOptionsFlow(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._errors = {}
        self._info = {}

    def _all_hosts_in_configuration_exist(self, ip_list) -> bool:
        """Return True if all hosts found already exist in configuration."""
        return all(ip in mypv_entries(self.hass) for ip in ip_list)

    def _check_hosts(self, min_ip: str, max_ip: str) -> tuple[bool, str]:
        """Check if connect to at least one myPV device in given ip range works."""

        # host_list = await detect_mypv(min_ip)
        host_list = []
        base_ip = min_ip.split(".")
        lower_ip = int(min_ip.split(".")[-1])
        upper_ip = int(max_ip.split(".")[-1])
        for ip in range(lower_ip, upper_ip + 1):
            ip_str = f"{base_ip[0]}.{base_ip[1]}.{base_ip[2]}.{ip}"
            try:
                response = requests.get(f"http://{ip_str}/mypv_dev.jsn", timeout=0.5)
                json.loads(response.text)
                host_list.append(ip_str)
            except (ConnectTimeout, HTTPError, TypeError, JSONDecodeError):
                pass
        return len(host_list) > 0, host_list

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""

        if user_input is not None:
            min_ip = user_input[MIN_IP]
            max_ip = user_input[MAX_IP]
            can_connect, ips_found = await self.hass.async_add_executor_job(
                self._check_hosts, min_ip, max_ip
            )
            if can_connect:
                if self._all_hosts_in_configuration_exist(ips_found):
                    self._errors[MIN_IP] = "host_exists"
                else:
                    return self.async_create_entry(
                        title="myPV",
                        data={
                            MIN_IP: min_ip,
                            MAX_IP: max_ip,
                            CONF_HOSTS: ips_found,
                        },
                    )
            else:
                self._errors[MIN_IP] = "could_not_connect"
        else:
            user_input = {}
            user_input[MIN_IP] = "192.168.178.100"
            user_input[MAX_IP] = "192.168.178.110"

        setup_schema = vol.Schema(
            {
                vol.Required(MIN_IP, default=user_input[MIN_IP]): str,
                vol.Required(MAX_IP, default=user_input[MAX_IP]): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=setup_schema, errors=self._errors
        )


class MpvOptionsFlow(config_entries.OptionsFlow, MpvConfigFlow):
    """Allow to change options of integration while running."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is None:
            user_input = {}
            user_input[MIN_IP] = "192.168.178.100"
            user_input[MAX_IP] = "192.168.178.110"

        opt_schema = vol.Schema(
            {
                vol.Required(MIN_IP, default=user_input[MIN_IP]): str,
                vol.Required(MAX_IP, default=user_input[MAX_IP]): str,
            }
        )
        errors = {}
        if user_input is not None:
            min_ip = user_input[MIN_IP]
            max_ip = user_input[MAX_IP]
            can_connect, ips_found = await self.hass.async_add_executor_job(
                self._check_hosts, min_ip, max_ip
            )
            if can_connect:
                if self._all_hosts_in_configuration_exist(ips_found):
                    self._errors[MIN_IP] = "host_exists"
                else:
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data=user_input,
                        options=self.config_entry.options,
                    )
                    return self.async_create_entry(data=user_input)
            else:
                self._errors[MIN_IP] = "could_not_connect"

        return self.async_show_form(
            step_id="init", data_schema=opt_schema, errors=errors
        )
