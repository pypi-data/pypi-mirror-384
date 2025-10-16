"""Switch control functionality for multiplexer testing in Battery Cell Quality Toolkit.

This module implements the BCQ Switch API for sequential testing of multiple DUTs
using NI switch modules. Supports EIS, ACIR, and OCV measurements with automatic
switching between test jigs.

Supported Equipment:
 - OCV: DMM (PXIe-4081/PXI-4071) + Switch (PXIe-2525 or PXI-2530B)
 - EIS/ACIR: SMU (PXIe-4139) + Source switch (PXIe-2525) + Sense switch (PXI-2530B)

Supported Switch Topologies:
 - 2-Wire 64x1 Mux
 - 2-Wire Dual 32x1 Mux
 - 2-Wire Quad 16x1 Mux (recommended)
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Protocol

import niswitch

from nibcq.enums import DeviceFamily, SwitchDeviceType, SwitchTopology


@dataclass
class SMUCellData:
    """Represents a switch channel connection for a DUT.

    Attributes:
        cell_serial_number (str): Serial number of the cell being the DUT
        source_dut_channel (str): Switch source channel connected to the DUT
        sense_dut_channel (str): Switch sense channel connected to the DUT
        source_device_channel (str): Switch source channel connected to the measurement device
        sense_device_channel (str): Switch sense channel connected to the measurement device
        jig_id (str): ID of the jig being used for the DUT
    """

    cell_serial_number: str
    source_dut_channel: str
    sense_dut_channel: str
    source_device_channel: str
    sense_device_channel: str
    jig_id: str


@dataclass
class SwitchConfiguration:
    """Represents the configuration for the switch system.

    Attributes:
        topology: The switch topology being used (can be SwitchTopology enum or string).
            Only set to string if you know it is a supported topology type for your switch!
        cells: A list of channel connections for the DUTs.
            Can be either a list of SMUCellData objects or a list of strings,
            which are DUT channel names, when the device family is DMM.
    """

    topology: SwitchTopology | str
    cells: List[SMUCellData] | List[str]

    def get_topology_string(self) -> str:
        """Get the topology as a string value.

        Converts the topology setting to its string representation, handling
        both SwitchTopology enum values and raw string values. This is used
        internally to build the full topology string for switch initialization.

        Returns:
            str: The topology string value suitable for switch configuration

        Examples:
            >>> config = SwitchConfiguration(SwitchTopology.SWITCH_2_WIRE_QUAD_16X1_MUX, ["ch0"])
            >>> topology_str = config.get_topology_string()
            >>> print(topology_str)  # "2-Wire Quad 16x1 Mux"
        """
        if isinstance(self.topology, SwitchTopology):
            return self.topology.value
        return self.topology

    @classmethod
    def from_file(cls, config_path: str | Path) -> "SwitchConfiguration":
        """Load switch configuration from a JSON file.

        Reads a JSON configuration file and creates a SwitchConfiguration
        object with the appropriate settings for the switch topology and
        DUT channel mappings. Supports both DMM and SMU configuration formats.

        Args:
            config_path (str or Path): The path to the JSON configuration file.
                Must be a valid file path pointing to a properly formatted
                switch configuration JSON file.

        Returns:
            SwitchConfiguration: A new SwitchConfiguration object populated
                with the configuration data from the file.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
            ValueError: If the file format is not compatible

        Examples:
            >>> config = SwitchConfiguration.from_file("switch_config.json")
            >>> print(f"Loaded {len(config.cells)} DUT channels")
            >>> config = SwitchConfiguration.from_file(Path("config/dmm_switch.json"))
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Switch configuration file not found: {path}")
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_json(data)

    @classmethod
    def from_json(cls, data: dict) -> "SwitchConfiguration":
        """Load switch configuration from a JSON dictionary.

        Creates a SwitchConfiguration object from a dictionary containing
        switch configuration data. Automatically detects whether the
        configuration is for DMM (simple channel list) or SMU (detailed
        cell data) based on the structure of the cells data.

        Args:
            data (dict): The JSON dictionary data containing configuration.
                Must include "Switches Topology" and "Cells" keys with
                appropriate values for the target device family.

        Returns:
            SwitchConfiguration: A new SwitchConfiguration object with:
                - List[str] cells for DMM configurations
                - List[SMUCellData] cells for SMU configurations
                - Topology as SwitchTopology enum if recognized, string otherwise

        Raises:
            KeyError: If required keys are missing from the data dictionary
            ValueError: If the data format is invalid or incompatible

        Examples:
            >>> data = {
            ...     "Switches Topology": "2-Wire Quad 16x1 Mux",
            ...     "Cells": ["ch0", "ch1", "ch2"]
            ... }
            >>> config = SwitchConfiguration.from_json(data)  # DMM format
            >>>
            >>> smu_data = {
            ...     "Switches Topology": "2-Wire Quad 16x1 Mux",
            ...     "Cells": [{"Cell Serial Number": "123", ...}]
            ... }
            >>> config = SwitchConfiguration.from_json(smu_data)  # SMU format
        """
        cells = data.get("Cells") or []
        topology_str = data.get("Switches Topology")

        # Try to match topology string to enum, fallback to string
        topology = cls._parse_topology(topology_str)

        if cells and isinstance(cells[0], str):
            # DMM format: just a list of channel names
            channels = list(cells)
        elif cells and isinstance(cells[0], dict):
            # SMU format: list of dicts
            channels = [
                SMUCellData(
                    cell_serial_number=cell.get("Cell Serial Number", ""),
                    source_dut_channel=cell.get("Source Switch DUT Channel", ""),
                    sense_dut_channel=cell.get("Sense Switch DUT Channel", ""),
                    source_device_channel=cell.get("Source Channel", ""),
                    sense_device_channel=cell.get("Sense Channel", ""),
                    jig_id=cell.get("Jig ID", ""),
                )
                for cell in cells
            ]
        else:
            channels = []
        return cls(
            topology=topology,
            cells=channels,
        )

    @staticmethod
    def _parse_topology(topology_str: str) -> SwitchTopology | str:
        """Parse topology string to SwitchTopology enum if possible.

        Attempts to match the provided topology string to a known SwitchTopology
        enum value. If a match is found, returns the enum; otherwise returns
        the original string for custom or unrecognized topologies.

        Args:
            topology_str (str): The topology string from configuration file
                or user input to parse and validate.

        Returns:
            SwitchTopology | str: SwitchTopology enum if a match is found,
                otherwise returns the original string unchanged.

        Examples:
            >>> result = SwitchConfiguration._parse_topology("2-Wire Quad 16x1 Mux")
            >>> print(type(result))  # <enum 'SwitchTopology'>
            >>> result = SwitchConfiguration._parse_topology("Custom Topology")
            >>> print(type(result))  # <class 'str'>
        """
        if not topology_str:
            return topology_str

        # Try to find matching enum value
        for topology_enum in SwitchTopology:
            if topology_enum.value == topology_str:
                return topology_enum

        # Return original string if no enum match found
        return topology_str


