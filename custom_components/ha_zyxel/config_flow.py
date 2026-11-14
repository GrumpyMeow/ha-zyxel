"""Config flow for Zyxel integration."""
import logging
from typing import Any
from urllib.parse import urlsplit

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .const import DEFAULT_HOST, DEFAULT_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Block excessive nr7101 debug logging
nr7101_logger = logging.getLogger("nr7101.nr7101")
nr7101_logger.setLevel(logging.WARNING)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


def _normalize_host(host: str) -> str | None:
    """Normalize and validate a router URL without changing its scheme."""
    host = host.strip()
    if not host:
        return None
    if "://" not in host:
        host = f"https://{host}"

    try:
        parsed = urlsplit(host)
        parsed.port
    except ValueError:
        return None

    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        return None

    return f"{parsed.scheme.lower()}://{parsed.netloc}".rstrip("/")


async def validate_input(hass: core.HomeAssistant, data):
    """Validate that the user input allows us to connect."""
    try:
        from nr7101 import nr7101

        router = await hass.async_add_executor_job(
            nr7101.NR7101,
            data[CONF_HOST],
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
        )

        if not await hass.async_add_executor_job(router.login):
            raise InvalidAuth

        if not await hass.async_add_executor_job(router.get_status):
            raise CannotConnect
    except (InvalidAuth, CannotConnect):
        raise
    except Exception as ex:
        _LOGGER.debug("Zyxel connection check failed: %s", type(ex).__name__)
        raise CannotConnect from ex

    return {"title": f"Zyxel device: ({data[CONF_HOST]})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zyxel devices."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        host = _normalize_host(user_input[CONF_HOST])
        if host is None:
            return self.async_show_form(
                step_id="user",
                data_schema=DATA_SCHEMA,
                errors={"base": "invalid_host"},
            )

        data = {**user_input, CONF_HOST: host}
        self._async_abort_entries_match({CONF_HOST: host})

        try:
            info = await validate_input(self.hass, data)
        except InvalidAuth:
            errors = {"base": "invalid_auth"}
        except CannotConnect:
            errors = {"base": "cannot_connect"}
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Unexpected config-flow error: %s", type(err).__name__)
            errors = {"base": "unknown"}
        else:
            return self.async_create_entry(title=info["title"], data=data)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate the router cannot be reached or queried."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate that router authentication failed."""
