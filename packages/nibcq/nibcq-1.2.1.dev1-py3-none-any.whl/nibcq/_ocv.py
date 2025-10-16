"""Handles the OCV process for the NIBCQ project."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Union, Final

import nidmm

from nibcq._device import Device
from nibcq.enums import DeviceFamily, DMMRange, PowerlineFrequency
from nibcq.measurement import Measurement, TestParameters, ConfigFileSupport


@dataclass
class OCVTestParameters(TestParameters, ConfigFileSupport):
    """Configuration parameters for Open Circuit Voltage (OCV) measurements.

    This class extends the base TestParameters to provide DMM-specific configuration
    options for precision DC voltage measurements. OCV measurements are fundamental
    in battery testing and electrochemical analysis where accurate voltage
    measurement without load is critical for state-of-charge determination and
    system health assessment.

    The parameters control measurement accuracy, speed, and noise rejection
    characteristics of the Digital Multimeter (DMM) used for OCV measurements.
    Proper configuration balances measurement precision with acquisition speed
    based on application requirements.

    Attributes:
        range: DMM voltage measurement range from DMMRange enum. Should be selected
               to provide adequate resolution while avoiding saturation. Common
               ranges include DC_10V for battery cells, DC_1000V for high-voltage
               systems. Auto-ranging is typically avoided for highest precision.
        aperture_time: Integration time per measurement in powerline cycles.
               Longer aperture times improve noise rejection and measurement
               stability but increase acquisition time. Values of 1-10 cycles
               are typical for most applications.
        number_of_averages: Number of internal measurements to average for each
                          reported result. Higher values improve measurement
                          precision by reducing random noise but increase
                          total measurement time. Values of 1-100 are common.
        adc_calibration: Enable/disable internal ADC calibration before measurement.
                        When enabled, improves measurement accuracy by correcting
                        for internal reference drift, but adds measurement time.
                        Recommended for highest precision applications.

    Example:
        >>> params = OCVTestParameters(
        ...     range=DMMRange.DC_10V,
        ...     aperture_time=1.0,
        ...     number_of_averages=10,
        ...     adc_calibration=True
        ... )
        >>> # Configuration optimized for precision battery voltage measurement
    """

    range: DMMRange = DMMRange.DC_10V
    aperture_time: float = 1.0
    number_of_averages: int = 1
    adc_calibration: bool = False

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "OCVTestParameters":
        """Create OCVTestParameters instance from JSON dictionary.

        Args:
            json_data: Dictionary containing OCV configuration data

        Returns:
            OCVTestParameters: Instance configured from JSON data

        Raises:
            ValueError: If required parameters are missing or invalid
            KeyError: If expected keys are not found in json_data
        """
        # Parse powerline frequency
        powerline_str = json_data.get("Powerline Frequency", "60 Hz")
        if powerline_str == "50 Hz":
            powerline_freq = PowerlineFrequency.FREQ_50_HZ
        elif powerline_str == "60 Hz":
            powerline_freq = PowerlineFrequency.FREQ_60_HZ
        else:
            raise ValueError(f"Unsupported powerline frequency: {powerline_str}")

        # Parse range
        range_value = json_data.get("Range", 10)
        if range_value == 10:
            dmm_range = DMMRange.DC_10V
        elif range_value == 1000:
            dmm_range = DMMRange.DC_1000V
        else:
            raise ValueError(f"Unsupported DMM range: {range_value}")

        return cls(
            range=dmm_range,
            aperture_time=json_data.get("Aperture time (PLCs)", 1.0),
            number_of_averages=json_data.get("Number Of Averages", 1),
            adc_calibration=bool(json_data.get("ADC Calibration", 0)),
            powerline_frequency=powerline_freq,
        )

    @classmethod
    def from_file(cls, file_path: str) -> "OCVTestParameters":
        """Create OCVTestParameters instance from JSON configuration file.

        Args:
            file_path: Path to JSON configuration file

        Returns:
            OCVTestParameters: Instance configured from file

        Raises:
            FileNotFoundError: If configuration file is not found
            ValueError: If file content is invalid or required parameters are missing
            json.JSONDecodeError: If file contains invalid JSON
        """
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        return cls.from_json(json_data)


class OCV(Measurement):
    """Class to handle the Open Circuit Voltage (OCV) process for a given instrument."""

    DEVICE_FAMILY: Final[DeviceFamily] = DeviceFamily.DMM
    """DeviceFamily: Device family for OCV measurements."""

    def __init__(self, device: Device, test_parameters: OCVTestParameters):
        """Initialize the OCV measurement with the specified DMM device.

        Sets up the Open Circuit Voltage measurement process using a Digital
        Multimeter (DMM) device. Inherits from the base Measurement class and
        configures DMM-specific functionality for voltage measurements.

        Args:
            device (Device): The DMM device instance to use for OCV measurements.
                Must be a valid Device object with DeviceFamily.DMM.

        Raises:
            ValueError: If device is None or not a DMM device
            RuntimeError: If device initialization fails
            FileNotFoundError: If specified calibration file path doesn't exist

        Examples:
            >>> dmm_device = Device(DeviceFamily.DMM, "PXI1Slot2")
            >>> ocv = OCV(dmm_device)
            >>> ocv = OCV(dmm_device, "/path/to/calibration.csv")
        """
        super().__init__(device=device, test_parameters=test_parameters)

    # Overwrite config_parameters as the class specific subtype of ConfigParameters.
    @property
    def test_parameters(self) -> OCVTestParameters:
        """Get the current OCV test parameters.

        Returns the OCVTestParameters object containing all configuration settings
        specific to Open Circuit Voltage measurements including DMM range, aperture
        time, averaging settings, and ADC calibration options.

        Returns:
            OCVTestParameters: The current OCV-specific test parameters configuration

        Examples:
            >>> ocv = OCV(device)
            >>> params = ocv.test_parameters
            >>> print(params.range)
            DMMRange.DC_10V
            >>> print(params.aperture_time)
            0.0
        """
        return self._test_parameters

    @test_parameters.setter
    def test_parameters(self, value: OCVTestParameters):
        """Set the OCV test parameters.

        Updates the test parameters with OCV-specific configuration settings.
        These parameters control DMM measurement behavior including voltage range,
        measurement timing, averaging, and calibration settings.

        Args:
            value (OCVTestParameters): The new OCV test parameters containing
                DMM range, aperture time, number of averages, ADC calibration
                setting, and other OCV-specific configuration options.

        Raises:
            TypeError: If value is not an OCVTestParameters instance
            ValueError: If the provided parameters contain invalid values

        Examples:
            >>> params = OCVTestParameters()
            >>> params.range = DMMRange.DC_1000V
            >>> params.aperture_time = 1.0
            >>> params.number_of_averages = 10
            >>> ocv.test_parameters = params
        """
        self._test_parameters = value

    @property
    def dmm_configuration(self):
        """Get the DMM configuration as an alias for test_parameters.

        Provides backward compatibility and clarity by offering an alias
        to the test_parameters property with a name that clearly indicates
        this is DMM-specific configuration. This matches the LabVIEW API
        naming convention.

        Returns:
            OCVTestParameters: The current DMM configuration (same as test_parameters)

        Examples:
            >>> ocv = OCV(device)
            >>> config = ocv.dmm_configuration
            >>> print(config.range)
            DMMRange.DC_10V
        """
        return self.test_parameters

    @property
    def result(
        self,
    ) -> Union[float, list[tuple[str, tuple[datetime, datetime, float]]]]:
        """Get the result of the last OCV measurement.

        Returns the measurement result from the most recent measurement operation.
        The result type depends on whether switching was used or not.

        Returns:
            Union[float, list[tuple[str, tuple[datetime, datetime, float]]]]: The result(s)
                of the last measurement. For switching measurements, returns a list of tuples
                where each tuple contains the cell data and its corresponding results.

        Raises:
            RuntimeError: If no measurement has been performed yet or if
                the result is not available
        """
        if not self._result:
            raise RuntimeError("No measurement value available!")
        return self._result

    # Define the abstract configure method, for DMM especially.
    def _configure(self):
        """Configures the DMM Parameters and sets them on the hardware side too.

        This method expects the config_parameters to already be set.
        """
        handler = self.device.session
        handler.powerline_freq = self.test_parameters.powerline_frequency.value
        handler.function = nidmm.Function.DC_VOLTS
        handler.resolution_digits = 7.5
        handler.sample_count = 1
        handler.range = self.test_parameters.range.value
        handler.aperture_time_units = nidmm.ApertureTimeUnits.POWER_LINE_CYCLES
        handler.aperture_time = self.test_parameters.aperture_time
        handler.number_of_averages = self.test_parameters.number_of_averages
        handler.auto_zero = nidmm.AutoZero.ON
        handler.adc_calibration = (
            nidmm.ADCCalibration.ON
            if self.test_parameters.adc_calibration
            else nidmm.ADCCalibration.OFF
        )

    # Measure back voltage from the DMM. Implemetation of the abstract measure method.
    def _measure(self):
        """Measure the voltage using the instrument handler."""
        if not self.device:
            raise RuntimeError("Hardware not initialized!")

        # Perform voltage measurements
        self._result = self.device.session.read()

    # Override run, so it also returns the start and end time of the measurement.
    # This is required to propely calculate run-time, and timestamp the measurement.
    def run(self) -> tuple[datetime, datetime, float]:
        """Run the OCV measurement process and return timing and result information.

        Performs a complete Open Circuit Voltage measurement using the configured
        DMM parameters. Returns detailed timing information along with the
        measurement result for proper timestamping and runtime calculation.

        Returns:
            tuple[datetime, datetime, float]: A tuple containing:
                - start_time: Timestamp when measurement started
                - end_time: Timestamp when measurement completed
                - result: The measured voltage value in volts

        Raises:
            RuntimeError: If the device is not initialized or measurement fails
            ValueError: If test_parameters are invalid or incomplete
            nidmm.errors.DriverError: If DMM-specific errors occur during measurement

        Examples:
            >>> params = OCVTestParameters()
            >>> ocv = OCV(device, params)
            >>> start, end, voltage = ocv.run()
            >>> print(f"Measured {voltage}V from {start} to {end}")
        """
        with self.device.session.lock():
            self._configure()
            start_time = datetime.now()
            self._measure()
            end_time = datetime.now()
        return start_time, end_time, self.result

    def run_with_switching(
        self,
    ) -> list[tuple[str, tuple[datetime, datetime, float]]]:
        """Run OCV measurement with automatic switching between DUT channels.

        Performs Open Circuit Voltage measurements on multiple DUTs by automatically
        switching between configured channels. Each measurement includes timing
        information and DUT identification.

        Args:
            test_parameters (OCVTestParameters): The OCV test parameters containing
                DMM range, aperture time, averaging settings, and other configuration
                options for the voltage measurement.

        Returns:
            list[tuple[str, float]]: List of tuples containing (channel_name, voltage_value)
                for each measured channel.

        Raises:
            RuntimeError: If switching is not enabled or no switch channels are configured
            RuntimeError: If the device is not initialized or measurement fails
            ValueError: If test_parameters are invalid or incomplete
            nidmm.errors.DriverError: If DMM-specific errors occur during measurement

        Examples:
            >>> params = OCVTestParameters()
            >>> ocv = OCV(device, params)
            >>> results = ocv.run_with_switching()
            >>> for channel, voltage in results:
            ...     print(f"Channel {channel}: {voltage} V")
        """
        if not self.has_switch_capability:
            raise RuntimeError("Switching not enabled. Call device.with_switching() first.")

        if not self.switch_cells:
            raise RuntimeError("No switch channels configured")

        results: list[tuple[str, tuple[datetime, datetime, float]]] = []

        try:
            for cell in self.switch_cells:
                self.connect_channel(cell)
                self.wait_for_debounce()
                single_result = self.run()
                results.append((cell, single_result))
                self.device.session.reset()
                self.disconnect_all()
        finally:
            self.disconnect_all()

        # Store results in _result for consistent access via result property
        self._result = [(key, value[2]) for key, value in results]
        return results
