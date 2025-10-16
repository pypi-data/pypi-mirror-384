"""This module defines the Hardware class for handling different hardware configurations."""

import os
from typing import Optional

import nidcpower
import nidmm

from .constants import TOOLKIT_FOLDER_PATH
from .enums import DeviceFamily, SwitchDeviceType
from .switch import (
    SwitchCapability,
    SwitchConfiguration,
    DmmSwitchCapability,
    SmuSwitchCapability,
)
from .temperature import TemperatureCapability, ThermocoupleSettings


class Device:
    """Class to represent and manage hardware device configurations.

    Handles connection and communication with National Instruments measurement devices
    including Digital Multimeters (DMM) and Source Measure Units (SMU). Provides
    device validation, session management, and hardware abstraction for measurement
    operations.

    Attributes:
        session (nidmm.Session | nidcpower.Session): The active session object for
            communication with the hardware device.
    """

    session: nidmm.Session | nidcpower.Session

    SUPPORTED_DMM_LIST = [
        # DMM
        "NI PXI-4071",
        "NI PXIe-4081",
    ]
    SUPPORTED_SMU_LIST = [
        # SMU
        "NI PXIe-4139",
        "NI PXIe-4139 (40W)",
    ]
    SUPPORTED_ELOAD_LIST = [
        # Electronic Load
        "NI PXIe-4051",
    ]

    def __init__(self, device_family: DeviceFamily):
        """Initialize the Device with the specified device family.

        Creates a new Device instance by defining what device family it is under.
        The device is not connected until connect() is called.

        Args:
            device_family (DeviceFamily): The type of device (DMM or SMU) to connect to.
                Must be a valid DeviceFamily enum value.

        Examples:
            >>> device = Device(DeviceFamily.SMU)
            >>> device = Device(DeviceFamily.DMM)
            >>> device.connect("PXI1Slot2")  # Connect after creation
        """
        # Using a generalized session calling. This makes it necessarry to pass the session.
        self._device_family = device_family
        self.session = None
        # Officially Open session
        self._is_closed = True
        # Read and set product type, check for support
        self._product = None
        # Fix serial number formatting to ensure leading zeros are preserved
        self._raw_serial_number = "0"

        # Initialize optional capabilities
        self._temperature_capability: Optional[TemperatureCapability] = None
        self._switch_capability: Optional[SwitchCapability] = None

    @property
    def product(self) -> str:
        """Get the product model name of the connected device.

        Returns the instrument model string as reported by the device driver.
        This is typically the full product name including manufacturer and model number.

        Returns:
            str: The product model name (e.g., "NI PXIe-4139", "NI PXI-4071")

        Examples:
            >>> device = Device.create(DeviceFamily.SMU, "PXI1Slot2")
            >>> print(device.product)
            "NI PXIe-4139"
        """
        return self._product

    @property
    def serial_number(self) -> str:
        """Get the device serial number in raw format without leading zeros.

        Returns the serial number as reported directly by the device driver,
        without any formatting modifications. For simulated devices, this
        typically returns "0".

        Returns:
            str: The raw serial number without leading zero padding

        Examples:
            >>> device = Device.create(DeviceFamily.SMU, "PXI1Slot2")
            >>> print(device.serial_number)
            "12345678"  # or "0" for simulated devices
        """
        return self._raw_serial_number

    @property
    def device_family(self) -> DeviceFamily:
        """Get the device family type of the connected device.

        Returns the DeviceFamily enum value indicating whether this device
        is a Digital Multimeter (DMM) or Source Measure Unit (SMU). This
        information is useful for determining available functionality and
        measurement capabilities.

        Returns:
            DeviceFamily: The device family enum (DeviceFamily.DMM or DeviceFamily.SMU)

        Examples:
            >>> device = Device.create(DeviceFamily.SMU, "PXI1Slot2")
            >>> print(device.device_family)
            DeviceFamily.SMU
            >>> if device.device_family == DeviceFamily.SMU:
            ...     print("This is a Source Measure Unit")
        """
        return self._device_family

    @property
    def full_serial_number(self) -> str:
        """Get the device serial number formatted with leading zeros.

        Returns the serial number padded to 8 characters with leading zeros
        for consistency with file naming conventions and device identification.
        For simulated devices (serial number "0"), returns "0" without padding.

        Returns:
            str: The serial number padded to 8 characters with leading zeros,
                or "0" for simulated devices

        Examples:
            >>> device = Device.create(DeviceFamily.SMU, "PXI1Slot2")
            >>> print(device.full_serial_number)
            "12345678"  # Raw: "12345678"
            >>> print(device.full_serial_number)
            "00001234"  # Raw: "1234"
            >>> print(device.full_serial_number)
            "0"         # Raw: "0" (simulated)
        """
        # For NI instruments, serial numbers are typically 8 characters
        # Pad with leading zeros if shorter
        serial_num = "0"
        if self._raw_serial_number != "0":
            serial_num = self._raw_serial_number.zfill(8)
        return serial_num

    @property
    def is_closed(self):
        """Get the current session state of the device.

        Returns whether the device session has been closed. A closed device
        cannot be used for measurements and must be reconnected to resume operation.
        This property is useful for session management and resource cleanup.

        Returns:
            bool: True if the device session is closed, False if active

        Examples:
            >>> device = Device.create(DeviceFamily.SMU, "PXI1Slot2")
            >>> print(device.is_closed)
            False
            >>> device.close()
            >>> print(device.is_closed)
            True
        """
        return self._is_closed

    @staticmethod
    def is_supported(
        device_type: DeviceFamily,
        device_to_check: str = None,
    ) -> bool:
        """Check if a device product type is supported by the nibcq package.

        Validates whether the specified device model is included in the list
        of supported instruments for the given device family. This is used
        during device initialization to ensure compatibility.

        Args:
            device_type (DeviceFamily): The device family to check against
                (DeviceFamily.DMM or DeviceFamily.SMU).
            device_to_check (str, optional): The product model name to validate.
                Should match the instrument_model string from the device driver.

        Returns:
            bool: True if the device is supported, False otherwise

        Raises:
            ValueError: If device_type is not a valid DeviceFamily enum value

        Examples:
            >>> Device.is_supported(DeviceFamily.SMU, "NI PXIe-4139")
            True
            >>> Device.is_supported(DeviceFamily.DMM, "NI PXI-4071")
            True
            >>> Device.is_supported(DeviceFamily.SMU, "Unsupported Model")
            False
        """
        if device_type is DeviceFamily.DMM:
            return device_to_check in Device.SUPPORTED_DMM_LIST
        elif device_type is DeviceFamily.SMU:
            return device_to_check in Device.SUPPORTED_SMU_LIST
        elif device_type is DeviceFamily.ELOAD:
            return device_to_check in Device.SUPPORTED_ELOAD_LIST
        else:
            raise ValueError(
                f"Unsupported device and type combo: {device_to_check} is not a supported {device_type.name}!"
            )

    def connect(self, resource_name: str, options: str = ""):
        """Connect this device instance to actual hardware.

        Establishes a session with the specified hardware instrument. This instance
        method allows you to create a device object first and then connect it later.

        Args:
            resource_name (str): The VISA resource name of the device to connect to.
                Example: "PXI1Slot2" or "Dev1".
            options (str, optional): Additional connection options for the VISA session.
                Defaults to empty string for standard connection.

        Returns:
            Device: Self (for method chaining)

        Raises:
            RuntimeError: If connection to the device fails or device already connected
            ValueError: If the device is not supported
            nidmm.errors.DriverError: If DMM-specific driver errors occur
            nidcpower.errors.DriverError: If SMU-specific driver errors occur

        Examples:
            >>> device = Device(DeviceFamily.SMU)
            >>> device.connect("PXI1Slot2")
            >>> # Or with method chaining:
            >>> device = Device(DeviceFamily.SMU).connect("PXI1Slot2")
        """
        if self.session is not None:
            raise RuntimeError("Device is already connected!")

        try:
            self.session = self._device_family.value.Session(
                resource_name=resource_name, options=options
            )
        # TODO: Use correct exceptions
        except nidmm.Error as dmmerror:
            raise RuntimeError(
                f"Something went wrong while connecting to {resource_name} DMM Instrument. Error: {dmmerror}."
            )
        except nidcpower.Error as smuerror:
            raise RuntimeError(
                f"Something went wrong while connecting to {resource_name} SMU Instrument. Error: {smuerror}."
            )

        if not self.session:
            raise RuntimeError("Cannot use an empty instrument handler!")
        # Officially Open session
        self._is_closed = False
        # Read and set product type, check for support
        self._product = self.session.instrument_model
        if not Device.is_supported(device_type=self._device_family, device_to_check=self.product):
            # TODO Change RuntimeError to Unsupported Instrument Error.
            raise RuntimeError(f"Unsupported {self._device_family.name} hardware: {self.product}")
        # Fix serial number formatting to ensure leading zeros are preserved
        self._raw_serial_number = self.session.serial_number
        return self

    @classmethod
    def create(cls, device_family: DeviceFamily, resource_name: str, options: str = ""):
        """Create a new Device instance and connect it to hardware in one step.

        Alternative constructor that provides a convenient interface for
        creating and connecting devices in a single call. This is equivalent
        to calling Device(device_family).connect(resource_name, options).

        Args:
            device_family (DeviceFamily): The type of device (DMM or SMU) to connect to.
                Must be a valid DeviceFamily enum value.
            resource_name (str): The VISA resource name of the device to connect to.
                Example: "PXI1Slot2" or "Dev1".
            options (str, optional): Additional connection options for the VISA session.
                Defaults to empty string for standard connection.

        Returns:
            Device: A new Device instance connected to the specified instrument

        Raises:
            RuntimeError: If connection to the device fails
            ValueError: If the device is not supported
            nidmm.errors.DriverError: If DMM-specific driver errors occur
            nidcpower.errors.DriverError: If SMU-specific driver errors occur

        Examples:
            >>> device = Device.create(DeviceFamily.SMU, "PXI1Slot2")
            >>> device = Device.create(DeviceFamily.DMM, "Dev1", "Simulate=1")
        """
        return cls(device_family).connect(resource_name, options)

    def close(self):
        """Close the device session and release hardware resources.

        Properly terminates the connection to the device and marks the session
        as closed. After calling this method, the device cannot be used for
        measurements until a new connection is established. This method should
        be called when finished with the device to ensure proper resource cleanup.

        Raises:
            nidmm.errors.DriverError: If DMM-specific errors occur during closure
            nidcpower.errors.DriverError: If SMU-specific errors occur during closure

        Examples:
            >>> device = Device.create(DeviceFamily.SMU, "PXI1Slot2")
            >>> # ... perform measurements ...
            >>> device.close()
            >>> print(device.is_closed)
            True
        """
        # Close temperature capability if present
        if self._temperature_capability:
            self._temperature_capability._close_thermocouple()
            self._temperature_capability = None

        # Close switch capability if present
        if self._switch_capability:
            self._switch_capability.close()
            self._switch_capability = None

        # Close main device session
        self.session.reset()
        if self.device_family == DeviceFamily.SMU:
            self.session.output_enabled = False
            self.session.output_connected = False
        self.session.close()
        self._is_closed = True

    # ================================
    # Handling of Context Manager
    # ================================

    def __enter__(self):
        """Enter the runtime context for use with 'with' statements.

        Enables the Device class to be used as a context manager, allowing
        automatic resource management through Python's 'with' statement.
        The device session will be automatically closed when exiting the
        context, even if an exception occurs.

        Returns:
            Device: The Device instance for use within the context

        Examples:
            >>> with Device.create(DeviceFamily.SMU, "PXI1Slot2") as device:
            ...     # Use device for measurements
            ...     result = device.session.measure()
            # Device is automatically closed here
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context and ensure proper resource cleanup.

        Automatically closes the device session when exiting a 'with' statement
        context. This ensures that hardware resources are properly released
        regardless of whether the context was exited normally or due to an exception.

        Args:
            exc_type: The exception type if an exception occurred, None otherwise
            exc_value: The exception instance if an exception occurred, None otherwise
            traceback: The traceback object if an exception occurred, None otherwise

        Returns:
            bool: False to allow any exception that occurred to propagate normally

        Examples:
            >>> with Device(DeviceFamily.SMU, "PXI1Slot2") as device:
            ...     raise ValueError("Something went wrong")
            # Device is still properly closed despite the exception
        """
        if not self._is_closed:
            self.close()
        # Return None (or False) to propagate any exception that occurred
        return False

    # ================================
    # Handling Device Self Calibration
    # ================================

    @property
    def default_calibration_path(self):
        """Get the default calibration file path for the connected device.

        Generates the default calibration diary file path based on the device's
        full serial number and the toolkit folder structure. This path is used
        when no specific calibration file path is provided during initialization.

        Returns:
            str: The default calibration file path in the format:
                {TOOLKIT_FOLDER}/Calibration/{serial_number}_calibration_log.csv

        Raises:
            RuntimeError: If the device is not initialized

        Examples:
            >>> measurement = Measurement(device)
            >>> print(measurement.default_calibration_path)
            "/path/to/toolkit/Calibration/12345678_calibration_log.csv"
        """
        base_path = os.path.join(
            TOOLKIT_FOLDER_PATH,
            "Calibration",
            str(self.full_serial_number)
            # TODO: Add this back when bug releated to this is reported.
            # + "_"
            # + Calibration.ProcessType.OCV.value
            + "_calibration_log.csv",
        )
        return base_path

    # ====================================
    # Optional Feature Life Cycle Handling
    # ====================================

    def with_temperature(self, thermocouple_settings: ThermocoupleSettings):
        """Add temperature measurement capability to this device.

        Args:
            thermocouple_settings: Configuration for the thermocouple measurement

        Returns:
            This device instance for method chaining

        Examples:
            >>> from nibcq.temperature import ThermocoupleSettings
            >>> settings = ThermocoupleSettings("Dev1/ai0")
            >>> device = Device.create(DeviceFamily.SMU, "PXI1Slot2").with_temperature(settings)
        """
        self._temperature_capability = TemperatureCapability()
        self._temperature_capability.setup_thermocouple(thermocouple_settings)
        return self

    def with_switching(
        self,
        config: "SwitchConfiguration",
        sense_switch_resource_name: str,
        source_switch_resource_name: Optional[str] = None,
        dmm_terminal_channel: Optional[str] = None,
        dmm_switch_type: Optional[SwitchDeviceType] = None,
    ):
        """Add switching capability to this device.

        Enables multiplexer switching functionality for sequential testing of multiple DUTs.
        The device will support automatic channel switching based on the switch configuration.

        Args:
            sense_switch_resource_name (str): The resource name of the sense switch.
                This is a VISA resource name.
                Defining this is manditory. In case of a DMM device, this defines the
                main switch, and in case of SMU devices, this is connected to the terminal
                responsible for sensing back the source signal impact.
            source_switch_resource_name (Optional[str]): The resource name of the source switch.
                This is a VISA resource name.
                It is optional, as only SMU Devices require a source switch.
                This is the switch connected to the source terminal of the SMU.
            dmm_terminal_channel (Optional[str]):
                The terminal channel connecting the switch to the DMM.
            dmm_switch_type (Optional[str]):
                The type of the switch being connected to the DMM.
            config (SwitchConfiguration):
                The switch configuration object containing topology,
                channel definitions, and DUT information.

        Returns:
            This device instance for method chaining

        Raises:
            ValueError: If switching is not supported for this device family
                or it was incorrectly set up.
            FileNotFoundError: If configuration file doesn't exist

        Examples:
            >>> device = Device.create(DeviceFamily.DMM, "Dev1").with_switching(
            ...     "switch_config.json"
            ... )
            >>> device = Device.create(DeviceFamily.SMU, "PXI1Slot2").with_switching(
            ...     "smu_switch.json"
            ... )
        """
        self._switch_capability = SwitchCapability.create_for_device_family(
            self.device_family,
            config,
        )
        if isinstance(self._switch_capability, DmmSwitchCapability):
            # Validate if correct type was made.
            if not self._device_family == DeviceFamily.DMM:
                raise ValueError("Incompatible switch capability for DMM device.")
            # Keep the default DMM switch type if not provided
            if not dmm_switch_type:
                dmm_switch_type = SwitchDeviceType.PXIe_2530B
            # Initialize the main switch session for DMM; pass the sense switch
            # resource name correctly (examples use `sense_switch_resource_name`).
            self._switch_capability.initialize_switches(
                sense_switch_resource_name=sense_switch_resource_name,
                device_terminal_channel=dmm_terminal_channel,
                sense_device_type=dmm_switch_type,
            )
        elif isinstance(self._switch_capability, SmuSwitchCapability):
            # Validate if correct type was made.
            if not self._device_family == DeviceFamily.SMU:
                raise ValueError("Incompatible switch capability for SMU device.")
            # Initialitze both switches' sessions, which handles the connections.
            self._switch_capability.initialize_switches(
                source_switch_resource_name=source_switch_resource_name,
                sense_switch_resource_name=sense_switch_resource_name,
            )
        return self
