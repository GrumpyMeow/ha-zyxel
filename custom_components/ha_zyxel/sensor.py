"""Support for Zyxel device sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.ha_zyxel.const import DOMAIN
from .entity import (
    ZyxelCoordinatorEntity,
    get_parent_device_id,
    sync_subdevice_areas,
)

_LOGGER = logging.getLogger(__name__)

# Define some known sensor types for proper configuration
KNOWN_SENSORS = {
    "INTF_RSSI": {
        "name": "Cellular RSSI",
        "unit": "dBm",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_PhyCell_ID": {
        "name": "Physical Cell ID",
        "unit": None,
        "icon": "mdi:antenna",
        "device_class": None,
        "state_class": None,
    },
    "INTF_RSRP": {
        "name": "Cellular Reference Signal Received Power",
        "unit": "dBm",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_RSRQ": {
        "name": "Cellular Reference Signal Received Quality",
        "unit": "dB",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_SINR": {
        "name": "Cellular Signal-to-Noise Ratio",
        "unit": "dB",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_MCS": {
        "name": "Cellular Modulation and Coding Scheme",
        "unit": "",
        "icon": "mdi:signal",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_CQI": {
        "name": "Cellular Channel Quality Indicator",
        "unit": "",
        "icon": "mdi:signal",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_RI": {
        "name": "Cellular Rank Indicator",
        "unit": "",
        "icon": "mdi:signal",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "INTF_PMI": {
        "name": "Cellular Precoding Matrix Indicator",
        "unit": "",
        "icon": "mdi:signal",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "NSA_PhyCellID": {
        "name": "NSA Physical Cell ID",
        "unit": None,
        "icon": "mdi:antenna",
        "device_class": None,
        "state_class": None,
    },
    "NSA_RSRP": {
        "name": "NSA Reference Signal Received Power",
        "unit": "dBm",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "NSA_RSRQ": {
        "name": "NSA Reference Signal Received Quality",
        "unit": "dB",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "NSA_RSSI": {
        "name": "NSA Reference Signal Strength Indicator",
        "unit": "dBm",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "NSA_SINR": {
        "name": "NSA Signal-to-Noise Ratio",
        "unit": "dB",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "TEMPERATURE_AMBIENT": {
        "name": "Ambient Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "TEMPERATURE_SDX": {
        "name": "SDX Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "TEMPERATURE_CPU0": {
        "name": "CPU Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "PhyCellID": {
        "name": "Physical Cell ID",
        "unit": None,
        "icon": "mdi:antenna",
        "device_class": None,
        "state_class": None,
    },
    "CELL_Roaming_Enable": {
        "name": "Roaming Enabled",
        "type": "boolean",
        "unit": None,
        "icon": "mdi:toggle-switch",
        "device_class": None,
        "state_class": None,
    },
    "EasyMeshEnable": {
        "name": "Easy Mesh Enabled",
        "type": "boolean",
        "unit": None,
        "icon": "mdi:toggle-switch",
        "device_class": None,
        "state_class": None,
    },
    
}

KNOWN_TYPES = {
    "Enable": {
        "name": "Enabled",
        "type": "boolean",
        "unit": None,
        "icon": "mdi:toggle-switch",
        "device_class": None,
        "state_class": None,
    },
    "BytesSent": {
        "name": "Bytes Sent",
        "unit": "B",
        "icon": "mdi:numeric-10-box",
        "device_class": SensorDeviceClass.DATA_SIZE,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "BytesReceived": {
        "name": "Bytes Received",
        "unit": "B",
        "icon": "mdi:numeric-10-box",
        "device_class": SensorDeviceClass.DATA_SIZE,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "PacketsSent": {
        "name": "Packets Sent",
        "unit": "packets",
        "icon": "mdi:counter",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "PacketsReceived": {
        "name": "Packets Received",
        "unit": "packets",
        "icon": "mdi:counter",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "SINR": {
        "name": "Cellular Signal-to-Noise Ratio",
        "unit": "dB",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "RSRQ": {
        "name": "Cellular Reference Signal Received Quality",
        "unit": "dB",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "RSSI": {
        "name": "Cellular RSSI",
        "unit": "dBm",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "RSRP": {
        "name": "Cellular Reference Signal Received Power",
        "unit": "dBm",
        "icon": "mdi:signal",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "MCC": {
        "name": "Mobile Country Code",
        "unit": None,
        "icon": "mdi:identifier",
        "device_class": None,
        "state_class": None,
    },
    "MNC": {
        "name": "Mobile Network Code",
        "unit": None,
        "icon": "mdi:identifier",
        "device_class": None,
        "state_class": None,
    },
    "RFCN": {
        "name": "RF Channel Number",
        "unit": None,
        "icon": "mdi:radio-tower",
        "device_class": None,
        "state_class": None,
    },
    "CPUUsage": {
        "name": "CPU Usage",
        "unit": "%",
        "icon": "mdi:chip",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },    
    "ProcessNumberOfEntries": {
        "name": "Process Number of Entries",
        "unit": None,
        "icon": "mdi:chip",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },    
    "temperature": {
        "name": "Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "voltage": {
        "name": "Voltage",
        "unit": "V",
        "icon": "mdi:flash",
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    "ErrorsSent": {
        "name": "Errors Sent",
        "unit": "errors",
        "icon": "mdi:alert",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "ErrorsReceived": {
        "name": "Errors Received",
        "unit": "errors",
        "icon": "mdi:alert",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "DiscardPacketsSent": {
        "name": "Discard Packets Sent",
        "unit": "packets",
        "icon": "mdi:alert",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "DiscardPacketsReceived": {
        "name": "Discard Packets Received",
        "unit": "packets",
        "icon": "mdi:alert",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "MulticastPacketsSent": {
        "name": "Multicast Packets Sent",
        "unit": "packets",
        "icon": "mdi:alert",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "MulticastPacketsReceived": {
        "name": "Multicast Packets Received",
        "unit": "packets",
        "icon": "mdi:alert",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "UnicastPacketsSent": {
        "name": "Unicast Packets Sent",
        "unit": "packets",
        "icon": "mdi:alert",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "UnicastPacketsReceived": {
        "name": "Unicast Packets Received",
        "unit": "packets",
        "icon": "mdi:counter",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "UnknownProtoPacketsSent": {
        "name": "Unknown Protocol Packets Sent",
        "unit": "packets",
        "icon": "mdi:counter",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "UnknownProtoPacketsReceived": {
        "name": "Unknown Protocol Packets Received",
        "unit": "packets",
        "icon": "mdi:counter",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "Total": {
        "name": "Total",
        "unit": None,
        "icon": "mdi:counter",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "Free": {
        "name": "Free",
        "unit": None,
        "icon": "mdi:counter",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "UpTime": {
        "name": "Up Time",
        "unit": None,
        "icon": "mdi:counter",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
}


def _flatten_dict(d: dict, parent_key: str = "") -> dict:
    """Flatten a nested dictionary with dot notation for keys."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)


