"""Support for Zyxel binary sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.ha_zyxel.const import DOMAIN
from .entity import (
    ZyxelCoordinatorEntity,
    get_parent_device_id,
    sync_subdevice_areas,
)
from .sensor import (
    _device_group_for_key,
    _flatten_dict,
    _is_value_scalar,
    _sensor_config_for_key,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Zyxel binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    if not coordinator.data:
        return

    flattened_data = _flatten_dict(coordinator.data)
    parent_device_id = get_parent_device_id(hass, entry, flattened_data)
    device_groups = {
        device_group
        for key, value in flattened_data.items()
        if _is_value_scalar(value)
        if (device_group := _device_group_for_key(key)) is not None
    }
    parent_area = sync_subdevice_areas(
        hass, entry, parent_device_id, device_groups
    )
    entities = []

    for key, value in flattened_data.items():
        if not _is_value_scalar(value):
            continue

        config = _sensor_config_for_key(key)
        if not config or config.get("type") != "boolean":
            continue

        device_group = _device_group_for_key(key)
        _LOGGER.debug("Creating binary sensor for key: %s", key)
        entities.append(
            BooleanZyxelSensor(
                coordinator,
                entry,
                key,
                config,
                device_group,
                parent_device_id,
                parent_area,
            )
        )

    if entities:
        async_add_entities(entities)


class BooleanZyxelSensor(ZyxelCoordinatorEntity, BinarySensorEntity):
    """Representation of a configured Zyxel binary sensor."""

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        key: str,
        config: dict[str, Any],
        device_group: str | None = None,
        parent_device_id: str | None = None,
        suggested_area: str | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(
            coordinator, entry, key, device_group, parent_device_id, suggested_area
        )
        self._attr_name = f"Zyxel {config['name']}"
        self._attr_icon = config["icon"]

    @property
    def is_on(self) -> bool | None:
        """Return the boolean value of the sensor."""
        try:
            value = self._get_value_from_path()
        except (KeyError, AttributeError, TypeError, ValueError):
            return None

        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on", "enabled"}:
                return True
            if normalized in {"false", "0", "no", "off", "disabled"}:
                return False
            return None
        return bool(value)
