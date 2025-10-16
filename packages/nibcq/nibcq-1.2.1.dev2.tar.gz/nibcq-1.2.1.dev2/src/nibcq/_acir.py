"""Defines the ACIR (Alternating Current Internal Resistance) measurement for the nibcq package."""

import cmath
import json
import math
from dataclasses import dataclass
from typing import Tuple, NamedTuple, Optional, Dict, Any, Union, Final

import nidcpower
import numpy as np

from nibcq._device import Device
from nibcq.compensation import Compensation, CompensationFile, CompensationMethod, ImpedanceTable
from nibcq.enums import DeviceFamily, SMUOutputFunction, PowerlineFrequency, InterpolationMode
from nibcq.measurement import (
    ConfigFileSupport,
    Measurement,
    SMUMeasurement,
    SMUResult,
    TestParameters,
)
from nibcq.switch import SMUCellData


@dataclass
class FrequencySet:
    """Configuration for frequency-specific signal generation properties in AC measurements.

    This dataclass encapsulates the signal generation parameters required for a specific
    frequency point in AC impedance measurements. It defines the current amplitude and
    number of measurement periods, which together determine the measurement quality and
    duration for that frequency.

    Attributes:
        current_amplitude (float): The AC current amplitude in Amperes for signal generation.
                          Higher amplitudes provide better signal-to-noise ratio but may
                          stress the DUT. Typical values range from 0.001 to 3.0 A.
        number_of_periods (int): The number of complete AC cycles to measure at this frequency.
                          More periods improve measurement accuracy but increase test time.
                          Typical values range from 1 to 100 periods.

    Example:
        >>> freq_config = FrequencySet(current_amplitude=0.1, number_of_periods=20)
        >>> freq_config.current_amplitude
        0.1
        >>> freq_config.number_of_periods
        20
    """

    current_amplitude: float = None
    number_of_periods: int = None


class DFTFeatures(NamedTuple):
    """Results of Discrete Fourier Transform analysis for AC impedance measurements.

    This named tuple contains the extracted frequency-domain features from DFT analysis
    of voltage and current waveforms. It encapsulates the fundamental frequency component
    and the complex phasors that represent the amplitude and phase relationships between
    voltage and current, which are essential for impedance calculations.

    The phasors contain both magnitude and phase information in complex number format,
    where the magnitude represents the RMS amplitude and the phase represents the
    phase relationship relative to the excitation signal.

    Attributes:
        tone_frequency (float): The fundamental frequency component extracted from the DFT analysis
                       in Hertz. Should match the excitation frequency for proper impedance
                       calculation.
        voltage_phasor (complex): Complex voltage phasor containing amplitude and phase information.
                       The magnitude represents RMS voltage, and the phase represents
                       voltage phase relative to the current excitation.
        current_phasor (complex): Complex current phasor containing amplitude and phase information.
                       The magnitude represents RMS current, and the phase represents
                       current phase relative to the voltage excitation.

    Example:
        >>> features = DFTFeatures(
        ...     tone_frequency=1000.0,
        ...     voltage_phasor=10.0+2.0j,
        ...     current_phasor=0.1+0.02j
        ... )
        >>> impedance = features.voltage_phasor / features.current_phasor
        >>> print(f"Impedance: {abs(impedance):.2f} Ohms at {features.tone_frequency} Hz")
    """

    tone_frequency: float
    voltage_phasor: complex
    current_phasor: complex


@dataclass
class SMUInputParameters:
    """Input parameters for configuring SMU-based AC impedance measurements.

    This dataclass contains all the configuration parameters required to set up
    a Source Measure Unit (SMU) for AC impedance spectroscopy measurements. It
    encompasses voltage and current limits, DC offset settings, signal generation
    characteristics, and compensation method specifications.

    These parameters control both the safety limits of the measurement (voltage/current
    limits) and the signal generation characteristics (frequency sweep, compensation).
    Proper configuration ensures accurate measurements while protecting both the DUT
    and the measurement equipment.

    Attributes:
        voltage_limit_hi (float): Upper voltage limit in Volts for DUT protection. Default 1.8M V
                        (effectively unlimited for most applications).
        voltage_limit_low (float): Lower voltage limit in Volts for DUT protection. Default 1.8M V
                        (effectively unlimited for most applications).
        current_limit (float): Current compliance limit in Amperes to prevent overcurrent.
                        Default 100 µA provides protection for sensitive DUTs.
        dc_offset (float): DC voltage offset applied to the AC signal in Volts. Default 0V
                        means pure AC excitation without DC bias.
        nominal_dut_voltage (float): Expected DUT voltage level in Volts for range optimization.
                        Helps SMU select appropriate measurement ranges.
        output_function (OutputFunction): SMU output mode.
                        Typically DC_CURRENT for impedance measurements,
                        where current is sourced and voltage is measured.
        frequency_sweep_characteristics (dict[float, FrequencySet]):
                        Dictionary mapping frequencies (Hz) to FrequencySet
                        objects containing amplitude and period information.
        compensation_method (CompensationMethod):
                        Error correction method from CompensationMethod enum.
                        NO_COMPENSATION, SHORT, GOLDEN_DUT, or SHORT_GOLDEN_DUT.
        powerline_frequency (PowerlineFrequency): Powerline frequency for noise rejection
                        (50 Hz or 60 Hz). Should match local electrical grid frequency.

    Example:
        >>> params = SMUInputParameters(
        ...     voltage_limit_hi=6.0,
        ...     current_limit=0.001,
        ...     output_function=OutputFunction.DC_CURRENT,
        ...     compensation_method=CompensationMethod.SHORT
        ... )
    """

    voltage_limit_hi: float = 1.8e6  #  1.8M
    voltage_limit_low: float = 1.8e6  #  1.8M
    current_limit: float = 0.0001  #  100u
    dc_offset: float = 0
    nominal_dut_voltage: float = 0
    output_function: SMUOutputFunction = SMUOutputFunction.DC_CURRENT
    frequency_sweep_characteristics: dict[float, FrequencySet] = None
    compensation_method: CompensationMethod = CompensationMethod.NO_COMPENSATION
    powerline_frequency: PowerlineFrequency = PowerlineFrequency.FREQ_60_HZ


@dataclass
class SMUGenerationParameters:
    """Internal parameters calculated for SMU signal generation configuration.

    This dataclass contains the calculated parameters used internally by the ACIR
    measurement system to configure the SMU for signal generation. These parameters
    are derived from the user-specified input parameters and hardware capabilities,
    representing the actual configuration applied to the SMU hardware.

    The parameters in this class are typically calculated during the measurement
    setup phase and are used to configure voltage/current ranges, timing parameters,
    and waveform generation settings for optimal measurement performance.

    Attributes:
        voltage_range (float):
                        Calculated voltage measurement range in Volts. Set before configuration
                        based on voltage limits and expected signal levels.
        current_range (float):
                        Calculated current measurement range in Amperes. Set before configuration
                        based on current limits and signal amplitude.
        configured_frequency (float): The frequency actually configured on the SMU in Hz. May differ
                        slightly from requested frequency due to hardware limitations.
        measured_frequency (float): The actual measured frequency in Hz after signal generation.
                        Only populated after measurement completion.
        sinusoidal_pattern_dt (float):
                        Time step between samples in the generated waveform in seconds.
                        Calculated during configuration based on sample rate.
        effective_sinusoidal_pattern_dt (float):
                        Internal scaling factor used for waveform generation calculations.
        first_period_number_of_samples (int): Number of samples in the first complete period.
                        Calculated during configuration for DFT analysis.
        timeout_value (float):
                        Measurement timeout value in seconds. Calculated based on measurement
                        duration and includes safety margin for hardware settling.
        generated_sinusoidal_waveform (list[float]):
                        List of amplitude values representing the
                        sinusoidal waveform to be generated by the SMU.

    Note:
        This class is used internally by the ACIR measurement system. Users typically
        do not need to interact with these parameters directly.
    """

    voltage_range: float = None  # Set before config
    current_range: float = None  # Set before config
    configured_frequency: float = None  # Set seperately
    measured_frequency: float = None  # Only set after measurement
    sinusoidal_pattern_dt: float = None  # Set while config
    effective_sinusoidal_pattern_dt: float = None  # Not used currently
    first_period_number_of_samples: int = None  # Set while config
    timeout_value: float = None  # Set while config
    generated_sinusoidal_waveform: list[float] = None  # Set while config - DVR in LabVIEW


