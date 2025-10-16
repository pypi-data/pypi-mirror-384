"""Create EIS (Electrochemical Impedance Spectroscopy) measurement class."""

import cmath
import json
import math
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any, NamedTuple, List, Union

from nibcq._acir import ACIR, FrequencySet, SMUInputParameters, SMUOutputFunction
from nibcq._device import Device
from nibcq.compensation import (
    Compensation,
    CompensationFile,
    CompensationMethod,
    InterpolationMode,
)
from nibcq.enums import PowerlineFrequency
from nibcq.measurement import ConfigFileSupport, SMUMeasurement, SMUResult, TestParameters
from nibcq.switch import SMUCellData


class PlotSeries(NamedTuple):
    """Generic X/Y series for plotting.

    Used for Nyquist (R vs -X) and Bode (frequency vs value) outputs.
    Access `.x` and `.y` to get the values, or just plot it as it is.

    Attributes:
        x (List[float]): The x-coordinates of the data points.
        y (List[float]): The y-coordinates of the data points.

    Example:
        >>> series = PlotSeries(x=[1, 2, 3], y=[4, 5, 6])
        >>> series.x
        [1, 2, 3]
        >>> series.y
        [4, 5, 6]
    """

    x: List[float]
    y: List[float]


@dataclass
class EISTestParameters(TestParameters, ConfigFileSupport):
    """Configuration parameters for Electrochemical Impedance Spectroscopy (EIS) measurements.

    This class extends the base TestParameters to provide EIS-specific configuration
    options. EIS measurements involve frequency sweeps across multiple frequency points,
    requiring comprehensive parameter specification for voltage limits, signal
    characteristics, and error compensation methods.

    EIS measurements are typically more complex than single-frequency ACIR measurements
    as they characterize the frequency-dependent behavior of electrochemical systems.
    Proper parameter configuration ensures accurate impedance characterization across
    the entire frequency spectrum of interest.

    Attributes:
        voltage_limit_hi: Upper voltage limit in Volts for DUT protection during the
                         entire frequency sweep. Default 5.0V provides safety for
                         most electrochemical cells.
        nominal_voltage: Expected DUT voltage level in Volts, used for measurement
                        range optimization. Default 4.0V is typical for battery cells.
        compensation_method: Error correction method applied to all frequency points.
                           Options include NO_COMPENSATION, SHORT, GOLDEN_DUT, or
                           SHORT_GOLDEN_DUT for systematic error correction.
        frequency_sweep_characteristics: Dictionary mapping each frequency (Hz) to its
                                       corresponding FrequencySet containing current
                                       amplitude and number of periods. This defines
                                       the complete EIS measurement protocol.

    Example:
        >>> sweep_config = {
        ...     1000.0: FrequencySet(current_amplitude=0.1, number_of_periods=20),
        ...     100.0: FrequencySet(current_amplitude=0.1, number_of_periods=50)
        ... }
        >>> params = EISTestParameters(
        ...     voltage_limit_hi=6.0,
        ...     nominal_voltage=3.7,
        ...     compensation_method=CompensationMethod.SHORT,
        ...     frequency_sweep_characteristics=sweep_config
        ... )
    """

    voltage_limit_hi: float = 5.0
    nominal_voltage: float = 4.0
    compensation_method: CompensationMethod = CompensationMethod.NO_COMPENSATION
    frequency_sweep_characteristics: dict[float, FrequencySet] = None

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "EISTestParameters":
        """Create EISTestParameters instance from JSON dictionary.

        Args:
            json_data: Dictionary containing EIS configuration data

        Returns:
            EISTestParameters: Instance configured from JSON data

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

        # Parse frequency sweep characteristics
        frequency_sweep = {}
        for freq_data in json_data.get("Frequency Sweep Characteristics", []):
            frequency = freq_data.get("Frequency (Hz)")
            current_amplitude = freq_data.get("Current Amplitude (A)")
            number_of_periods = freq_data.get("Number of Periods")

            if frequency is None or current_amplitude is None or number_of_periods is None:
                raise ValueError("Frequency sweep characteristic missing required fields")

            frequency_sweep[frequency] = FrequencySet(
                current_amplitude=current_amplitude, number_of_periods=number_of_periods
            )

        return cls(
            voltage_limit_hi=json_data.get("Voltage Limit Hi (V)", 5.0),
            nominal_voltage=json_data.get("Nominal DUT Voltage (V)", 4.0),
            compensation_method=comp_method,
            frequency_sweep_characteristics=frequency_sweep,
            powerline_frequency=powerline_freq,
        )

    @classmethod
    def from_file(cls, file_path: str) -> "EISTestParameters":
        """Create EISTestParameters instance from JSON configuration file.

        Args:
            file_path: Path to JSON configuration file

        Returns:
            EISTestParameters: Instance configured from file

        Raises:
            FileNotFoundError: If configuration file is not found
            ValueError: If file content is invalid or required parameters are missing
            json.JSONDecodeError: If file contains invalid JSON
        """
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        return cls.from_json(json_data)


class EIS(ACIR):
    """Electrochemical Impedance Spectroscopy (EIS) measurement handler class.

    This class extends the ACIR class to provide multi-frequency impedance spectroscopy
    capabilities. EIS measurements characterize the frequency-dependent impedance behavior
    of electrochemical systems by sweeping across a range of frequencies and measuring
    the complex impedance at each point.

    EIS is a powerful technique for analyzing electrochemical processes, battery
    characterization, corrosion studies, and material property investigations. The
    class manages frequency sweeps, data collection across multiple frequencies,
    and provides methods for generating common EIS visualization formats like
    Nyquist and Bode plots.

    The class inherits all ACIR functionality for single-frequency measurements and
    extends it with frequency sweep management, multi-point data storage, and
    EIS-specific analysis capabilities.

    Example:
        >>> device = Device("PXIe-4139")
        >>> eis = EIS(device)
        >>>
        >>> # Configure frequency sweep
        >>> sweep_config = {
        ...     1000.0: FrequencySet(current_amplitude=0.1, number_of_periods=20),
        ...     100.0: FrequencySet(current_amplitude=0.1, number_of_periods=50)
        ... }
        >>> params = EISTestParameters(frequency_sweep_characteristics=sweep_config)
        >>>
        >>> # Run EIS measurement
        >>> results = eis.run(params, compensation)
        >>> print(f"Measured {len(results)} frequency points")
    """

    def __init__(self, device: Device, test_parameters: EISTestParameters):
        """Initialize the EIS measurement with the instrument device.

        Sets up the EIS measurement session with the specified device. Initializes internal
        parameters, frequency list, and result storage. Inherits ACIR functionality and
        extends it for multi-frequency electrochemical impedance spectroscopy measurements.

        Args:
            device (Device): The device instance to use for EIS measurements.
                Must be a valid SMU device capable of AC measurements.
            test_parameters (EISTestParameters): The test parameters for the measurement.

        Raises:
            ValueError: If device is None or invalid
            RuntimeError: If device initialization fails
            FileNotFoundError: If calibration_file_path is specified but file doesn't exist

        Examples:
            >>> device = Device.connect(DeviceFamily.SMU, "PXIe-4139")
            >>> params = EISTestParameters()
            >>> eis = EIS(device, params)
        """
        super().__init__(device=device, test_parameters=test_parameters)
        # Specific fields reinitialization
        self._calculated_generation_parameters.configured_frequency = None
        self.test_parameters = test_parameters
        self._current_frequency = None
        self._result = list()

    # Overwrite test_parameters as the class specific subtype of ConfigParameters.
    @property
    def test_parameters(self) -> EISTestParameters:
        """Get the current EIS test parameters.

        Returns the EISTestParameters object containing all configuration settings
        for the EIS measurement including voltage limits, nominal voltage, compensation
        method, and frequency sweep characteristics.

        Returns:
            EISTestParameters: The current test parameters configuration

        Examples:
            >>> eis = EIS(device)
            >>> params = eis.test_parameters
            >>> print(params.voltage_limit_hi)
            5.0
        """
        return self._test_parameters

    @test_parameters.setter
    def test_parameters(self, value: EISTestParameters):
        """Set the EIS test parameters and configure internal parameters.

        Updates the test parameters and automatically configures all internal
        generation input parameters based on the provided EIS configuration.
        This method must be called before running measurements to ensure proper
        device setup.

        Args:
            value (EISTestParameters): The new EIS test parameters containing
                voltage limits, nominal voltage, compensation method, frequency
                sweep characteristics, and other measurement settings.

        Raises:
            ValueError: If value is None or contains invalid parameter values
            TypeError: If value is not an EISTestParameters instance
            AttributeError: If required frequency sweep characteristics are missing

        Examples:
            >>> params = EISTestParameters()
            >>> params.voltage_limit_hi = 6.0
            >>> params.frequency_sweep_characteristics = {1000: FrequencySet(1.0, 20)}
            >>> eis.test_parameters = params
        """
        self._test_parameters = value

        # Also set the other, private parameters, so config can have only the device-configuration.
        # --- SET GENERATION INPUT PARAMETERS ---
        # Part of "Obtain Test Parameters" on LabVIEW API
        self._generation_input_parameters = SMUInputParameters(
            voltage_limit_hi=value.voltage_limit_hi,
            # Changed from LabVIEW Code.
            # There it not gets set, and the upper limit's negated gets used automatically.
            voltage_limit_low=-1.0 * value.voltage_limit_hi,
            current_limit=3.0,  # Maximum supported current measurement, not used in LabVIEW API.
            dc_offset=0,  # No offset is set in LabVIEW API.
            nominal_dut_voltage=value.nominal_voltage,
            output_function=SMUOutputFunction.DC_CURRENT,  # Fix Value
            # Change: Just copy from the value instead of generating one.
            frequency_sweep_characteristics=value.frequency_sweep_characteristics,
            compensation_method=value.compensation_method,
            powerline_frequency=value.powerline_frequency,
        )

    @property
    def current_frequency(self) -> float:
        """Get the current measurement frequency.

        Returns the frequency currently being used for measurements. This value
        changes during frequency sweeps as the EIS measurement progresses through
        different frequencies.

        Returns:
            float: The current frequency in Hz, or None if not set

        Examples:
            >>> eis.current_frequency = 1000.0
            >>> print(eis.current_frequency)
            1000.0
        """
        return self._current_frequency

    @current_frequency.setter
    def current_frequency(self, value: float):
        """Set the current measurement frequency with validation.

        Sets the frequency for the current measurement cycle. The frequency must
        be within the supported range (0 to FREQUENCY_LIMIT) and must be present
        in the frequency sweep characteristics.

        Args:
            value (float): The frequency to set in Hz. Must be between 0 and
                FREQUENCY_LIMIT and present in frequency_sweep_characteristics.

        Raises:
            ValueError: If frequency is out of bounds (0 to FREQUENCY_LIMIT) or
                not present in the frequency sweep characteristics
            TypeError: If value is not a number

        Examples:
            >>> eis.current_frequency = 1000.0  # Valid if in sweep characteristics
            >>> eis.current_frequency = 5000.0  # Raises ValueError if > FREQUENCY_LIMIT
        """
        if 0.0 <= value <= ACIR.FREQUENCY_LIMIT:
            if value in self._generation_input_parameters.frequency_sweep_characteristics:
                self._current_frequency = value
        else:
            raise ValueError(f"{value} Hz frequency is out of bounds.")

    @property
    def frequency_list(self):
        """Get the frequency sweep frequencies as a descending sorted list.

        Returns all frequencies defined in the frequency sweep characteristics,
        sorted in descending order (highest to lowest frequency). This order
        is typically used in EIS measurements to start with high frequencies
        and sweep down to low frequencies.

        Returns:
            list[float]: A list of frequencies in Hz, sorted in descending order

        Raises:
            ValueError: If frequency sweep characteristics are not set or empty

        Examples:
            >>> eis.frequency_list
            [1000.0, 500.0, 100.0, 50.0, 10.0]
        """
        chars = self._generation_input_parameters.frequency_sweep_characteristics
        if not chars:
            raise ValueError("Frequency sweep characteristics are not set.")
        return sorted(chars.keys(), reverse=True)

    @property
    def result(
        self,
    ) -> Union[list[SMUResult], list[tuple[SMUCellData, list[SMUResult]]]]:
        """Get the result of the last EIS measurement.

        Returns the measurement result from the most recent measurement operation.
        The result type depends on whether switching was used or not.

        Returns:
            list[SMUResult] | list[tuple[SMUCellData, list[SMUResult]]]: The measurement result(s).
                For switching measurements, returns a list of tuples where each tuple contains
                the cell data and its corresponding results.

        Raises:
            RuntimeError: If no measurement has been performed yet or if
                the result is not available
        """
        if not self._result:
            raise RuntimeError("No measurement value available!")
        return self._result

    def get_plots(
        self,
    ) -> (
        tuple[PlotSeries, PlotSeries, PlotSeries] | list[tuple[PlotSeries, PlotSeries, PlotSeries]]
    ):
        """Return plotting datasets for Nyquist and Bode plots.

        For single device measurements, returns a 3-tuple:
          - (nyquist_x, nyquist_y): Nyquist (Cole) data where nyquist_x is R and
            nyquist_y is -X (both lists of floats) sorted by ascending frequency.
          - (freqs, magnitudes): Bode magnitude data (frequency ascending, abs(Z)).
          - (freqs, phases): Bode phase data (frequency ascending, theta in degrees).

        For switching measurements, returns a list of 3-tuples, one for each cell.

        The method reads measurement results and sorts the returned points by frequency
        (ascending) to make plotting predictable for common plotting conventions.

        Raises:
            RuntimeError: If no measurement results are available.
        """
        if self.has_switch_capability and self._result:
            # Check if _result contains switching data (list of tuples)
            if (
                isinstance(self._result, list)
                and len(self._result) > 0
                and isinstance(self._result[0], tuple)
                and len(self._result[0]) == 2
            ):
                # Switching mode: _result is list[tuple[SMUCellData, list[SMUResult]]]
                plot_data_per_cell = []

                for cell_data, results in self._result:
                    # Extract arrays for this cell
                    freqs = [r.measured_frequency for r in results]
                    r_vals = [r.r for r in results]
                    x_vals = [r.x for r in results]
                    z_vals = [r.z for r in results]
                    theta_vals = [r.theta for r in results]

                    # sort by frequency ascending
                    order = sorted(range(len(freqs)), key=lambda i: freqs[i])
                    freqs_sorted = [freqs[i] for i in order]
                    r_sorted = [r_vals[i] for i in order]
                    x_sorted = [x_vals[i] for i in order]
                    z_sorted = [z_vals[i] for i in order]
                    theta_sorted = [theta_vals[i] for i in order]

                    # Nyquist uses R and -X
                    nyquist_x = r_sorted
                    nyquist_y = [-x for x in x_sorted]

                    plot_data_per_cell.append(
                        (
                            PlotSeries(nyquist_x, nyquist_y),
                            PlotSeries(freqs_sorted, z_sorted),
                            PlotSeries(freqs_sorted, theta_sorted),
                        )
                    )

                return plot_data_per_cell

        # Single device mode or non-switching data
        # Use the public result property which will raise if empty
        results = list(self.result)

        # Extract arrays
        freqs = [r.measured_frequency for r in results]
        r_vals = [r.r for r in results]
        x_vals = [r.x for r in results]
        z_vals = [r.z for r in results]
        theta_vals = [r.theta for r in results]

        # sort by frequency ascending
        order = sorted(range(len(freqs)), key=lambda i: freqs[i])
        freqs_sorted = [freqs[i] for i in order]
        r_sorted = [r_vals[i] for i in order]
        x_sorted = [x_vals[i] for i in order]
        z_sorted = [z_vals[i] for i in order]
        theta_sorted = [theta_vals[i] for i in order]

        # Nyquist uses R and -X
        nyquist_x = r_sorted
        nyquist_y = [-x for x in x_sorted]

        return (
            PlotSeries(nyquist_x, nyquist_y),
            PlotSeries(freqs_sorted, z_sorted),
            PlotSeries(freqs_sorted, theta_sorted),
        )

    def run(
        self,
        compensation: Compensation,
        measurement_callback: Optional[Callable[[SMUMeasurement], None]] = None,
    ) -> list[SMUResult]:
        """Run the EIS process with the passed configuration parameters.

        Validates temperature if the compensation specifies a target temperature, and
        the device supports temperature measurement. Then performs a full frequency sweep
        as defined in the test parameters, measuring impedance at each frequency point.

        Args:
            compensation:
                The compensation object to use for impedance correction
            measurement_callback:
                Optional callback function to call after each measurement cycle.
                One measurement cycle is a waveform generation and
                measurement done on a specific frequency.

                Pass your callback function here what you use to document the raw measurement data.
                It should have one input parameter, which is a SMUMeasurement object.

        Returns:
            A list of SMUResults, containing all of the results from the done measurements.

        Raises:
            ValueError: If configuration parameters are invalid or would cause measurement errors.
                Also raised if temperature validation fails.
            RuntimeError: If device configuration or measurement fails.
            AttributeError: If frequency sweep characteristics are missing or improperly formatted.

        Examples:
            >>> params = EISTestParameters()
            >>> eis = EIS(device, params)
            >>> compensation = eis.load_compensation_file()
            >>> results = eis.run(compensation)
        """
        # Validate temperature if necessary
        if compensation.target_temperature is not None and (
            not math.isnan(compensation.target_temperature.center)
        ):
            # Measure and Validate temperature
            self.validate_temperature(compensation.target_temperature)

        with self.device.session.lock():
            # Initialize results list
            eis_results: list[SMUResult] = []
            # Do measurement.
            for frequency in self.frequency_list:
                self.current_frequency = frequency
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

                eis_results.append(single_result)
                if measurement_callback:
                    measurement_callback(self.raw_data)
                # Using reset instead of disable, as disable would stop the device from working.
                self.device.session.reset()
            # Set results
            self._result = eis_results

        return self.result

    def run_with_switching(
        self,
        compensation: Compensation | list[Compensation],
        measurement_callback: Optional[Callable[[SMUMeasurement], None]] = None,
    ):
        """Run complete EIS frequency sweeps across multiple DUTs using switch matrix configuration.

        This method performs comprehensive Electrochemical Impedance Spectroscopy measurements
        on multiple devices under test (DUTs) by automatically switching between different
        channels. For each connected DUT, it executes a complete frequency sweep as defined
        in the test parameters, collecting impedance data across the entire frequency range.

        The switching process ensures proper isolation between measurements, with automatic
        debounce timing for stable connections and complete disconnection between DUTs.
        This enables efficient multi-battery characterization, comparative electrochemical
        analysis, or production testing scenarios where multiple samples need identical
        frequency sweep measurements.

        Each DUT receives the same complete EIS treatment: frequency sweep from high to low
        frequencies, compensation application, and result collection. The method maintains
        measurement consistency across all DUTs while leveraging hardware switching for
        efficiency.

        Args:
            compensation (Compensation | list[Compensation]): The compensation object containing
                frequency-dependent error correction data for impedance accuracy improvement across
                all measurement frequencies in the sweep.
                This can be passed as a list of compensations, a different one for each cell.
            measurement_callback (Optional[Callable[[SMUMeasurement], None]]): Optional callback
                function invoked after each individual frequency measurement within each DUT's
                sweep. Receives the raw SMUMeasurement data for real-time monitoring, logging,
                or progress tracking. Called once per frequency per DUT.

        Returns:
            list[tuple[SMUCellData, list[SMUResult]]]: A list of tuples mapping each cell to its
                complete EIS measurement results. Each SMUCellData represents a DUT connection
                point, and the corresponding list[SMUResult] contains impedance measurements
                for all frequencies in the sweep, enabling complete frequency-domain analysis
                for each individual DUT.

        Raises:
            RuntimeError: If switching capability is not enabled (call device.with_switching()
                first) or if no switch channels are configured in the switch matrix.
            ValueError: If configuration parameters are invalid, would cause measurement errors
                across the frequency range, or if compensation list length doesn't match the
                number of DUTs. Also raised if temperature validation fails for any cell.
            AttributeError: If frequency sweep characteristics are missing or improperly
                formatted in the test parameters.
            Exception: If connection to any DUT fails during switching operations or if
                any frequency measurement fails during the sweep.

        Examples:
            >>> params = EISTestParameters()
            >>> eis = EIS(device, params)
            >>> compensation = eis.load_compensation_file()
            >>> results = eis.run_with_switching(compensation)

        Note:
            This method performs a complete frequency sweep for each DUT, which can be
            time-intensive for large frequency ranges or many DUTs. The measurement callback
            can be used to monitor progress and provide feedback during long measurement
            sequences. Switch timing includes automatic debounce delays for measurement
            stability, and proper disconnection is guaranteed even if exceptions occur.
        """
        if not self.has_switch_capability:
            raise RuntimeError("Switching not enabled. Call device.with_switching() first.")

        if not self.switch_cells:
            raise RuntimeError("No switch channels configured")

        # Compensation list size validation
        if isinstance(compensation, list):
            if len(compensation) != len(self.switch_cells):
                raise ValueError("Compensation list must match the number of DUTs.")

        results: list[tuple[SMUCellData, list[SMUResult]]] = []

        try:
            for i, cell in enumerate(self.switch_cells):
                self.connect_channel(cell)
                self.wait_for_debounce()

                result_list = self.run(
                    compensation=(
                        compensation[i] if isinstance(compensation, list) else compensation
                    ),
                    measurement_callback=measurement_callback,
                )
                results.append((cell, result_list))
                self.disconnect_all()
        finally:
            self.disconnect_all()
            self._result = results  # Make even partial results available.
        return results

    def write_compensation_file(
        self,
        compensation_file_path: Optional[str] = None,
        kit_file_path: Optional[str] = None,
        comment: Optional[str] = None,
        measurement_callback: Optional[Callable[[SMUMeasurement], None]] = None,
    ) -> str:
        """Create a compensation file based on measurements at all frequencies in the sweep.

        Args:
            compensation_file_path (Optional[str]): Optional specific file path to write to.
                If None, generates path automatically.
            kit_file_path (Optional[str]): Optional specific file path to the
                known impedance table. If None, no known impedance table is used.
            comment (Optional[str]): Optional comment to include in the compensation file.
                If None, no comment is included.

        Returns:
            str: The path of the created compensation file.

        Raises:
            ValueError: If parameters are invalid or compensation method does not support
                compensation files.
            FileNotFoundError: If compensation file is required but not found.
            RuntimeError: If device configuration or measurement fails.
            NotImplementedError: If unsupported compensation method is specified.
        """
        # Runs a pseudo measurement and saves the result to a file
        # Determine what path to save, if it was not provided.
        # Try to create the basic path, to check if the file type is supported.
        base_compensation_file_path = self.generate_compensation_file_path()
        # If no specific path is provided, use the base path.
        if compensation_file_path is None:
            compensation_file_path = base_compensation_file_path

        # Validate compensation method support
        if self.test_parameters.compensation_method == CompensationMethod.NO_COMPENSATION:
            raise ValueError(
                f"You must select a compensation method other than "
                f"{CompensationMethod.NO_COMPENSATION.value} to create a compensation file."
            )

        # Get temperature
        self.measure_temperature()

        # Collect compensation data for all frequencies
        compensation_parameters = {}

        with self.device.session.lock():
            for frequency in self.frequency_list:
                self.current_frequency = frequency
                self._configure()
                compensation_parameters[frequency] = self._measure().impedance
                if measurement_callback:
                    measurement_callback(self.raw_data)
                self.device.session.reset()

        # Populate Compensation Data with all frequencies
        compensation = Compensation(
            compensation_method=self.test_parameters.compensation_method,
            compensation_file_path=compensation_file_path,
            target_temperature=self.temperature_range,
            compensation_parameters=compensation_parameters,
        )

        # Apply KIT if necessary.
        if self.test_parameters.compensation_method == CompensationMethod.SHORT and kit_file_path:
            self._apply_kit_compensation(compensation, kit_file_path, InterpolationMode.NEAREST)

        # Create Compensation file.
        new_file = CompensationFile.memory_to_file(compensation=compensation, comment=comment)
        new_file.save_to_file(compensation_file_path)

        return compensation_file_path