class SwitchCapable(Protocol):
    """Protocol for devices that support switching functionality."""

    def connect_channel(self, cell: str | SMUCellData) -> None:
        """Connect the current device to the specified Cell DUT on the switch."""
        ...

    def disconnect_all(self) -> None:
        """Disconnect all channels on the switch."""
        ...

    def wait_for_debounce(self) -> None:
        """Wait for all the switch relays to settle."""
        ...


class SwitchCapability(ABC, SwitchCapable):
    """Base class for switch control functionality."""

    config: SwitchConfiguration
    _sessions: Dict[str, niswitch.Session]

    def __init__(self, config: SwitchConfiguration = None):
        """Initialize switch capability with configuration file, object, or parameters.

        Args:
            config: SwitchConfiguration object
        """
        self.config: SwitchConfiguration = config
        self._sessions: Dict[str, niswitch.Session] = {}

    def _build_full_topology(self, device_type: SwitchDeviceType) -> str:
        """Build full topology string with device prefix.

        Args:
            device_type: The switch device type

        Returns:
            Full topology string like "2530/2-Wire Quad 16x1 Mux"
        """
        return f"{device_type.value}/{self.config.get_topology_string()}"

    @classmethod
    def create_for_device_family(
        cls,
        device_family: DeviceFamily,
        config: SwitchConfiguration,
    ) -> "SwitchCapability":
        """Factory function to create appropriate switch capability.

        Args:
            device_family: The device family (DMM or SMU)
            config: SwitchConfiguration object

        Returns:
            SwitchCapability instance appropriate for the device family.

        Raises:
            ValueError: If device family is not supported for switching or config is None.
        """
        if not config:
            raise ValueError("Switch Configuration cannot be Empty.")
        if device_family == DeviceFamily.DMM:
            return DmmSwitchCapability(config)
        elif device_family == DeviceFamily.SMU:
            return SmuSwitchCapability(config)
        else:
            raise ValueError(f"Switching not supported for device family: {device_family}")

    @abstractmethod
    def initialize_switches(self) -> None:
        """Initialize switch sessions based on device family requirements."""
        pass

    @abstractmethod
    def connect_channel(self, cell: str | SMUCellData) -> None:
        """Connect the current device to the specified Cell DUT on the switch.

        Args:
            cell: Channel name string or SMUCellData containing connection information
        """
        pass

    def disconnect_all(self) -> None:
        """Disconnect all channels concurrently."""
        for session in self._sessions.values():
            session.disconnect_all()

    def wait_for_debounce(self) -> None:
        """Wait for all the switch relays to settle concurrently."""
        for session in self._sessions.values():
            session.wait_for_debounce()

    def close(self) -> None:
        """Close all switch sessions."""
        for session in self._sessions.values():
            try:
                session.close()
            except Exception:
                pass  # Don't fail on cleanup
        self._sessions.clear()