@dataclass
class SMUMeasurementParameters:
    """Internal parameters for SMU measurement acquisition configuration.

    This dataclass contains the calculated parameters used to configure the SMU
    for data acquisition during AC impedance measurements. These parameters control
    the timing, sampling, and data collection aspects of the measurement process.

    The parameters are derived from the measurement requirements and hardware
    capabilities, ensuring optimal data quality while maintaining measurement
    speed and accuracy. They define how the SMU will acquire voltage and current
    data during the AC excitation signal.

    Attributes:
        effective_sample_rate (float): The actual sample rate achieved by the SMU in samples/second.
                        May differ from requested rate due to hardware limitations.
        number_of_samples (int): Total number of samples to acquire during the measurement.
                        Calculated based on frequency, periods, and sample rate.
        actual_measurement_record_dt (float):
                        Actual time step between measurement samples in seconds.
                        Inverse of effective_sample_rate.
        aperture_time (float): Integration time for each measurement sample in seconds.
                        Affects measurement noise and speed tradeoff.
        sample_rate (float): Requested sample rate in samples/second before hardware adjustment.
        dut_voltage (list[float]): List of measured voltage values per channel in Volts.
                        Populated during measurement execution.
        dut_temperature (list[float]): List of measured temperature values per channel in Celsius.
                        Populated during measurement if temperature monitoring is enabled.

    Note:
        This class is used internally by the ACIR measurement system for configuring
        data acquisition parameters. Users typically do not interact with these
        parameters directly.
    """

    effective_sample_rate: float = None
    number_of_samples: int = None
    actual_measurement_record_dt: float = None
    aperture_time: float = None
    sample_rate: float = None
    dut_voltage: list[float] = None  # Per Channel
    dut_temperature: list[float] = None  # Per Channel


@dataclass
class ACIRTestParameters(TestParameters, ConfigFileSupport):
    """Configuration parameters for Alternating Current Internal Resistance (ACIR) measurements.

    This class extends the base TestParameters to provide ACIR-specific configuration
    options for single-frequency AC impedance measurements. ACIR measurements characterize
    the complex impedance of a Device Under Test (DUT) at a specific frequency using
    sinusoidal current excitation and voltage measurement.

    These parameters control the measurement conditions including voltage limits for
    safety, signal amplitude for signal-to-noise ratio optimization, measurement
    duration for accuracy, and error compensation methods for systematic error correction.

    Attributes:
        nominal_voltage (float):
                            Expected DUT voltage level in Volts for measurement range optimization.
                            Default 4.0V is typical for battery cells and electrochemical systems.
        voltage_limit_hi (float): Upper voltage limit in Volts for DUT protection. Default 5.0V
                            provides safety margin for most applications.
        current_amplitude (float): AC current amplitude in Amperes for excitation signal.
                            Default 1.0A provides good signal levels but may need adjustment
                            based on DUT characteristics and desired measurement conditions.
        number_of_periods (int): Number of complete AC cycles to measure for averaging and
                            noise reduction. Default 20 periods provides good balance
                            between accuracy and measurement speed.
        compensation_method (CompensationMethod):
                            Error correction method from CompensationMethod enum.
                            Options include NO_COMPENSATION, SHORT, GOLDEN_DUT, or
                            SHORT_GOLDEN_DUT for systematic error correction.

    Example:
        >>> params = ACIRTestParameters(
        ...     nominal_voltage=3.7,
        ...     voltage_limit_hi=4.2,
        ...     current_amplitude=0.1,
        ...     number_of_periods=50,
        ...     compensation_method=CompensationMethod.SHORT
        ... )
    """

    nominal_voltage: float = 4.0
    voltage_limit_hi: float = 5.0
    current_amplitude: float = 1.0
    number_of_periods: int = 20
    compensation_method: CompensationMethod = CompensationMethod.NO_COMPENSATION

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "ACIRTestParameters":
        """Create ACIRTestParameters instance from JSON dictionary.

        Args:
            json_data (Dict[str, Any]): Dictionary containing ACIR configuration data.

        Returns:
            ACIRTestParameters: Instance configured from JSON data

        Raises:
            ValueError: If required parameters are missing or invalid
            KeyError: If expected keys are not found in json_data
        """
        # Parse powerline frequency
        powerline_freq_value = json_data.get("Power Line Frequency", 60)
        if powerline_freq_value == 50:
            powerline_freq = PowerlineFrequency.FREQ_50_HZ
        elif powerline_freq_value == 60:
            powerline_freq = PowerlineFrequency.FREQ_60_HZ
        else:
            raise ValueError(f"Unsupported powerline frequency: {powerline_freq_value}")

        # Parse compensation method
        comp_method_str = json_data.get("Compensation Method", "No Compensation")
        if comp_method_str == "No Compensation":
            comp_method = CompensationMethod.NO_COMPENSATION
        elif comp_method_str == "Short":
            comp_method = CompensationMethod.SHORT
        elif comp_method_str == "Golden DUT":
            comp_method = CompensationMethod.GOLDEN_DUT
        elif comp_method_str == "Short-Golden DUT":
            comp_method = CompensationMethod.SHORT_GOLDEN_DUT
        else:
            raise ValueError(f"Unsupported compensation method: {comp_method_str}")

        return cls(
            nominal_voltage=json_data.get("Nominal DUT Voltage (V)", 4.0),
            voltage_limit_hi=json_data.get("Voltage Limit Hi (V)", 5.0),
            current_amplitude=json_data.get("Current Amplitude (A)", 1.0),
            number_of_periods=json_data.get("Number of Periods", 20),
            compensation_method=comp_method,
            powerline_frequency=powerline_freq,
        )

    @classmethod
    def from_file(cls, file_path: str) -> "ACIRTestParameters":
        """Create ACIRTestParameters instance from JSON configuration file.

        Args:
            file_path (str): Path to JSON configuration file

        Returns:
            ACIRTestParameters: Instance configured from file

        Raises:
            FileNotFoundError: If configuration file is not found
            ValueError: If file content is invalid or required parameters are missing
            json.JSONDecodeError: If file contains invalid JSON
        """
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        return cls.from_json(json_data)


