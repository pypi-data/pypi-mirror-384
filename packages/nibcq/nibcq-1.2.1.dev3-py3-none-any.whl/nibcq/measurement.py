"""Creates the Measurement main Abstract Base Class for all measurement subclasses."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Union, Protocol, runtime_checkable

from ._device import Device
from .enums import DeviceFamily, PowerlineFrequency
from .switch import SwitchAware, SMUCellData
from .temperature import TemperatureAware


@runtime_checkable
class ConfigFileSupport(Protocol):
    """Protocol for configuration file support in parameter classes.

    This protocol defines the interface that parameter classes should implement
    to support loading configuration from JSON files. Using a protocol allows
    for duck typing while maintaining clear expectations for implementers.

    Classes implementing this protocol can be used with configuration management
    utilities and provide consistent JSON loading behavior across different
    parameter types.
    """

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "ConfigFileSupport":
        """Create instance from JSON dictionary.

        Args:
            json_data: Dictionary containing configuration data parsed from JSON

        Returns:
            Instance of the class implementing this protocol

        Raises:
            ValueError: If required parameters are missing or invalid
            KeyError: If expected keys are not found in json_data
        """
        ...

    @classmethod
    def from_file(cls, file_path: str) -> "ConfigFileSupport":
        """Create instance from JSON configuration file.

        Args:
            file_path: Path to JSON configuration file

        Returns:
            Instance of the class implementing this protocol

        Raises:
            FileNotFoundError: If configuration file is not found
            ValueError: If file content is invalid or required parameters are missing
            json.JSONDecodeError: If file contains invalid JSON
        """
        ...


@dataclass
class TestParameters:
    """Base configuration parameters class for all measurement types.

    This class serves as the foundation for all measurement-specific parameter
    classes in the nibcq framework. It provides common configuration options
    that are needed across different measurement types while allowing
    specialized subclasses to add their own specific parameters.

    The base class primarily handles powerline frequency configuration, which
    is essential for noise rejection in precision measurements. Subclasses
    extend this with measurement-specific parameters like voltage limits,
    current amplitudes, and timing configurations.

    Attributes:
        powerline_frequency: The local powerline frequency for noise rejection.
                           Should be set to match the local electrical grid
                           frequency (50 Hz or 60 Hz) to minimize powerline
                           interference in sensitive measurements.

    Example:
        >>> params = TestParameters()
        >>> params.powerline_frequency = PowerlineFrequency.FREQ_50_HZ
        >>>
        >>> # Typically used as base for specialized parameters
        >>> class CustomTestParameters(TestParameters):
        ...     voltage_limit: float = 5.0
    """

    powerline_frequency: PowerlineFrequency = PowerlineFrequency.FREQ_60_HZ


@dataclass
class SMUMeasurement:
    """Container for raw voltage and current waveform data from SMU measurements.

    This dataclass stores the time-domain measurement data acquired from a Source
    Measure Unit (SMU) during AC impedance measurements. It contains the raw voltage
    and current waveforms along with the frequency information, providing the
    fundamental data needed for impedance calculations via DFT analysis.

    The voltage and current values represent time-series data sampled at regular
    intervals during the AC excitation. This raw data is subsequently processed
    through DFT analysis to extract the impedance characteristics of the DUT.

    Attributes:
        tone_frequency: The excitation frequency in Hz for this measurement.
                       Should match the frequency of the generated AC signal.
        voltage_values: List of measured voltage samples in Volts, sampled at regular
                       time intervals during the AC excitation. Used for DFT analysis
                       to extract voltage phasor information.
        current_values: List of measured current samples in Amperes, sampled at regular
                       time intervals during the AC excitation. Used for DFT analysis
                       to extract current phasor information.

    Example:
        >>> measurement = SMUMeasurement(
        ...     tone_frequency=1000.0,
        ...     voltage_values=[4.0, 4.1, 4.0, 3.9, 4.0],  # Simplified example
        ...     current_values=[0.1, 0.105, 0.1, 0.095, 0.1]
        ... )
        >>> print(f"Measured {len(measurement.voltage_values)} samples "
        ...       f"at {measurement.tone_frequency} Hz")
    """

    tone_frequency: float = None
    voltage_values: list[float] = None
    current_values: list[float] = None


@dataclass
class SMUResult:
    """Container class for SMU impedance measurement results.

    This dataclass encapsulates the complete set of results from a Source Measure
    Unit (SMU) impedance measurement, providing both complex impedance representation
    and derived quantities in multiple formats for convenience and compatibility
    with different analysis tools.

    The results include the fundamental complex impedance value along with
    separated real/imaginary components, magnitude/phase representation, and
    the measured frequency. This comprehensive result set supports various
    analysis workflows and visualization requirements.

    Attributes:
        measured_frequency: The actual frequency measured during the test in Hz.
                          May differ slightly from requested frequency due to
                          hardware limitations or timing constraints.
        impedance: Complex impedance value in Ohms (Z = R + jX format).
                  Primary result containing both magnitude and phase information.
        r: Real part of impedance (resistance) in Ohms. Represents the resistive
           component of the impedance, related to energy dissipation.
        x: Imaginary part of impedance (reactance) in Ohms. Represents the
           reactive component, related to energy storage (positive for inductive,
           negative for capacitive behavior).
        z: Magnitude of impedance in Ohms (abs(Z) = sqrt(R² + X²)).
           Represents the overall impedance magnitude.
        theta: Phase angle of impedance in degrees. Represents the phase
               relationship between voltage and current (positive for inductive,
               negative for capacitive behavior).

    Example:
        >>> result = SMUResult(
        ...     measured_frequency=1000.0,
        ...     impedance=10.0+5.0j,
        ...     r=10.0,
        ...     x=5.0,
        ...     z=11.18,
        ...     theta=26.57
        ... )
        >>> print(f"Impedance: {result.z:.2f} Ohms at {result.theta:.1f} degrees")
    """

    measured_frequency: float = 0.0
    impedance: complex = complex(0.0, 0.0)
    r: float = 0.0
    x: float = 0.0
    z: float = 0.0
    theta: float = 0.0


class Measurement(ABC, SwitchAware, TemperatureAware):
    """Abstract base class for all measurement subclasses.

    This class provides the basic structure and properties for any measurement process.
    You will need to implement the 'configure' and 'measure' methods in subclasses.
    It also provides general properties for hardware, configuration parameters,
    result, and calibration file path. This class is designed to be extended
    for specific measurement types like OCV, ACIR, or EIS.

    Attributes:
        hardware (Hardware): The hardware configuration used for the measurement.
        config_parameters (ConfigParameters): Configuration parameters
            for the measurement, provided by the user. There can be other,
            measurement type specific parameters in the child classes.
    """

    device: Device
    test_parameters: TestParameters
    result: Union[
        float,
        SMUResult,
        list[SMUResult],
        list[tuple[SMUCellData, SMUResult]],
        list[tuple[SMUCellData, list[SMUResult]]],
        list[tuple[str, tuple[datetime, datetime, float]]],
    ]

    DEVICE_FAMILY: DeviceFamily = None  # To be defined in subclasses

    def __init__(self, device: Device, test_parameters: TestParameters):
        """Initialize the Measurement with the specified device and calibration file.

        Sets up the measurement base class with the provided device and calibration
        file path. If no calibration file path is provided, uses the default path
        based on the device serial number. Initializes test parameters and result
        storage for the measurement process.

        Args:
            device (Device): The device instance to use for measurements.
                Must be a valid Device object with an active session.

        Raises:
            ValueError: If device is None or invalid
            RuntimeError: If device initialization fails
            FileNotFoundError: If specified calibration file path doesn't exist

        Examples:
            >>> device = Device(DeviceFamily.DMM, "PXI1Slot2")
            >>> measurement = Measurement(device)
            >>> measurement = Measurement(device, "/path/to/calibration.csv")
        """
        self.device = device
        self._test_parameters = test_parameters
        self._result = None
        # Initialize temperature awareness mixin
        TemperatureAware.__init__(self)
        # Initialize switch awareness mixin
        SwitchAware.__init__(self)

    @property
    def test_parameters(self) -> TestParameters:
        """Get the current test parameters for the measurement.

        Returns the configuration parameters that define how the measurement
        should be performed, including settings like powerline frequency
        and other measurement-specific parameters.

        Returns:
            TestParameters: The current test parameters configuration

        Examples:
            >>> measurement = Measurement(device)
            >>> params = measurement.test_parameters
            >>> print(params.powerline_frequency)
            PowerlineFrequency.FREQ_60_HZ
        """
        return self._test_parameters

    @test_parameters.setter
    def test_parameters(self, value: TestParameters):
        """Set the test parameters for the measurement.

        Updates the configuration parameters that control how the measurement
        is performed. These parameters must be set before running a measurement
        to ensure proper device configuration.

        Args:
            value (TestParameters): The new test parameters configuration.
                Must be a valid TestParameters instance or subclass.

        Raises:
            TypeError: If value is not a TestParameters instance
            ValueError: If the provided parameters contain invalid values

        Examples:
            >>> params = TestParameters()
            >>> params.powerline_frequency = PowerlineFrequency.FREQ_50_HZ
            >>> measurement.test_parameters = params
        """
        self._test_parameters = value

    @property
    def result(
        self,
    ) -> Union[
        float,
        SMUResult,
        list[SMUResult],
        list[tuple[SMUCellData, SMUResult]],
        list[tuple[SMUCellData, list[SMUResult]]],
        list[tuple[str, tuple[datetime, datetime, float]]],
        Any,
    ]:
        """Get the result of the last measurement.

        Returns the measurement result from the most recent measurement operation.
        The result type depends on the specific measurement implementation and
        whether switching was used:

        - Single measurements:
            - float for OCV and DCIR
            - SMUResult for ACIR
            - list[SMUResult] for EIS
        - Switching measurements:
            - list[tuple[SMUCellData, SMUResult]] for ACIR with switching
            - list[tuple[SMUCellData, list[SMUResult]]], for EIS with switching
            - list[tuple[str, tuple[datetime, datetime, float]]], for OCV with switching

        Returns:
            float | SMUResult | list[SMUResult]
            | list[tuple[SMUCellData, SMUResult]]
            | list[tuple[SMUCellData, list[SMUResult]]]
            | list[tuple[str, tuple[datetime, datetime, float]]]
            | Any: The measurement result(s).
            For switching measurements, returns a list of tuples where each tuple contains
            the cell data and its corresponding results.

        Raises:
            RuntimeError: If no measurement has been performed yet or if
                the result is not available

        Examples:
            >>> measurement.run(test_parameters)
            >>> result = measurement.result
            >>> print(f"Measurement result: {result}")
            >>>
            >>> # For switching measurements
            >>> switching_results = measurement.run_with_switching(compensation)
            >>> for cell_data, cell_results in measurement.result:
            ...     print(f"Cell {cell_data.cell_serial_number}: {len(cell_results)} results")
        """
        if not self._result:
            raise RuntimeError("No measurement value available!")
        return self._result

    @abstractmethod
    def _configure(self):
        """Implement this function to configure the used hardware specifically.

        This method expects the config_parameters to already be set.
        """
        # Implement the hardware configuration in your subclass here.
        pass

    @abstractmethod
    def _measure(self):
        """Do the measurement using the instrument handler, and update values accordingly."""
        if not self.device:
            raise RuntimeError("Hardware not initialized!")
        # Implement performing measurements
        pass

    @abstractmethod
    def run(self):
        """Run the measurement process with the given test parameters used to configure the device.

        Returns:
            A single result which is calculated and populated after fetching the data.
        """
        # Example Implementation: Implement with the correct TestParameter Subclass
        # Implement this to change the return logic or produce additional measurement values!
        with self.device.session.lock():
            self._configure()
            self._measure()
        return self.result

    @abstractmethod
    def run_with_switching(self):
        """Run measurement with automatic switching between DUT channels.

        This method must be implemented by each measurement subclass to provide
        switching functionality. It should use the SwitchAware mixin capabilities
        to iterate through configured channels and perform measurements.

        Returns:
            List of measurement results for each DUT channel

        Raises:
            RuntimeError: If switching not enabled or no channels configured
        """
        pass