class DmmSwitchCapability(SwitchCapability):
    """Switch capability for DMM devices (OCV measurements)."""

    device_terminal_channel: str

    def initialize_switches(
        self,
        sense_switch_resource_name: str,
        device_terminal_channel: str,
        sense_device_type: SwitchDeviceType = SwitchDeviceType.PXIe_2530B,
    ) -> None:
        """Initialize single switch session for DMM measurements.

        Args:
            sense_switch_resource_name: The switch resource name connecting the DMM and the Cells.
            device_terminal_channel: The switching channel connected to the device itself.
                This connects the OCV Terminal, the DMM itself, to the switch.
            sense_device_type: The switch device type (defaults to PXIe_2530B)
        """
        if not sense_switch_resource_name:
            raise ValueError("Switch resource not specified")

        # Build full topology with explicit device prefix
        full_topology = self._build_full_topology(sense_device_type)

        # Create single switch session for DMM
        self._sessions["main"] = niswitch.Session(
            resource_name=sense_switch_resource_name, topology=full_topology
        )
        self.device_terminal_channel = device_terminal_channel

    def connect_channel(self, cell: str) -> None:
        """Connect DMM to specific DUT channel.

        Args:
            cell: Channel name for DMM connection
        """
        # For DMM, we expect a simple string channel name
        if isinstance(cell, str):
            self._sessions["main"].connect(cell, self.device_terminal_channel)
        else:
            raise ValueError(
                "DMM switch capability expects a string channel name, but got something else."
            )


class SmuSwitchCapability(SwitchCapability):
    """Switch capability for SMU devices (EIS/ACIR measurements)."""

    def initialize_switches(
        self,
        source_switch_resource_name: str,
        sense_switch_resource_name: str,
        source_device_type: SwitchDeviceType = SwitchDeviceType.PXI_2525,
        sense_device_type: SwitchDeviceType = SwitchDeviceType.PXIe_2530B,
    ) -> None:
        """Initialize source and sense switch sessions for SMU measurements.

        Args:
            source_switch_resource_name: Resource name for source switch
            sense_switch_resource_name: Resource name for sense switch
            source_device_type: Switch device type for source (defaults to PXI_2525)
            sense_device_type: Switch device type for sense (defaults to PXIe_2530B)
        """
        if not source_switch_resource_name or not sense_switch_resource_name:
            raise ValueError("Both source and sense switch resources must be specified")

        # Build full topology with explicit device prefixes
        source_topology = self._build_full_topology(source_device_type)
        sense_topology = self._build_full_topology(sense_device_type)

        # Create source switch session
        self._sessions["source"] = niswitch.Session(
            resource_name=source_switch_resource_name,
            topology=source_topology,
        )

        # Create sense switch session
        self._sessions["sense"] = niswitch.Session(
            resource_name=sense_switch_resource_name,
            topology=sense_topology,
        )

    def connect_channel(self, cell: SMUCellData) -> None:
        """Connect SMU source and sense to specific DUT channel.

        Args:
            cell: SMUCellData containing connection information
        """
        # Connect both source and sense switches sequentially
        self._sessions["source"].connect(cell.source_dut_channel, cell.source_device_channel)
        self._sessions["sense"].connect(cell.sense_dut_channel, cell.sense_device_channel)


# Mixin for measurement classes that support switching
class SwitchAware(SwitchCapable):
    """Mixin to add switching capability access to measurement classes.

    This class provides a simple interface for measurements that need access
    to switching functionality. It delegates to the device's switch capability
    if available, similar to how TemperatureAware works.
    """

    def __init__(self):
        """The SwitchAware is a mixin for measurement classes.

        Just provides access to switch capabilities, no further logic is needed.
        """
        pass

    @property
    def has_switch_capability(self) -> bool:
        """Check if the device has switch capability.

        Returns:
            True if switch capability is available, False otherwise
        """
        return hasattr(self.device, "_switch_capability") and self.device._switch_capability

    def connect_channel(self, channel: SMUCellData) -> None:
        """Connect to a specific DUT channel using the device's switch capability.

        Args:
            channel: SwitchChannel containing connection information

        Raises:
            RuntimeError: If no switch capability is available
        """
        if not self.has_switch_capability:
            raise RuntimeError("No switch capability available on device")
        self.device._switch_capability.connect_channel(channel)

    def disconnect_all(self) -> None:
        """Disconnect all channels using the device's switch capability.

        Raises:
            RuntimeError: If no switch capability is available
        """
        if not self.has_switch_capability:
            raise RuntimeError("No switch capability available on device")
        self.device._switch_capability.disconnect_all()

    def wait_for_debounce(self) -> None:
        """Wait for switch relays to settle using the device's switch capability.

        Raises:
            RuntimeError: If no switch capability is available
        """
        if not self.has_switch_capability:
            raise RuntimeError("No switch capability available on device")
        self.device._switch_capability.wait_for_debounce()

    @property
    def switch_cells(self) -> List[str] | List[SMUCellData]:
        """Get the configured switch cells from the device.

        Returns:
            A list of DUT channel names or SMUCellData objects,
            which contain the DUT and switch channel information.
        """
        if self.device._switch_capability and self.device._switch_capability.config:
            return self.device._switch_capability.config.cells
        return []