def _is_value_scalar(value: Any) -> bool:
    """Check if a value is a scalar (string, number, bool)."""
    return isinstance(value, (str, int, float, bool)) or value is None


def _device_group_for_key(key: str) -> str | None:
    """Return the first path component, except for router-level device data."""
    group, separator, _ = key.partition(".")
    return group if separator and group and group != "device" else None


def _sensor_config_for_key(key: str) -> dict | None:
    """Return configured sensor metadata for a flattened data key."""
    key_parts = key.split(".")
    sensor_name = key_parts[-1]
    sensor_group = key_parts[-2] if len(key_parts) > 2 else None

    if sensor_name.startswith("X_ZYXEL_"):
        sensor_name = sensor_name[len("X_ZYXEL_") :]

    sensor_config = KNOWN_SENSORS.get(sensor_name)
    if not sensor_config and len(key_parts) > 1:
        sensor_config = KNOWN_TYPES.get(sensor_name)
        if sensor_config:
            sensor_config = dict(sensor_config)
            if sensor_group:
                sensor_config["name"] = f"{sensor_group} {sensor_config['name']}"
    return sensor_config


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Zyxel sensors."""
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

    sensors = []

    # Process all keys in the JSON and create sensors for them
    # We'll use a flat structure for simplicity
    for key, value in flattened_data.items():
        # Skip non-scalar values
        if not _is_value_scalar(value):
            continue

        _LOGGER.debug("Key: %s", key)
        device_group = _device_group_for_key(key)
        sensor_config = _sensor_config_for_key(key)

        if sensor_config:
            if sensor_config.get("type") == "boolean":
                continue
            sensors.append(
                ConfiguredZyxelSensor(
                    coordinator,
                    entry,
                    key,
                    sensor_config,
                    device_group,
                    parent_device_id,
                    parent_area,
                )
            )
        else:
            sensors.append(
                GenericZyxelSensor(
                    coordinator,
                    entry,
                    key,
                    device_group,
                    parent_device_id,
                    parent_area,
                )
            )

    if sensors:
        async_add_entities(sensors)


class AbstractZyxelSensor(ZyxelCoordinatorEntity, SensorEntity):
    """Base class for Zyxel device sensors."""


class ConfiguredZyxelSensor(AbstractZyxelSensor):
    """Representation of a configured Zyxel sensor."""

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        key: str,
        config: dict,
        device_group: str | None = None,
        parent_device_id: str | None = None,
        suggested_area: str | None = None,
    ):
        """Initialize the sensor."""
        super().__init__(
            coordinator, entry, key, device_group, parent_device_id, suggested_area
        )
        self._config = config
        self._attr_name = f"Zyxel {config['name']}"
        self._attr_native_unit_of_measurement = config["unit"]
        self._attr_icon = config["icon"]
        self._attr_device_class = config["device_class"]
        self._attr_state_class = config["state_class"]

    @property
    def state(self):
        """Return the state of the sensor."""
        try:
            return self._get_value_from_path()
        except (KeyError, AttributeError):
            return None


class GenericZyxelSensor(AbstractZyxelSensor):
    """Representation of a generic Zyxel sensor."""

    @property
    def name(self):
        """Return the name of the sensor."""
        name_parts = self._key.split(".")
        if len(name_parts) > 1:
            name_parts = name_parts[1:]
        return f"Zyxel {'.'.join(name_parts)}"

    @property
    def state(self):
        """Return the state of the sensor."""
        try:
            return self._get_value_from_path()
        except (KeyError, AttributeError):
            return None

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:router-wireless"