class ACIR(Measurement):
    """Alternating Current Internal Resistance (ACIR) measurement handler class.

    This class implements single-frequency AC impedance spectroscopy measurements using
    a Source Measure Unit (SMU). ACIR measurements characterize the complex impedance
    of electrochemical systems, batteries, and other devices by applying a sinusoidal
    current excitation and measuring the resulting voltage response.

    The class handles the complete measurement workflow including signal generation,
    data acquisition, DFT analysis for impedance calculation, and error compensation.
    It provides a foundation for more complex measurements like EIS (Electrochemical
    Impedance Spectroscopy) which extends ACIR for frequency sweeps.

    ACIR measurements are fundamental in battery testing, electrochemical analysis,
    and material characterization where understanding the frequency-dependent
    impedance behavior is crucial for system performance evaluation.

    Example:
        >>> # Configure measurement parameters
        >>> params = ACIRTestParameters(
        ...     current_amplitude=0.1,
        ...     number_of_periods=20,
        ...     compensation_method=CompensationMethod.SHORT
        ... )
        >>>
        >>> device = Device.connect("PXIe-4139")
        >>> acir = ACIR(device, test_frequency=1000.0, test_parameters=params)
        >>>
        >>> # Run measurement at 1000 Hz
        >>> compensation = Compensation()
        >>> result = acir.run(compensation=compensation)
        >>> print(f"Impedance: {abs(result.impedance):.2f} Ohms")
    """

    DEVICE_FAMILY: Final[DeviceFamily] = DeviceFamily.SMU
    """DeviceFamily: Device family for ACIR and similar measurement types."""

    FREQUENCY_LIMIT: Final[float] = 10000.0
    """float: Frequency limit for ACIR and similar measurement types."""

    CURRENT_LIMIT: Final[float] = 2.0
    """float: Current limit for ACIR and similar measurement types."""

    def __init__(
        self,
        device: Device,
        test_parameters: ACIRTestParameters,
        test_frequency: float = 1000,
    ):
        """Initialize the ACIR measurement with the instrument device.

        Args:
            device (Device): The device instance to use for measurements
            test_parameters (ACIRTestParameters): The test parameters for the measurement
            test_frequency (float): The frequency in Hz at which to run the ACIR measurement
                Must be within the supported range (0 to FREQUENCY_LIMIT).

        Raises:
            ValueError: If device is None or invalid
            RuntimeError: If device initialization fails

        Examples:
            >>> device = Device.connect(DeviceFamily.SMU, "PXIe-4139")
            >>> params = ACIRTestParameters()
            >>> acir = ACIR(device, params)
        """
        super().__init__(device=device, test_parameters=test_parameters)
        # Initialize internal parameter fields
        self._generation_input_parameters = SMUInputParameters()
        self._generation_input_parameters.frequency_sweep_characteristics = {}
        self._calculated_generation_parameters = SMUGenerationParameters()
        self._calculated_generation_parameters.generated_sinusoidal_waveform = []
        self._calculated_measurement_parameters = SMUMeasurementParameters()
        self._calculated_measurement_parameters.dut_voltage = []
        self._calculated_measurement_parameters.dut_temperature = []
        self._raw_measurement_data = SMUMeasurement()
        self._result = SMUResult()
        # Initialize input parameters
        self.current_frequency = test_frequency
        self.test_parameters = test_parameters

    # Overwrite test_parameters as the class specific subtype of ConfigParameters.
    @property
    def test_parameters(self) -> ACIRTestParameters:
        """Get the test parameters for ACIR measurement.

        Returns:
            ACIRTestParameters: The current test parameters configuration

        Raises:
            ValueError: If test parameters have not been set
        """
        return self._test_parameters

    @test_parameters.setter
    def test_parameters(self, value: ACIRTestParameters):
        """Set the test parameters for an ACIR measurement.

        Implementation made for the ACIR Measurement process.
        Make sure frequency is supported, then update all private parameters too.
        Set this before calling run!

        Args:
            value (ACIRTestParameters): The new configuration parameters to base the update
                process on

        Raises:
            ValueError: If frequency is not set before setting test parameters
            TypeError: If value is not an ACIRTestParameters instance
        """
        if self.current_frequency is None:
            raise ValueError("Frequency must be set before setting test parameters.")

        # Set Test Parameters field
        self._test_parameters = value

        # Also set the other, private parameters, so config can have only the device-configuration.
        # --- SET GENERATION INPUT PARAMETERS ---
        # Part of "Obtain Test Parameters" on LabVIEW API
        self._generation_input_parameters = SMUInputParameters(
            voltage_limit_hi=value.voltage_limit_hi,
            # Changed from LabVIEW Code.
            # There it not gets set, and the upper limit's negated gets used automatically.
            voltage_limit_low=-1.0 * value.voltage_limit_hi,
            current_limit=2.0,  # Maximum supported current measurement, not used in LabVIEW API.
            dc_offset=0,  # No offset is set in LabVIEW API.
            nominal_dut_voltage=value.nominal_voltage,
            output_function=SMUOutputFunction.DC_CURRENT,  # Fix Value
            frequency_sweep_characteristics={
                self.current_frequency: FrequencySet(
                    current_amplitude=value.current_amplitude,
                    number_of_periods=value.number_of_periods,
                )
            },
            compensation_method=value.compensation_method,
            powerline_frequency=value.powerline_frequency,
        )

    @property
    def current_frequency(self) -> float:
        """Get the current frequency of the ACIR Measurement.

        Returns:
            float: The current configured frequency in Hz

        Raises:
            ValueError: If frequency has not been set
        """
        return self._calculated_generation_parameters.configured_frequency

    @current_frequency.setter
    def current_frequency(self, value: float):
        """Set the current frequency of the ACIR Measurement.

        Allows a value from 0.0 to maximum (10k Hz), including the limit values.
        0.0 frequency means a constant DC value.

        Args:
            value (float): The frequency in Hz to set for the measurement

        Raises:
            ValueError: If frequency is outside the supported range (0.0 to FREQUENCY_LIMIT)
            TypeError: If value is not a number
        """
        if 0.0 <= value <= ACIR.FREQUENCY_LIMIT:
            # Update the value to run on,
            self._calculated_generation_parameters.configured_frequency = value
            # Move the already set targets to the new frequency,
            # BUT ONLY IF there is a value present already
            if len(self._generation_input_parameters.frequency_sweep_characteristics) > 0:
                _, set = self._generation_input_parameters.frequency_sweep_characteristics.popitem()
                self._generation_input_parameters.frequency_sweep_characteristics[value] = set
        else:
            raise ValueError(
                f"{value} Hz frequency is out of bounds. "
                f"Frequency should be between {0} and {ACIR.FREQUENCY_LIMIT} Hz."
            )

    @property
    def result(
        self,
    ) -> Union[SMUResult, list[tuple[SMUCellData, SMUResult]]]:
        """Get the result of the last ACIR measurement.

        Returns the measurement result from the most recent measurement operation.
        The result type depends on whether switching was used or not.

        Returns:
            SMUResult | list[tuple[SMUCellData, SMUResult]]: The measurement result(s).
                For switching measurements, returns a list of tuples where each tuple contains
                the cell data and its corresponding results.

        Raises:
            RuntimeError: If no measurement has been performed yet or if
                the result is not available
        """
        if not self._result:
            raise RuntimeError("No measurement value available!")
        return self._result

    def generate_compensation_file_path(self) -> str:
        """Generate compensation file path using current compensation method setting.

        Returns:
            str: The generated file path for compensation data, or None if no compensation
                is needed

        Raises:
            NotImplementedError: If compensation_method is not supported by nibcq Python API
            ValueError: If test parameters are not set
        """
        # Raise error if parameters not set.
        compensation_method = self._test_parameters.compensation_method

        # Check if compensation method is supported by the nibcq Python API
        if compensation_method == CompensationMethod.NO_COMPENSATION:
            return None
        elif compensation_method not in (CompensationMethod.SHORT, CompensationMethod.GOLDEN_DUT):
            raise NotImplementedError(
                f"Compensation method '{compensation_method.value}' is not supported by the "
                f"nibcq Python API. Supported methods are: {CompensationMethod.SHORT.value}, "
                f"{CompensationMethod.GOLDEN_DUT.value}, {CompensationMethod.NO_COMPENSATION.value}"
            )

        # Use the existing generate_file_path function but replace the default path with custom path
        return CompensationFile.generate_file_path(
            compensation_method,
            self.device.full_serial_number,
        )

    @property
    def measurement_data(self) -> SMUMeasurement:
        """Get the processed measurement data used for impedance calculations.

        Only allows measurement to be read, not access it directly.
        For frequencies > 60 Hz, sanitizes data by removing edge effects.
        Applies DC offset removal to ensure measurements start and end near zero.

        Returns:
            SMUMeasurement: Sanitized measurement data containing tone frequency, voltage
                values, and current values

        Raises:
            ValueError: If no measurement data is available or measurement is incomplete
        """
        if not (
            self._raw_measurement_data.tone_frequency
            and self._raw_measurement_data.current_values
            and self._raw_measurement_data.voltage_values
        ):
            raise ValueError("No measurement is available.")
        # Sanitize data if necessary
        voltage_measurements = self._raw_measurement_data.voltage_values
        current_measurements = self._raw_measurement_data.current_values

        # Remove parts of the signal that are affected by edge effects
        # Still leaves a long line at the end in high frequencies because of source freq mismatch.
        number_of_periods = self._generation_input_parameters.frequency_sweep_characteristics[
            self.current_frequency
        ].number_of_periods
        if self.current_frequency > 60 and number_of_periods > 10:
            first_period = self._calculated_generation_parameters.first_period_number_of_samples - 1
            voltage_measurements = self._raw_measurement_data.voltage_values[
                2 * first_period :  # -1 * first_period
            ]
            current_measurements = self._raw_measurement_data.current_values[
                2 * first_period :  # -1 * first_period
            ]

        # Apply DC offset removal to ensure measurements center around zero
        # This compensates for any DC drift or offset in the measurement system
        # Currently skip it because of weird stuff happening with the end if signal
        if voltage_measurements:
            voltage_mean = sum(voltage_measurements) / len(voltage_measurements)
            voltage_measurements = [v - voltage_mean for v in voltage_measurements]

        if current_measurements:
            current_mean = sum(current_measurements) / len(current_measurements)
            current_measurements = [i - current_mean for i in current_measurements]

        return SMUMeasurement(
            tone_frequency=self._raw_measurement_data.tone_frequency,
            voltage_values=voltage_measurements,
            current_values=current_measurements,
        )

    @property
    def raw_data(self) -> SMUMeasurement:
        """Get the raw measurement data read from the device.

        Only allows measurement to be read, not access it directly.
        Returns unprocessed data as captured from the device.

        Returns:
            SMUMeasurement: Raw measurement data containing tone frequency, voltage values,
                and current values

        Raises:
            ValueError: If no measurement data is available or measurement is incomplete
        """
        if not (
            self._raw_measurement_data.tone_frequency
            and self._raw_measurement_data.current_values
            and self._raw_measurement_data.voltage_values
        ):
            raise ValueError("No measurement is available.")
        return self._raw_measurement_data

    @staticmethod
    def validate_current_amplitude(current_amplitude: float) -> bool:
        """Validate that the current amplitude is within acceptable limits."""
        if not (0 < current_amplitude <= ACIR.CURRENT_LIMIT):
            raise ValueError(
                f"{current_amplitude} Amperes is out of bounds. "
                f"Current amplitude should be greater than 0 and up to {ACIR.CURRENT_LIMIT} Amperes."
            )
        return True

    def _determine_current_level_range(self) -> int:
        """Determine the appropriate current level range based on actual amplitude.

        Uses current ranges to determine the appropriate current level range.
        This is required to properly set the current level ranges on the SMU to existing ranges.

        Currently, this is a PXIe-4139 specific implementation.

        Returns:
            int: The appropriate current level range (0.1, 1, or 3 Amperes)

        Raises:
            ValueError: If current amplitude is not set in test parameters
            AttributeError: If frequency sweep characteristics are not initialized
        """
        # List of (max_current, current_level) tuples in ascending order
        current_ranges = [
            (0.1, 0.1),
            (1, 1),
            (3, 3),
        ]

        # Find the appropriate sample rate by checking which range the frequency falls into
        for curr_step, current_level in current_ranges:
            if (
                self._generation_input_parameters.frequency_sweep_characteristics[
                    self.current_frequency
                ].current_amplitude
                <= curr_step  # The logic defines to always get the next level range after we pass one
            ):
                return current_level

        # This should never be reached due to the float('inf') case, but just in case
        # TODO: This could give an error already if the set current is over 3 (it will fail later)
        return 3

    def _determine_sample_rate(self) -> int:
        """Determine the appropriate sample rate based on frequency.

        Uses frequency ranges to determine the appropriate sample rate.
        Returns the sample rate for the frequency range that is closest to the input frequency.

        Currently, this is a PXIe-4139 specific implementation.

        Returns:
            int: The appropriate sample rate in Hz (100 to 80000 Hz)

        Raises:
            ValueError: If current frequency is not set
            AttributeError: If frequency configuration is missing
        """
        # List of (frequency_threshold, sample_rate) tuples in ascending order
        frequency_ranges = [
            (0.01, 100),
            (0.1, 1000),
            (1, 10000),
            (100, 20000),
            (200, 40000),
            (400, 80000),
        ]

        # For frequencies above the highest threshold, return the maximum sample rate
        if self.current_frequency >= 400:
            return frequency_ranges[len(frequency_ranges) - 1][1]

        # Find the closest frequency threshold
        min_distance = float("inf")
        closest_sample_rate = frequency_ranges[len(frequency_ranges) - 1][1]
        for freq_threshold, sample_rate in frequency_ranges:
            distance = abs(self.current_frequency - freq_threshold)
            if distance < min_distance:
                min_distance = distance
                closest_sample_rate = sample_rate
            if distance > min_distance:
                break

        return closest_sample_rate

    def _determine_voltage_limit_range(self):
        """Determine the appropriate voltage level range based on voltage limit.

        Uses a simple logic to limit the voltage on 6V or 60V.
        This is required to properly set the voltage level ranges on the SMU.

        Currently, this is a PXIe-4139 specific implementation.

        Returns:
            int: The appropriate voltage range (6 or 60 Volts)

        Raises:
            ValueError: If voltage_limit_hi is not set in generation input parameters
            AttributeError: If generation input parameters are not initialized
        """
        return 60 if self._generation_input_parameters.voltage_limit_hi > 6 else 6

    def _calculate_number_of_samples(self) -> Tuple[float, float]:
        """Calculate total samples and samples in the first period for a sine waveform measurement.

        These represent the number of discrete samples for a sine waveform based on
        measurement cycles, sample rate, and frequency.

        The first period contains the first complete cycle.
        The total samples are calculated based on the number of cycles.

        Returns:
            Tuple[float, float]: A tuple containing (total_samples, samples_in_first_period)

        Raises:
            MemoryError: If total samples exceed 15,000,000 (PXIe-4139 limit)
            ValueError: If sample rate or frequency is not set
            ZeroDivisionError: If current frequency is zero
        """
        samples_in_first_period = int(
            (self._calculated_measurement_parameters.sample_rate / self.current_frequency) + 1
        )
        total_samples = int(
            (
                self._calculated_measurement_parameters.sample_rate
                * self._generation_input_parameters.frequency_sweep_characteristics[
                    self.current_frequency
                ].number_of_periods
                / self.current_frequency
            )
            + 1
        )

        # This is a PXIe-4139 specific implementation
        if total_samples >= 15000000:
            raise MemoryError(
                f"Too many periods have been selected for frequency {self.current_frequency} [Hz]."
                " Lower the number of periods!"
            )
        return total_samples, samples_in_first_period

    def _generate_waveform(self):
        """Generate a list of floats representing a sine waveform.

        Waveform Generation: sin(2*pi*frequency*time)
        Time here is a list of discrete points in time, so it becomes n(index)/sample_rate

        This maintains the exact requested frequency for accurate impedance measurements.
        The SMU reset after measurement ensures clean state between measurements.

        Returns:
            list[float]: A list of amplitude values representing the sinusoidal waveform

        Raises:
            ValueError: If frequency sweep characteristics or sample rate are not set
            ZeroDivisionError: If sample rate is zero
            AttributeError: If required parameters are not initialized
        """
        # If the value is non-zero
        if 0 < self.current_frequency <= ACIR.FREQUENCY_LIMIT:
            # Use the original frequency-based formula to maintain frequency accuracy
            return [
                self._generation_input_parameters.frequency_sweep_characteristics[
                    self.current_frequency
                ].current_amplitude
                * math.sin(
                    2
                    * math.pi
                    * self.current_frequency
                    * n
                    / self._calculated_measurement_parameters.sample_rate
                )
                for n in range(self._calculated_measurement_parameters.number_of_samples)
            ]
        # If the frequency is zero, create a basic DC signal
        elif self.current_frequency == 0.0:
            return [
                self._generation_input_parameters.frequency_sweep_characteristics[
                    self.current_frequency
                ].current_amplitude
                for n in range(self._calculated_measurement_parameters.number_of_samples)
            ]
        # Raise error if frequency is somehow out of bounds.
        raise ValueError(
            f"This should never happen, but it clearly has! Welcome to the twilight zone."
            f"Triggered Error: {self.current_frequency} Hz frequency is out of bounds. "
            f"Frequency should be between {0} and {ACIR.FREQUENCY_LIMIT} Hz."
        )

    def _delta_to_seconds(self, delta) -> float:
        """Convert delta (timedelta or numeric seconds) to float seconds.

        Args:
            delta (float | int | "datetime.timedelta"):
                A timedelta-like object or numeric seconds value to convert to
                float seconds.

        Returns:
            float: Seconds as a float value.

        Raises:
            TypeError: If delta is not convertible to seconds.
        """
        if delta is None:
            raise TypeError("delta is None")
        if hasattr(delta, "total_seconds"):  # timedelta-like
            return float(delta.total_seconds())
        try:  # numeric-like (float or int)
            return float(delta)
        except Exception as exc:
            raise TypeError("delta must be timedelta or numeric seconds") from exc

    def _build_terminal_name(self, channel_name: int | str, local_terminal_name: str) -> str:
        """Build a terminal name string for device configuration.

        Args:
            channel_name (int | str): The channel identifier (typically an integer).
            local_terminal_name (str): The local terminal name string.

        Returns:
            str: A formatted terminal name string for device configuration.

        Raises:
            RuntimeError: If device is not initialized.
            AttributeError: If device session is not available.
        """
        if not self.device:
            raise RuntimeError("Device is not initialized.")
        return (
            "/"
            + self.device.session.io_resource_descriptor
            + "/Engine"
            + str(channel_name)
            + "/"
            + str(local_terminal_name)
        )

    def _configure(self):
        """Configure the hardware device for ACIR measurement.

        This method expects the config_parameters (including self.frequency) to already be set.
        Configures SMU parameters, signal generation, and measurement settings.

        Raises:
            ValueError: If measurement cannot run without set frequency or test parameters
            RuntimeError: If SMU parameter setup fails or voltage/current limits are incorrect
            nidcpower.errors.DriverError: If device configuration fails
        """
        # Raise error if parameters not set.
        if self.current_frequency is None:
            raise ValueError("Measurement cannot run without a set current waveform frequency.")

        # Before configuring any device, validate current amplitude for each frequency.
        for _, data in self._generation_input_parameters.frequency_sweep_characteristics.items():
            ACIR.validate_current_amplitude(data.current_amplitude)

        # --- DETERMINE VALUES NEEDED FOR DEVICE PARAMETERS SET ---
        # Calculate waveform generation parameters and set them step by step
        gen_params = self._calculated_generation_parameters
        mes_params = self._calculated_measurement_parameters
        # Sample Rate - Needed for all other
        mes_params.sample_rate = self._determine_sample_rate()
        # Number of Samples - Needed for waveform
        total_samples, first_period_samples = self._calculate_number_of_samples()
        mes_params.number_of_samples = total_samples
        gen_params.first_period_number_of_samples = first_period_samples
        # Timing releated variables - Uses sample rate, not needded for other
        mes_params.aperture_time = 1.0 / mes_params.sample_rate
        gen_params.sinusoidal_pattern_dt = 1.0 / mes_params.sample_rate
        gen_params.timeout_value = mes_params.number_of_samples / mes_params.sample_rate + 1
        # Generate waveform
        gen_params.generated_sinusoidal_waveform = self._generate_waveform()
        # Set ranges
        self._calculated_generation_parameters.voltage_range = self._determine_voltage_limit_range()
        self._calculated_generation_parameters.current_range = self._determine_current_level_range()

        # --- SMU PARAMETER SETUP ---
        # Try to set up SMU with the values provided
        # Set up Signal Measurement first.
        sess = self.device.session
        sess.measure_when = nidcpower.MeasureWhen.ON_MEASURE_TRIGGER  # FIX
        sess.aperture_time_units = nidcpower.ApertureTimeUnits.SECONDS  # FIX
        sess.measure_record_length = self._calculated_measurement_parameters.number_of_samples
        sess.aperture_time = self._calculated_measurement_parameters.aperture_time
        sess.power_line_frequency = self.test_parameters.powerline_frequency.value
        sess.sense = nidcpower.Sense.REMOTE  # FIX
        sess.dc_noise_rejection = nidcpower.DCNoiseRejection.NORMAL  # FIX
        sess.digital_edge_measure_trigger_input_terminal = self._build_terminal_name(
            channel_name=0, local_terminal_name="SourceCompleteEvent"
        )
        sess.measure_trigger_type = nidcpower.TriggerType.DIGITAL_EDGE  # FIX
        # no property found for Triggers:Measure Trigger:Digital Edge:Edge. It should be RISING
        sess.measure_complete_event_delay = 0  # FIX

        # Set Sequence before setting up generation, so sequence mode can be set!
        sess.set_sequence(
            values=self._calculated_generation_parameters.generated_sinusoidal_waveform,
            source_delays=[
                0 for i in range(self._calculated_measurement_parameters.number_of_samples)
            ],
        )

        # Set up Signal Generation.
        sess.output_function = self._generation_input_parameters.output_function.value
        sess.source_mode = nidcpower.SourceMode.SEQUENCE  # FIX
        sess.current_limit_autorange = False  # FIX
        sess.transient_response = nidcpower.TransientResponse.NORMAL  # FIX FOR 10K
        sess.current_level_range = self._calculated_generation_parameters.current_range
        sess.voltage_limit = self._generation_input_parameters.voltage_limit_hi
        sess.voltage_limit_range = self._calculated_generation_parameters.voltage_range
        sess.source_delay = 0  # FIX
        sess.output_resistance = 1000  # FIX
        sess.sequence_step_delta_time_enabled = True  # FIX
        sess.sequence_step_delta_time = self._calculated_generation_parameters.sinusoidal_pattern_dt

        # --- READY MEASURE ---
        # Commit config
        sess.commit()
        # Connect output if it is already not connected.
        if not sess.output_connected:
            sess.output_connected = True
        # Retrieve SMU Config - normalize to float seconds immediately
        raw_delta_time = self._delta_to_seconds(sess.measure_record_delta_time)
        self._calculated_measurement_parameters.actual_measurement_record_dt = raw_delta_time
        self._calculated_measurement_parameters.number_of_samples = sess.measure_record_length

        # Check if current and voltage is between limits
        voltage_high_okay = (
            self._calculated_generation_parameters.voltage_range == sess.voltage_limit_high
        )
        voltage_low_okay = (
            self._calculated_generation_parameters.voltage_range * -1 == sess.voltage_limit_low
        )
        current_okay = self._determine_current_level_range() == sess.current_level_range
        if not (voltage_high_okay and voltage_low_okay and current_okay):
            # TODO: CHANGE TO CORRECT ERROR
            raise ValueError("SMU Parameter problem - Incorrect Voltage or current limit.")
        return

    def _calculate_parabolic_interpolation_with_sinc_correction(
        self,
        bin_order_sign: int,
        before_bin: float,
        middle_bin: float,
        after_bin: float,
        true_middle_index: int,
    ) -> tuple[float, float]:
        """Calculate parabolic interpolation with sinc correction for FFT peak analysis.

        Performs the LabVIEW 3-bin parabolic interpolation algorithm followed by sinc
        correction for amplitude adjustment. This handles the BinOrderSign logic and
        applies the appropriate mathematical corrections.

        Args:
            bin_order_sign (int): Sign describing bin order used for interpolation
                (0 = before>after, 1 = before==after, 2 = before<after).
            before_bin (float): Magnitude of the bin before the peak.
            middle_bin (float): Magnitude of the peak bin.
            after_bin (float): Magnitude of the bin after the peak.
            true_middle_index (int): The absolute index of the middle bin in the spectrum.

        Returns:
            tuple[float, float]: (estimated_tone_bin, corrected_amplitude)
                - estimated_tone_bin: The interpolated bin position with sub-bin accuracy
                - corrected_amplitude: The amplitude corrected with sinc interpolation

        Raises:
            RuntimeError: If interpolation or sinc correction fails
            ZeroDivisionError: If division by zero occurs during calculations
            ValueError: If bin order sign is invalid
        """
        if middle_bin == 0:
            raise RuntimeError("Peak amplitude is zero - invalid measurement")

        try:
            match bin_order_sign:
                case 0:  # before_bin > after_bin
                    if before_bin == 0:
                        raise ZeroDivisionError("Before bin is zero during interpolation")
                    bin_diff = middle_bin / before_bin
                    tone_bin_offset = (bin_diff - 2) / (bin_diff + 1)
                case 1:  # before_bin == after_bin
                    tone_bin_offset = 0.0
                case 2:  # before_bin < after_bin
                    if after_bin == 0:
                        raise ZeroDivisionError("After bin is zero during interpolation")
                    bin_diff = middle_bin / after_bin
                    tone_bin_offset = (2 - bin_diff) / (bin_diff + 1)
                case _:  # Invalid case
                    raise ValueError(f"Invalid order sign: {bin_order_sign}")
        except (ZeroDivisionError, OverflowError) as e:
            raise RuntimeError(f"Interpolation failed: {e}")

        estimated_tone_bin = tone_bin_offset + true_middle_index

        # Sinc correction for amplitude (LabVIEW CorrectedToneAmplitude)
        try:
            sinc_correction = (1 - tone_bin_offset**2) / np.sinc(tone_bin_offset)
            corrected_tone_amplitude = middle_bin * sinc_correction

            if not np.isfinite(corrected_tone_amplitude) or corrected_tone_amplitude <= 0:
                raise RuntimeError("Sinc correction produced invalid amplitude")
        except (ZeroDivisionError, OverflowError) as e:
            raise RuntimeError(f"Sinc correction failed: {e}")

        return estimated_tone_bin, corrected_tone_amplitude

    def _extract_single_tone_information(
        self,
        target_frequency: float,
        search_percentage: float,
        measurements: list[float],
        delta_t: float,
    ) -> tuple[float, float, float]:
        """Extract single tone frequency, amplitude, and phase from measurement data.

        Implements the LabVIEW "Get Single Tone Information (1 Channel)" algorithm with
        complete FFT processing, aliasing correction, and 3-bin interpolation.

        Args:
            target_frequency (float): The expected frequency to search around in Hz.
            search_percentage (float): The search range as a percentage
                (e.g., 5.0 for ±5%).
            measurements (list[float]): List of measurement values (voltage or current
                samples) to analyze.
            delta_t (float | int | "datetime.timedelta"):
                The actual measurement delta time in seconds, or a timedelta-like
                object.

        Returns:
            tuple[float, float, float]: (detected_frequency, detected_amplitude, detected_phase)
                - detected_frequency: The extracted tone frequency in Hz
                - detected_amplitude: The detected amplitude (RMS equivalent)
                - detected_phase: The detected phase in degrees

        Raises:
            ValueError: If input data is invalid or search parameters are out of range
            RuntimeError: If tone detection fails or produces invalid results
        """
        # Input validation
        if not measurements:
            raise ValueError("Measurements cannot be empty")
        # measurements = measurements[:-1]

        # Accept timedelta or numeric seconds
        delta_seconds = self._delta_to_seconds(delta_t)
        if delta_seconds <= 0:
            raise ZeroDivisionError("Delta time must be greater than zero")
        if search_percentage < 0:
            raise ValueError("Search percentage must be non-negative")

        total_samples = len(measurements)
        if total_samples < 4:
            raise ValueError("Signal must contain at least 4 samples for proper FFT analysis")

        actual_sample_rate = 1.0 / delta_seconds

        # Step 1: Convert to numpy arrays and apply Hann window
        signal_array = np.array(measurements, dtype=np.float64)

        # Check for invalid data
        if not np.isfinite(signal_array).all():
            raise ValueError("Input signal contains NaN or infinite values")

        # Apply Hann window (LabVIEW implementation: window scaled for DC, then divided by sqrt(2))
        hann_window = np.hanning(total_samples)
        signal_windowed = signal_array * (hann_window / math.sqrt(2))
        # Prepare data for FFT: Normalize by length/2
        signal_windowed = signal_windowed / (total_samples / 2)

        # Step 2: Compute FFT and create cleaned spectrum
        signal_fft = np.fft.fft(signal_windowed)

        # Step 3: Extract first half + middle value (LabVIEW SubsetLen calculation)
        subset_length = (total_samples + 1) // 2
        signal_magnitudes = signal_fft[:subset_length]
        # Correct first element in the subset
        signal_magnitudes[0] /= math.sqrt(2)

        # Only get the absolute values as the cleared value
        cleared_signal_magnitudes = np.abs(signal_magnitudes)

        # Step 4: DC cleaning. Set the first two bins to zero (LabVIEW CleanedSpectrum behavior)
        cleared_signal_magnitudes[0] = 0.0
        cleared_signal_magnitudes[1] = 0.0

        # Step 5: Targeted search with 3-bin peak detection
        sample_base = actual_sample_rate / total_samples
        target_bin = target_frequency / sample_base
        search_length_raw = max(int(total_samples * 0.01 * search_percentage), 1)

        # Cap search length to prevent oversized ranges that include DC or harmonics
        # Maximum search length is 25% of target_bin to avoid including DC region
        # Also limit to maximum of 50 bins to prevent excessive search ranges
        max_search_based_on_frequency = max(int(target_bin * 0.25), 5)  # At least 5 bins
        max_search_absolute = 50  # Maximum 50 bins
        search_length = min(search_length_raw, max_search_based_on_frequency, max_search_absolute)

        # Calculate search range around target_bin
        target_bin_int = int(round(target_bin))
        start_index = max(target_bin_int - search_length, 1)
        end_index = min(target_bin_int + search_length + 1, len(cleared_signal_magnitudes) - 1)

        if start_index >= end_index:
            raise RuntimeError("Search range is too narrow for frequency detection")

        # Optional plotting goes here when required. Not part of release code.

        # Find peak in search region
        search_region = cleared_signal_magnitudes[start_index:end_index]
        if len(search_region) == 0:
            raise RuntimeError("No valid search region for peak detection")

        middle_bin_local_index = np.argmax(search_region)
        true_middle_index = start_index + middle_bin_local_index

        # Ensure we have neighbors for 3-bin interpolation
        if true_middle_index <= 0 or true_middle_index >= len(cleared_signal_magnitudes) - 1:
            raise RuntimeError("Peak is at spectrum boundary - cannot perform 3-bin interpolation")

        # Step 6: Extract 3 bins for parabolic interpolation
        before_bin = cleared_signal_magnitudes[true_middle_index - 1]
        middle_bin = cleared_signal_magnitudes[true_middle_index]
        after_bin = cleared_signal_magnitudes[true_middle_index + 1]

        # Step 7-8: Parabolic interpolation and sinc correction
        bin_order_sign = np.sign(after_bin - before_bin) + 1
        estimated_tone_bin, corrected_tone_amplitude = (
            self._calculate_parabolic_interpolation_with_sinc_correction(
                bin_order_sign=bin_order_sign,
                before_bin=before_bin,
                middle_bin=middle_bin,
                after_bin=after_bin,
                true_middle_index=true_middle_index,
            )
        )

        # Step 9: Aliasing correction around DC and Fs/2 (LabVIEW third frame)
        # Preparation phase: Get complex values and tone phase
        estimated_tone_bin_index = int(np.floor(estimated_tone_bin))
        if estimated_tone_bin_index >= len(signal_magnitudes):
            estimated_tone_bin_index = len(signal_magnitudes) - 1

        tone_value_complex = signal_magnitudes[estimated_tone_bin_index]
        tone_value_theta = cmath.phase(tone_value_complex)

        # DC Aliasing correction (4-bin loop around DC) - DISABLED
        for loop_iter in range(4):
            iter_main_index = estimated_tone_bin_index - 1 + loop_iter

            # Ensure we stay within bounds
            if iter_main_index < 0 or iter_main_index >= len(signal_magnitudes):
                continue

            # Calculate sinc for DC aliasing: sin(x)/x where:
            # x = (EstimatedToneBin + IterMainIndex) * π
            sinc_arg_dc = estimated_tone_bin + iter_main_index
            sinc_dc = np.sinc(sinc_arg_dc)
            # Calculate DC aliasing complex correction
            denominator = (estimated_tone_bin + iter_main_index) ** 2 - 1
            if abs(denominator) < 1e-12:
                continue  # Skip if denominator is too small

            dc_magnitude = abs(sinc_dc / denominator) * corrected_tone_amplitude
            dc_phase = -1 * (math.pi + tone_value_theta)
            dc_aliased_complex = cmath.rect(dc_magnitude, dc_phase)

            # Apply correction to spectrum
            signal_magnitudes[iter_main_index] -= dc_aliased_complex

        # Fs/2 Aliasing correction (4-bin loop around Fs/2) - DISABLED
        for loop_iter in range(4):
            iter_main_index = estimated_tone_bin_index - 1 + loop_iter

            # Ensure we stay within bounds
            if iter_main_index < 0 or iter_main_index >= len(signal_magnitudes):
                continue

            # Calculate IndexToValue = IterMainIndex - (FFTSize - EstimatedToneBin)
            index_to_value = iter_main_index - (total_samples - estimated_tone_bin)
            # Calculate sinc for Fs/2 aliasing: sin(y)/y where y = IndexToValue * π
            sinc_fs = np.sinc(index_to_value)
            # Calculate Fs/2 aliasing complex correction
            denominator = index_to_value**2 - 1
            if abs(denominator) < 1e-12:
                continue  # Skip if denominator is too small

            fs_magnitude = abs(sinc_fs / denominator) * corrected_tone_amplitude
            fs_phase = -1 * tone_value_theta
            fs_aliased_complex = cmath.rect(fs_magnitude, fs_phase)

            # Apply correction to spectrum
            signal_magnitudes[iter_main_index] -= fs_aliased_complex

        # Extract original 3-bin values for final interpolation (NO aliasing correction)
        true_after_bin = np.abs(signal_magnitudes[true_middle_index + 1])
        true_before_bin = np.abs(signal_magnitudes[true_middle_index - 1])
        true_middle_bin = np.abs(signal_magnitudes[true_middle_index])
        true_tone_value_complex = signal_magnitudes[estimated_tone_bin_index]
        true_tone_value_theta = cmath.phase(true_tone_value_complex)

        # Step 10: Final calculation with original 3-bin interpolation (NO aliasing correction)
        final_estimated_tone_bin, final_corrected_tone_amplitude = (
            self._calculate_parabolic_interpolation_with_sinc_correction(
                bin_order_sign=bin_order_sign,
                before_bin=true_before_bin,
                middle_bin=true_middle_bin,
                after_bin=true_after_bin,
                true_middle_index=true_middle_index,
            )
        )

        # Calculate final detected values
        detected_frequency = final_estimated_tone_bin * sample_base
        detected_amplitude = final_corrected_tone_amplitude * math.sqrt(2)

        if not np.isfinite(detected_frequency) or detected_frequency <= 0:
            raise RuntimeError("Frequency detection produced invalid result")
        if not np.isfinite(detected_amplitude) or detected_amplitude <= 0:
            raise RuntimeError("Amplitude detection produced invalid result")

        # Step 11: Phase calculation with LabVIEW corrections
        estimation_remainder = final_estimated_tone_bin - 1 * np.floor(final_estimated_tone_bin / 1)
        detected_phase = (
            ((180 / math.pi) * true_tone_value_theta) - (180 * estimation_remainder)
        ) + 90

        # Error handling for phase
        has_phase_error = (
            detected_phase is None
            or not np.isfinite(detected_phase)
            or not isinstance(detected_phase, (int, float))
        )
        if has_phase_error:
            raise RuntimeError("Failed to detect tone phase")

        return detected_frequency, detected_amplitude, detected_phase

    def _calculate_impedance(
        self, voltage_signal: list[float], current_signal: list[float]
    ) -> DFTFeatures:
        """Extract tone features for impedance calculation using LabVIEW-compatible FFT analysis.

        Uses the extracted single tone information method to analyze both voltage and current
        signals separately, then combines the results to create voltage and current phasors
        for impedance calculation.

        Args:
            voltage_signal (list[float]): Real-valued voltage samples from measurement
            current_signal (list[float]): Real-valued current samples from measurement

        Returns:
            DFTFeatures: A named tuple containing extracted FFT analysis features:
                - tone_frequency: The extracted tone frequency in Hz with sub-bin accuracy
                - voltage_phasor: The complex phasor value for voltage measurements
                - current_phasor: The complex phasor value for current measurements

        Raises:
            ValueError: If input signals are empty, have different lengths, or contain invalid data
            ZeroDivisionError: If sample rate is zero or calculation results in division by zero
            AttributeError: If measurement parameters are not properly initialized
            RuntimeError: If FFT analysis fails or produces invalid results
        """
        # Input validation
        if not voltage_signal or not current_signal:
            raise ValueError("Input signals cannot be empty")

        if len(voltage_signal) != len(current_signal):
            raise ValueError("Voltage and current signals must have the same length")

        if (
            not hasattr(self, "_calculated_measurement_parameters")
            or not self._calculated_measurement_parameters
        ):
            raise AttributeError("Measurement parameters are not properly initialized")

        # Use actual hardware timing for better accuracy
        actual_dt = self._calculated_measurement_parameters.actual_measurement_record_dt
        actual_seconds = self._delta_to_seconds(actual_dt)
        if actual_seconds <= 0:
            raise ZeroDivisionError("Sample rate must be greater than zero")

        # Step 1: Extract single tone information from current signal with 5% search range
        # This determines the actual tone frequency present in the measurement
        target_frequency = self.current_frequency

        current_frequency, current_amplitude, current_phase = self._extract_single_tone_information(
            target_frequency=target_frequency,
            search_percentage=5.0,  # ±5% search range for frequency detection
            measurements=current_signal,
            delta_t=actual_seconds,
        )

        # Step 2: Extract single tone information from voltage signal using detected frequency
        # Use 0% search range since we know the exact frequency from current analysis
        voltage_frequency, voltage_amplitude, voltage_phase = self._extract_single_tone_information(
            target_frequency=current_frequency,  # Use detected frequency from current
            search_percentage=0.0,  # No search range - use exact frequency
            measurements=voltage_signal,
            delta_t=actual_seconds,
        )

        # Step 3: Build voltage and current phasors from amplitude and phase
        # Current Phasor Complex parts
        current_phasor_abs = current_amplitude / math.sqrt(2)
        current_phasor_angle = (math.pi / 180) * (current_phase - voltage_phase)
        # Voltage Phasor Complex parts
        voltage_phasor_abs = voltage_amplitude / math.sqrt(2)
        voltage_phasor_angle = 0  # Voltage Phase is arbitrary 0
        # Make the complex values
        current_phasor = cmath.rect(current_phasor_abs, current_phasor_angle)
        voltage_phasor = cmath.rect(voltage_phasor_abs, voltage_phasor_angle)

        # Step 4: Validate phasor results
        if not np.isfinite(voltage_phasor.real) or not np.isfinite(voltage_phasor.imag):
            raise RuntimeError("Voltage phasor calculation produced invalid result")
        if not np.isfinite(current_phasor.real) or not np.isfinite(current_phasor.imag):
            raise RuntimeError("Current phasor calculation produced invalid result")

        # Step 5: Return results in a structured format
        return DFTFeatures(
            tone_frequency=current_frequency,  # Use the detected frequency from current analysis
            voltage_phasor=voltage_phasor,
            current_phasor=current_phasor,
        )

    # Measure back results from the SMU. Implementation of the abstract measure method.
    def _measure(self) -> SMUResult:
        """Perform the ACIR measurement using the configured device and calculate impedance.

        Initiates device measurement, fetches data, processes signals through DFT analysis,
        and calculates impedance phasor from voltage and current measurements.

        Returns:
            SMUResult: A complete measurement result containing frequency, impedance,
                resistance, reactance, magnitude, and phase

        Raises:
            RuntimeError: If device measurement fails or times out
            ValueError: If measurement data is invalid or incomplete
            nidcpower.errors.DriverError: If device communication fails
            ZeroDivisionError: If current phasor is zero during impedance calculation
        """
        # Perform measurements
        self.device.session.initiate()
        self.device.session.wait_for_event(
            event_id=nidcpower.Event.SEQUENCE_ENGINE_DONE,
            timeout=self._calculated_generation_parameters.timeout_value,
        )

        # Get all measurement points
        measurements = self.device.session.fetch_multiple(
            count=self._calculated_measurement_parameters.number_of_samples
        )
        self._raw_measurement_data = SMUMeasurement(
            tone_frequency=self.current_frequency,
            voltage_values=[m.voltage for m in measurements],
            current_values=[m.current for m in measurements],
        )

        # Abort after measurement is fetched
        self.device.session.abort()

        # Calculate Impedance - Use the Sanitized data
        dft_features = self._calculate_impedance(
            voltage_signal=self.measurement_data.voltage_values,
            current_signal=self.measurement_data.current_values,
        )
        # Set Tone Frequency data with the calculated values
        self._raw_measurement_data.tone_frequency = dft_features.tone_frequency
        self._calculated_generation_parameters.measured_frequency = dft_features.tone_frequency

        # Calculate Phasor
        impedance_phasor = dft_features.voltage_phasor / dft_features.current_phasor
        # Package results and return
        return SMUResult(
            measured_frequency=self._raw_measurement_data.tone_frequency,
            impedance=impedance_phasor,
            r=impedance_phasor.real,
            x=impedance_phasor.imag,
            z=abs(impedance_phasor),
            theta=math.degrees(cmath.phase(impedance_phasor)),
        )

    def load_compensation_file(
        self,
        file_path: Optional[str] = None,
    ) -> Compensation:
        """Load compensation file based on compensation method and device serial number.

        Creates and returns a compensation object with the appropriate compensation data.
        For NO_COMPENSATION, creates a default compensation object.
        For other methods, loads compensation data from file.

        Args:
            file_path (Optional[str]): Optional specific file path to read from.
                If None, generates path automatically

        Returns:
            Compensation: The loaded compensation object

        Raises:
            FileNotFoundError: If compensation file is not found and compensation is required
            ValueError: If compensation file is invalid and compensation is required
            NotImplementedError: If compensation method is not supported by the nibcq Python API
        """
        compensation_method = self._test_parameters.compensation_method

        # Determine what path to save, if it was not provided.
        # Also checks if compensation method is supported.
        # Try to create the basic path, to check if the file type is supported.
        base_conv_file_path = self.generate_compensation_file_path()
        # Generate the correct compensation object.
        if base_conv_file_path:
            # If no path was provided use the default one.
            if not file_path:
                file_path = base_conv_file_path
            # Load and return compensation file
            return Compensation.from_file(method=compensation_method, file_path=file_path)
        # Fallback to No Compensation
        return Compensation(compensation_method=CompensationMethod.NO_COMPENSATION)

    def run(self, compensation: Compensation) -> SMUResult:
        """Run the complete ACIR measurement process with the specified parameters.

        Validates temperature if the compensation specifies a target temperature,
        and the device supports temperature measurement.
        Then configures the device, performs the measurement, applies compensation if specified,
        and returns the final impedance results.

        Args:
            compensation (Compensation): The compensation object to use for impedance correction

        Returns:
            SMUResult: A complete measurement result containing compensated impedance data
                including frequency, impedance, resistance, reactance, magnitude, and phase

        Raises:
            ValueError: If test frequency is out of range or parameters are invalid.
            Also raised if temperature validation fails.
            FileNotFoundError: If compensation file is required but not found
            RuntimeError: If device configuration or measurement fails
            NotImplementedError: If unsupported compensation method is specified

        Examples:
            >>> params = ACIRTestParameters()
            >>> acir = ACIR(device, params)
            >>> compensation = acir.load_compensation_file()
            >>> results = acir.run(1000, compensation)
        """
        # Validate temperature if necessary
        if compensation.target_temperature is not None and (
            not math.isnan(compensation.target_temperature.center)
        ):
            # Measure and Validate temperature
            self.validate_temperature(compensation.target_temperature)

        with self.device.session.lock():
            self._configure()
            single_result = self._measure()

            # Apply compensation
            compensated_impedance = compensation.get_compensated_impedance(
                frequency=single_result.measured_frequency,
                measured_impedance=single_result.impedance,
            )

            # Update result with compensated values
            single_result = SMUResult(
                measured_frequency=single_result.measured_frequency,
                impedance=compensated_impedance,
                r=compensated_impedance.real,
                x=compensated_impedance.imag,
                z=abs(compensated_impedance),
                theta=math.degrees(cmath.phase(compensated_impedance)),
            )

            self._result = single_result
            return single_result

    def run_with_switching(self, compensation: Compensation) -> list[tuple[SMUCellData, SMUResult]]:
        """Run ACIR measurements across multiple DUTs using switch matrix configuration.

        This method performs AC impedance measurements on multiple devices under test (DUTs)
        by automatically switching between different channels. It leverages the device's
        switching capability to sequentially connect to each configured DUT, perform the
        ACIR measurement, and collect results for all channels.

        The switching process includes proper debounce timing to ensure stable connections
        before measurements, and automatic disconnection after each measurement to prevent
        interference. This enables efficient multi-DUT testing for battery characterization,
        production testing, or comparative analysis scenarios.

        Args:
            compensation (Compensation): The compensation object containing error correction
                data for impedance accuracy improvement across the measurement frequency.

        Returns:
            list[tuple[SMUCellData, SMUResult]]: A list of tuples mapping each cell to its
                measurement result. Each SMUCellData represents a DUT connection point,
                and SMUResult contains the impedance, resistance, reactance, magnitude,
                and phase measurements for that specific DUT.

        Raises:
            RuntimeError: If switching capability is not enabled (call device.with_switching()
                first) or if no switch channels are configured in the switch matrix.
            ValueError: If test_frequency is out of bounds, test_parameters contain
                invalid values that would cause measurement errors, or if compensation list
                length doesn't match the number of DUTs. Also raised if temperature validation
                fails for any cell.
            Exception: If connection to any DUT fails during switching operations.

        Note:
            This method automatically handles switch timing with debounce delays to ensure
            measurement stability. The end guarantees proper disconnection even
            if exceptions occur during measurement, preventing DUT damage or interference.

        Examples:
            >>> params = ACIRTestParameters()
            >>> acir = ACIR(device, params)
            >>> compensation = acir.load_compensation_file()
            >>> results = acir.run_with_switching(1000, compensation)
        """
        if not self.has_switch_capability:
            raise RuntimeError("Switching not enabled. Call device.with_switching() first.")

        if not self.switch_cells:
            raise RuntimeError("No switch channels configured")

        # Compensation list size validation
        if isinstance(compensation, list):
            if len(compensation) != len(self.switch_cells):
                raise ValueError("Compensation list must match the number of DUTs.")

        results: list[tuple[SMUCellData, SMUResult]] = []

        try:
            for i, cell in enumerate(self.switch_cells):
                self.connect_channel(cell)
                self.wait_for_debounce()
                single_result = self.run(
                    compensation=(
                        compensation[i] if isinstance(compensation, list) else compensation
                    ),
                )
                results.append((cell, single_result))
                self.device.session.reset()
                self.disconnect_all()
        finally:
            self.disconnect_all()
            self._result = results  # Make even partial results available.
        return results

    def _apply_kit_compensation(
        self,
        compensation: Compensation,
        known_impedance_table_file_path: str,
        interpolation_mode: InterpolationMode = InterpolationMode.NEAREST,
    ) -> None:
        """Apply KIT (Known Impedance Table) compensation to all compensation parameters.

        Subtracts the known impedance values from the measured compensation values
        for all frequencies in the compensation parameter list.

        Args:
            compensation (Compensation): The compensation object containing parameters to modify
            known_impedance_table_file_path (str): Path to the KIT file containing
                known impedance values for reference standards
            interpolation_mode (InterpolationMode): The interpolation mode to use when looking up
                KIT values at specific frequencies. Defaults to NEAREST.

        Raises:
            FileNotFoundError: If the KIT file is not found
            ValueError: If the KIT file is invalid or contains no data
        """
        kit_table = ImpedanceTable.from_file(known_impedance_table_file_path)
        for frequency, compensation_value in compensation.compensation_parameters.items():
            kit_value = kit_table.value_at(frequency, interpolation_mode)
            compensation.compensation_parameters[frequency] = compensation_value - kit_value

    def write_compensation_file(
        self,
        compensation_file_path: Optional[str] = None,
        kit_file_path: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> str:
        """Create a compensation file based on the current compensation data.

        Args:
            compensation_file_path (Optional[str]): Optional specific file path to write to.
                If None, generates path automatically.
            kit_file_path (Optional[str]): Optional specific file path to the
                known impedance table. If None, no known impedance table is used.
            comment (Optional[str]): Optional comment to include in the compensation file.
                If None, no comment is included.

        Returns:
            string: The path of the created compensation file.

        Raises:
            ValueError: If test frequency is out of range, parameters are invalid or
                compensation method not supports compensation files.
            FileNotFoundError: If compensation file is required but not found.
            RuntimeError: If device configuration or measurement fails.
            NotImplementedError: If unsupported compensation method is specified.
        """
        # Runs a pseudo measurement and saves the result to a file
        # Determine what path to save, if it was not provided.
        # Try to create the basic path, to check if the file type is supported.
        base_conv_file_path = self.generate_compensation_file_path()
        # If no specific path is provided, use the base path.
        if compensation_file_path is None:
            compensation_file_path = base_conv_file_path

        # Validate compensation method support
        if self.test_parameters.compensation_method == CompensationMethod.NO_COMPENSATION:
            raise ValueError(
                f"You must select a compensation method other than "
                f"{CompensationMethod.NO_COMPENSATION.value} to create a compensation file."
            )

        # Get temperature
        self.measure_temperature()

        # Get Raw Impedance
        with self.device.session.lock():
            self._configure()
            single_result = self._measure()

        # Populate Compensation Data
        compensation = Compensation(
            compensation_method=self.test_parameters.compensation_method,
            compensation_file_path=compensation_file_path,
            target_temperature=self.temperature_range,
            compensation_parameters={self.current_frequency: single_result.impedance},
        )
        # Apply KIT if necessary.
        if self.test_parameters.compensation_method == CompensationMethod.SHORT and kit_file_path:
            self._apply_kit_compensation(compensation, kit_file_path, InterpolationMode.NEAREST)

        # Create Compensation file.
        new_file = CompensationFile.memory_to_file(compensation=compensation, comment=comment)
        new_file.save_to_file(compensation_file_path)

        return compensation_file_path
